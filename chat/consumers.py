import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import ChatRoom, ChatMessage
from .services import can_send_message
from .constants import PREDEFINED_CHAT


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Matrimony Chat WebSocket Consumer

    Supports:
    - Predefined Q&A (non-subscribers)
    - Suggested answers for predefined questions
    - Custom text chat (subscribers only)
    """

    async def connect(self):
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        if not self.user.is_authenticated:
            await self.close()
            return

        self.chat_room = await self.get_chat_room()
        if not self.chat_room:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        message_type = data.get("message_type")  # predefined / custom
        message_text = data.get("message_text")
        question_id = data.get("question_id")
        answer_index = data.get("answer_index")

        sender = self.user
        receiver = await self.get_receiver(sender)

        # 🔐 Subscription / permission check
        allowed, error_message = await sync_to_async(can_send_message)(
            sender, receiver, message_type
        )

        if not allowed:
            await self.send(json.dumps({
                "type": "error",
                "message": error_message
            }))
            return

        suggested_answers = None

        # ==========================
        # PREDEFINED MESSAGE
        # ==========================
        if message_type == "predefined":

            if question_id not in PREDEFINED_CHAT:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "Invalid predefined question"
                }))
                return

            # 📩 QUESTION
            if answer_index is None:
                message_text = PREDEFINED_CHAT[question_id]["question"]

                suggested_answers = [
                    {"index": idx, "text": text}
                    for idx, text in enumerate(
                        PREDEFINED_CHAT[question_id]["answers"]
                    )
                ]

            # 📤 ANSWER
            else:
                answers = PREDEFINED_CHAT[question_id]["answers"]

                if (
                    not isinstance(answer_index, int)
                    or answer_index < 0
                    or answer_index >= len(answers)
                ):
                    await self.send(json.dumps({
                        "type": "error",
                        "message": "Invalid answer index"
                    }))
                    return

                message_text = answers[answer_index]

        # ==========================
        # CUSTOM MESSAGE
        # ==========================
        elif message_type == "custom":

            if not message_text or not message_text.strip():
                await self.send(json.dumps({
                    "type": "error",
                    "message": "Message text cannot be empty"
                }))
                return

            message_text = message_text.strip()

        else:
            await self.send(json.dumps({
                "type": "error",
                "message": "Invalid message type"
            }))
            return

        # ==========================
        # SAVE MESSAGE
        # ==========================
        message = await self.create_message(
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            message_text=message_text,
            question_id=question_id,
            answer_index=answer_index
        )

        # ==========================
        # BROADCAST MESSAGE
        # ==========================
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": message.id,
                    "sender": sender.id,
                    "receiver": receiver.id,
                    "text": message.message_text,
                    "message_type": message.message_type,
                    "question_id": question_id,
                    "answer_index": answer_index,
                    "created_at": message.created_at.isoformat()
                }
            }
        )

        # ==========================
        # SEND SUGGESTED ANSWERS
        # ==========================
        if suggested_answers:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "suggested_answers",
                    "receiver_id": receiver.id,
                    "question_id": question_id,
                    "answers": suggested_answers
                }
            )

    # ==========================
    # GROUP EVENT HANDLERS
    # ==========================

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            **event["message"]
        }))

    async def suggested_answers(self, event):
        if self.user.id != event["receiver_id"]:
            return

        await self.send(text_data=json.dumps({
            "type": "suggested_answers",
            "question_id": event["question_id"],
            "answers": event["answers"]
        }))

    # ==========================
    # DATABASE HELPERS
    # ==========================

    @sync_to_async
    def get_chat_room(self):
        try:
            return ChatRoom.objects.get(id=self.room_id)
        except ChatRoom.DoesNotExist:
            return None

    @sync_to_async
    def get_receiver(self, sender):
        return (
            self.chat_room.user2
            if self.chat_room.user1 == sender
            else self.chat_room.user1
        )

    @sync_to_async
    def create_message(
        self,
        sender,
        receiver,
        message_type,
        message_text,
        question_id,
        answer_index
    ):
        return ChatMessage.objects.create(
            chat_room=self.chat_room,
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            message_text=message_text,
            predefined_question_id=question_id,
            predefined_answer_index=answer_index
        )
