from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from backend.models import Caste, MusicGenre, MusicActivity, ReadingPreference, MovieGenre
from backend.models import SubscriptionPlan
import uuid
import random
import re
from django.db.models import Max
# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)
    
  
class CustomUser(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("user", "User"),
        ("sub_admin", "Sub Admin"),
    )

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    name = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    unique_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True, blank=True, null=True
    )
    is_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True
    )

    fcm_token = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True
    )

    # 🆔 Aadhaar Card (PDF / Image)
    aadhaar_card = models.FileField(
        upload_to='aadhaar_cards/',
        null=True,
        blank=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = self.generate_unique_id()
        super().save(*args, **kwargs)

    def generate_unique_id(self):
        # --- 1️⃣ Get first 3 letters of name ---
        if self.name:
            name_part = re.sub(r'[^A-Za-z]', '', self.name).upper()[:3]
        else:
            name_part = "USR"

        name_part = name_part.ljust(3, "X")  # Ensure 3 letters

        # --- 2️⃣ Get 5 random digits from phone number ---
        if self.phone_number:
            digits = re.sub(r'\D', '', self.phone_number)
            phone_part = ''.join(random.sample(digits, min(5, len(digits))))
            phone_part = phone_part.ljust(5, "0")
        else:
            phone_part = ''.join(random.choices("0123456789", k=5))

        # --- 3️⃣ Serial number (001, 002...) ---
        last_user = (
            CustomUser.objects
            .filter(unique_id__startswith=f"USR-{name_part}-")
            .aggregate(max_id=Max("unique_id"))
        )

        if last_user["max_id"]:
            last_serial = int(last_user["max_id"].split("-")[-1])
            serial = f"{last_serial + 1:03d}"
        else:
            serial = "001"

        return f"USR-{name_part}-{phone_part}-{serial}"


    def __str__(self):
        return self.email
    
class PhoneOTP(models.Model):
    phone_number = models.CharField(max_length=15, db_index=True)
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)


class UserImage(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="user_images"
    )

    image = models.ImageField(
        upload_to="user_images/"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.email} - Image {self.id}"


class MatrimonyProfile(models.Model):
    ACCOUNT_FOR_CHOICES = (
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('friend', 'Friend'),
        ('myself', 'Myself'),
        ('relative', 'Relative'),
    )

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )

    PHYSICAL_STATUS_CHOICES = (
        ('normal', 'Normal'),
        ('challenged', 'Physically Challenged'),
    )

    MARITAL_STATUS_CHOICES = (
        ('never_married', 'Never Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
    )

    EDUCATION_CHOICES = (
        ('diploma', 'Diploma'),
        ('bachelors', "Bachelor's Degree"),
        ('masters', "Master's Degree"),
        ('phd', 'PhD'),
        ('professional', 'Professional Degree'),
        ('other', 'Other'),
    )

    OCCUPATION_CHOICES = (
        ('software', 'Software Engineer'),
        ('doctor', 'Doctor'),
        ('teacher', 'Teacher'),
        ('business', 'Business'),
        ('govt', 'Govt Service'),
        ('banking', 'Banking'),
        ('other', 'Other'),
    )

    INCOME_CHOICES = (
        ('2-5', '2–5 Lakhs'),
        ('5-10', '5–10 Lakhs'),
        ('10-15', '10–15 Lakhs'),
        ('15-25', '15–25 Lakhs'),
        ('25-50', '25–50 Lakhs'),
        ('50+', '50+ Lakhs'),
    )

    FAMILY_STATUS_CHOICES = (
        ('middle', 'Middle Class'),
        ('upper_middle', 'Upper Middle Class'),
        ('rich', 'Rich'),
    )

    FAMILY_WORTH_CHOICES = (
        ('5', '5 Lakh'),
        ('5-10', '5–10 Lakh'),
        ('10-25', '10–25 Lakh'),
        ('25-50', '25–50 Lakh'),
        ('50-100', '50 Lakh – 1 Crore'),
        ('1cr+', '1 Crore+'),
    )

    # 🔗 Relation
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # 🧍 Basic Info
    this_account_for = models.CharField(max_length=20, choices=ACCOUNT_FOR_CHOICES)
    mother_tongue = models.CharField(max_length=50)

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    date_of_birth = models.DateField()
    height = models.CharField(max_length=10)

    physical_status = models.CharField(
        max_length=20,
        choices=PHYSICAL_STATUS_CHOICES
    )

    # 💍 Marriage Info
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES
    )

    children_count = models.PositiveIntegerField(null=True, blank=True)
    children_with_me = models.BooleanField(null=True, blank=True)

    # 🕉 Religion & Caste
    religion = models.ForeignKey(
        Caste,
        on_delete=models.SET_NULL,
        null=True,
        related_name='religion_profiles',
        limit_choices_to={'level': 'religion'}
    )

    caste = models.ForeignKey(
        Caste,
        on_delete=models.SET_NULL,
        null=True,
        related_name='caste_profiles',
        limit_choices_to={'level': 'caste'}
    )

    sub_caste = models.CharField(max_length=100, blank=True, null=True)
    willing_inter_caste = models.BooleanField(default=False)

    # 🎓 Education & Job
    education = models.CharField(max_length=20, choices=EDUCATION_CHOICES)
    field_of_study = models.CharField(max_length=100)

    occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES)
    annual_income = models.CharField(max_length=10, choices=INCOME_CHOICES)

    # 🌍 Location
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    # 👪 Family
    family_status = models.CharField(max_length=20, choices=FAMILY_STATUS_CHOICES)
    family_worth = models.CharField(max_length=20, choices=FAMILY_WORTH_CHOICES)

    # 📝 About
    description = models.TextField(blank=True)

    # 📜 Legal
    terms_accepted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} Profile"



class PersonalLifestyle(models.Model):

    SMOKING_DRINKING_CHOICES = (
        ('never', 'Never'),
        ('occasionally', 'Occasionally'),
        ('regularly', 'Regularly'),
        ('quit', 'Quit'),
    )

    EATING_HABITS_CHOICES = (
        ('eggetarian', 'Eggetarian'),
        ('veg', 'Vegetarian'),
        ('non_veg', 'Non-Vegetarian'),
    )

    # 🔗 Relation
    profile = models.OneToOneField(
        MatrimonyProfile,
        on_delete=models.CASCADE,
        related_name='lifestyle'
    )

    # 🎵 Multi-select (ManyToMany)
    music_genres = models.ManyToManyField(MusicGenre, blank=True)
    music_activities = models.ManyToManyField(MusicActivity, blank=True)
    reading_preferences = models.ManyToManyField(ReadingPreference, blank=True)
    movie_tv_genres = models.ManyToManyField(MovieGenre, blank=True)

    # 📚 Reading & Language
    reading_language = models.CharField(max_length=100, blank=True)

    # 🏃 Lifestyle
    favorite_sports = models.CharField(max_length=100, blank=True)
    fitness_activity = models.CharField(max_length=100, blank=True)

    spoken_languages = models.CharField(max_length=200, blank=True)
    cooking = models.BooleanField(default=False)

    # 🕉 Birth & Astrology
    time_of_birth = models.TimeField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=100, blank=True)
    nakshatra = models.CharField(max_length=50, blank=True)
    rashi = models.CharField(max_length=50, blank=True)

    # 🍽 Habits
    eating_habits = models.CharField(
        max_length=20,
        choices=EATING_HABITS_CHOICES
    )

    smoking = models.CharField(
        max_length=20,
        choices=SMOKING_DRINKING_CHOICES
    )

    drinking = models.CharField(
        max_length=20,
        choices=SMOKING_DRINKING_CHOICES
    )

    # 🎓 Education Details
    college = models.CharField(max_length=150, blank=True)
    course_degree = models.CharField(max_length=100, blank=True)
    passing_year = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Lifestyle - {self.profile.user.email}"


class SubscriptionPayment(models.Model):

    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    subscription = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=20,
        default="razorpay",
    )

    transaction_id = models.CharField(
        max_length=255,
        unique=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Subscription Payment"
        verbose_name_plural = "Subscription Payments"

    def __str__(self):
        return f"{self.user.email} - ₹{self.amount} - {self.payment_status}"
