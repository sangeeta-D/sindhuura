from django.db import models
from auth_api.models import CustomUser
from match.models import MatchRequest
from django.core.exceptions import ValidationError
# Create your models here.


class ChatRoom(models.Model):
    user1 = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="chatrooms_as_user1"
    )
    user2 = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="chatrooms_as_user2"
    )

    match_request = models.OneToOneField(
        MatchRequest,
        on_delete=models.CASCADE,
        related_name="chat_room"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user1", "user2")

    def __str__(self):
        return f"ChatRoom {self.user1.email} & {self.user2.email}"



class ChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ("predefined", "Predefined"),
        ("custom", "Custom"),
        ("system", "System"),
    )

    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    receiver = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="received_messages"
    )

    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES
    )

    # For predefined answers or custom text
    message_text = models.TextField()

    # Only for predefined messages (store question_id & answer index)
    predefined_question_id = models.IntegerField(
        null=True,
        blank=True
    )

    predefined_answer_index = models.IntegerField(
        null=True,
        blank=True
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.email} → {self.receiver.email} ({self.message_type})"
