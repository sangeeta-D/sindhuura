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
    sender_id = serializers.IntegerField(source="sender.id", read_only=True)
    receiver_id = serializers.IntegerField(source="receiver.id", read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "sender_id",
            "receiver_id",
            "message_type",
            "message_text",
            "predefined_question_id",
            "predefined_answer_index",
            "is_read",
            "created_at",
        ]