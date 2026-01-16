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


class PredefinedMessage(models.Model):
    text = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.text
    
class PredefinedAnswer(models.Model):
    message = models.ForeignKey(
        PredefinedMessage,
        on_delete=models.CASCADE,
        related_name="answers"
    )
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text
    

class ChatMessage(models.Model):
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE
    )

    predefined_message = models.ForeignKey(
        PredefinedMessage,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    predefined_answer = models.ForeignKey(
        PredefinedAnswer,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Either question OR answer must be selected
        if not self.predefined_message and not self.predefined_answer:
            raise ValidationError("Message or Answer is required")

    def __str__(self):
        return f"{self.sender.email} → Chat {self.chat_room.id}"
