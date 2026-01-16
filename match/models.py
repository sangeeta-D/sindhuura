from django.db import models
from auth_api.models import CustomUser
# Create your models here.


class MatchRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    from_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_match_requests'
    )

    to_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='received_match_requests'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user.email} → {self.to_user.email} ({self.status})"


class SuccessStory(models.Model):
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="success_stories"
    )

    groom_name = models.CharField(max_length=255)
    bride_name = models.CharField(max_length=255)

    wedding_date = models.DateField()
    venue = models.CharField(max_length=255)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def couple_name(self):
        return f"{self.bride_name} & {self.groom_name}"

    def __str__(self):
        return self.couple_name()


class SuccessStoryImage(models.Model):
    success_story = models.ForeignKey(
        SuccessStory,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="success_stories/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image - {self.success_story.couple_name()}"
    
class StoryBanner(models.Model):
    image = models.ImageField(
        upload_to='story_banners/',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Banner {self.id}"