from django.db import models

# from auth_api.models import CustomUser
# Create your models here.
class Caste(models.Model):
    LEVEL_CHOICES = (
        ('religion', 'Religion'),
        ('caste', 'Caste'),
    )

    name = models.CharField(max_length=100)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='castes'
    )

    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Religion / Caste"
        verbose_name_plural = "Religions & Castes"
        unique_together = ('name', 'parent')

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name


class MusicGenre(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class MusicActivity(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class ReadingPreference(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class MovieGenre(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    

class SubscriptionPlan(models.Model):

    plan_name = models.CharField(
        max_length=100,
        unique=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price in INR"
    )

    validity = models.PositiveIntegerField(
        help_text="Validity in days"
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["price"]
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return f"{self.plan_name} - ₹{self.price}"


class SidebarMenu(models.Model):

    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    icon_class = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class SubAdminMenuPermission(models.Model):

    sub_admin = models.ForeignKey(
        "auth_api.CustomUser",
        on_delete=models.CASCADE,
        limit_choices_to={"role": "sub_admin"},
        related_name="menu_permissions"
    )

    menu = models.ForeignKey(
        SidebarMenu,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("sub_admin", "menu")

    def __str__(self):
        return f"{self.sub_admin.email} → {self.menu.name}"



class Blog(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("published", "Published"),
    )

    title = models.CharField(
        max_length=255
    )

    short_description = models.TextField(
        help_text="Short summary shown in blog listing"
    )

    content = models.TextField(
        help_text="Full blog content (HTML or plain text)"
    )

    cover_media = models.FileField(
        upload_to="blogs/",
        null=True,
        blank=True,
        help_text="Upload cover image (JPG, PNG) or video (MP4, WebM)"
    )

    cover_media_type = models.CharField(
        max_length=10,
        choices=[("image", "Image"), ("video", "Video")],
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    is_featured = models.BooleanField(
        default=False
    )

    views_count = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Event(models.Model):
    event_name = models.CharField(max_length=255)
    event_datetime = models.DateTimeField()
    venue = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="event_images/")  # Store images in media/event_images/
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.event_name