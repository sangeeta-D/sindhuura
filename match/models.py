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


class ContactInfoView(models.Model):
    """Track contact information views for subscribed users"""
    viewer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='contact_info_views'
    )
    viewed_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='contact_info_viewed_by'
    )
    views_count = models.PositiveIntegerField(default=1)
    last_viewed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('viewer', 'viewed_user')
        ordering = ['-last_viewed_at']

    def __str__(self):
        return f"{self.viewer.email} viewed {self.viewed_user.email} ({self.views_count} times)"
    
class Notification(models.Model):

    NOTIFICATION_TYPES = (
        ("match_request", "Match Request"),
        ("match_accepted", "Match Accepted"),
        ("match_rejected", "Match Rejected"),
        ("general", "General"),
    )

    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications"
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    # Optional: Link to match request
    match_request = models.ForeignKey(
        MatchRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.email} - {self.notification_type}"