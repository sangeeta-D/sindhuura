from rest_framework import serializers
from chat.models import ChatRoom, ChatMessage


class ChatUserListSerializer(serializers.Serializer):
    chat_room_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    unique_id = serializers.CharField()
    name = serializers.CharField()
    profile_image = serializers.ImageField(allow_null=True)
    is_subscribed = serializers.BooleanField()

    last_message = serializers.CharField(allow_null=True)
    last_message_time = serializers.DateTimeField(allow_null=True)



class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "sender",
            "message_type",
            "message_text",
            "predefined_question_id",
            "predefined_answer_index",
            "is_read",
            "created_at",
        ]

    def get_sender(self, obj):
        current_user = self.context.get("current_user")

        # ✅ Message sent by logged-in user
        if obj.sender == current_user:
            return "you"

        # ✅ Message sent by the other user
        return {
            "id": obj.sender.id,
            "name": obj.sender.name,
        }
