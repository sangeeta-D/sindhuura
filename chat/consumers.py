import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import ChatRoom, ChatMessage
from .services import can_send_message
from .constants import PREDEFINED_CHAT
from .firebase import send_push_notification

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]

        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.chat_room = await self.get_chat_room()
        if not self.chat_room:
            await self.close(code=4004)
            return

        self.room_group_name = f"chat_{self.room_id}"

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

        # =====================================================
        # 🔥 DELETE MESSAGE (FOR EVERYONE – HARD DELETE)
        # =====================================================
        action = data.get("action")
        if action == "delete_message":
            message_id = data.get("message_id")

            if not message_id:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "message_id is required"
                }))
                return

            deleted = await self.delete_message(
                message_id=message_id,
                user=self.user
            )

            if not deleted:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "You are not allowed to delete this message"
                }))
                return

            # 🔥 Notify both users
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "message_deleted",
                    "message_id": message_id
                }
            )
            return

        # =====================================================
        # 🔹 SEND MESSAGE (EXISTING LOGIC)
        # =====================================================
        message_type = data.get("message_type")
        message_text = data.get("message_text")
        question_id = data.get("question_id")
        answer_index = data.get("answer_index")

        sender = self.user
        receiver = await self.get_receiver(sender)

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

        # ---------- PREDEFINED ----------
        if message_type == "predefined":

            if question_id not in PREDEFINED_CHAT:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "Invalid predefined question"
                }))
                return

            if answer_index is None:
                message_text = PREDEFINED_CHAT[question_id]["question"]
                suggested_answers = [
                    {"index": idx, "text": text}
                    for idx, text in enumerate(
                        PREDEFINED_CHAT[question_id]["answers"]
                    )
                ]
            else:
                answers = PREDEFINED_CHAT[question_id]["answers"]
                if answer_index < 0 or answer_index >= len(answers):
                    await self.send(json.dumps({
                        "type": "error",
                        "message": "Invalid answer index"
                    }))
                    return
                message_text = answers[answer_index]

        # ---------- CUSTOM ----------
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

        message = await self.create_message(
            sender,
            receiver,
            message_type,
            message_text,
            question_id,
            answer_index
        )

        await self.send_firebase_notification(
            sender=sender,
            receiver=receiver,
            message_text=message.message_text,
            room_id=self.room_id
        )

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
                    "created_at": message.created_at.isoformat()
                }
            }
        )

        if suggested_answers:
            await self.send(json.dumps({
                "type": "suggested_answers",
                "question_id": question_id,
                "answers": suggested_answers
            }))

    # =====================================================
    # 🔹 GROUP EVENTS
    # =====================================================
    async def chat_message(self, event):
        await self.send(json.dumps({
            "type": "message",
            **event["message"]
        }))

    async def message_deleted(self, event):
        await self.send(json.dumps({
            "type": "message_deleted",
            "message_id": event["message_id"]
        }))

    # =====================================================
    # 🔹 DATABASE HELPERS
    # =====================================================
    @sync_to_async
    def get_chat_room(self):
        try:
            return ChatRoom.objects.select_related(
                "user1", "user2"
            ).get(id=self.room_id)
        except ChatRoom.DoesNotExist:
            return None

    @sync_to_async
    def get_receiver(self, sender):
        if self.chat_room.user1_id == sender.id:
            return self.chat_room.user2
        return self.chat_room.user1

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

    @sync_to_async
    def delete_message(self, message_id, user):
        try:
            message = ChatMessage.objects.get(
                id=message_id,
                chat_room=self.chat_room,
                sender=user  # 🔐 only sender can delete
            )
            message.delete()
            return True
        except ChatMessage.DoesNotExist:
            return False
        
    @sync_to_async
    def send_firebase_notification(self, sender, receiver, message_text, room_id):
        # If receiver has no FCM token, skip
        if not getattr(receiver, "fcm_token", None):
            return

        send_push_notification(
            token=receiver.fcm_token,
            title=f"New message from {sender.name or 'Someone'}",
            body=message_text[:100],  # limit length
            data={
                "type": "chat",
                "room_id": str(room_id),
                "sender_id": str(sender.id),
            }
        )

