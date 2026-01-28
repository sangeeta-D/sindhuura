from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from backend.models import Caste, SubscriptionPlan
from auth_api.models import MatrimonyProfile
from auth_api.models import CustomUser as User
from .models import *
from django.utils import timezone
import pytz
from backend.models import Blog

class RegisterSerializer(serializers.Serializer):
    # 🔐 USER FIELDS
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    phone_number = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)

    profile_image = serializers.ImageField(required=False, allow_null=True)
    aadhaar_card = serializers.FileField(required=False, allow_null=True)

    # 🧍 MATRIMONY PROFILE FIELDS
    this_account_for = serializers.ChoiceField(
        choices=MatrimonyProfile.ACCOUNT_FOR_CHOICES
    )
    mother_tongue = serializers.CharField()

    gender = serializers.ChoiceField(
        choices=MatrimonyProfile.GENDER_CHOICES
    )

    date_of_birth = serializers.DateField()
    height = serializers.CharField()

    physical_status = serializers.ChoiceField(
        choices=MatrimonyProfile.PHYSICAL_STATUS_CHOICES
    )
    marital_status = serializers.ChoiceField(
        choices=MatrimonyProfile.MARITAL_STATUS_CHOICES
    )

    children_count = serializers.IntegerField(
        required=False, allow_null=True
    )
    children_with_me = serializers.BooleanField(
        required=False, allow_null=True
    )

    religion = serializers.PrimaryKeyRelatedField(
        queryset=Caste.objects.filter(level="religion")
    )

    caste = serializers.PrimaryKeyRelatedField(
        queryset=Caste.objects.filter(level="caste"),
        required=False,
        allow_null=True
    )

    sub_caste = serializers.CharField(
        required=False, allow_blank=True
    )
    willing_inter_caste = serializers.BooleanField()

    education = serializers.ChoiceField(
        choices=MatrimonyProfile.EDUCATION_CHOICES
    )
    field_of_study = serializers.CharField()

    occupation = serializers.ChoiceField(
        choices=MatrimonyProfile.OCCUPATION_CHOICES
    )
    annual_income = serializers.ChoiceField(
        choices=MatrimonyProfile.INCOME_CHOICES
    )

    country = serializers.CharField()
    state = serializers.CharField()
    city = serializers.CharField()

    family_status = serializers.ChoiceField(
        choices=MatrimonyProfile.FAMILY_STATUS_CHOICES
    )
    family_worth = serializers.ChoiceField(
        choices=MatrimonyProfile.FAMILY_WORTH_CHOICES
    )

    description = serializers.CharField(
        required=False, allow_blank=True
    )

    terms_accepted = serializers.BooleanField()

    # ✅ VALIDATIONS
    def validate(self, data):

        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")

        if not data["terms_accepted"]:
            raise serializers.ValidationError(
                "You must accept terms & conditions"
            )

        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                "Email already registered"
            )

        if (
            data["marital_status"] != "never_married"
            and data.get("children_count") is None
        ):
            raise serializers.ValidationError(
                "Children count required for married profiles"
            )

        return data

    # 🔥 ATOMIC CREATE
    @transaction.atomic
    def create(self, validated_data):

        # Remove non-model fields
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")

        # Pop USER-ONLY fields
        profile_image = validated_data.pop("profile_image", None)
        aadhaar_card = validated_data.pop("aadhaar_card", None)

        # Create USER
        user = User.objects.create_user(
            email=validated_data.pop("email"),
            password=password,
            phone_number=validated_data.pop("phone_number", None),
            name=validated_data.pop("name", None),
            is_active=True,
        )

        # Save files
        if profile_image:
            user.profile_image = profile_image
        if aadhaar_card:
            user.aadhaar_card = aadhaar_card

        user.save()

        # Create MATRIMONY PROFILE
        profile = MatrimonyProfile.objects.create(
            user=user,
            **validated_data
        )

        return user, profile



class PersonalLifestyleSerializer(serializers.ModelSerializer):

    music_genres = serializers.PrimaryKeyRelatedField(
        queryset=MusicGenre.objects.all(),
        many=True,
        required=False
    )
    music_activities = serializers.PrimaryKeyRelatedField(
        queryset=MusicActivity.objects.all(),
        many=True,
        required=False
    )
    reading_preferences = serializers.PrimaryKeyRelatedField(
        queryset=ReadingPreference.objects.all(),
        many=True,
        required=False
    )
    movie_tv_genres = serializers.PrimaryKeyRelatedField(
        queryset=MovieGenre.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = PersonalLifestyle
        exclude = ("profile",)

    @transaction.atomic
    def create(self, validated_data):
        profile = self.context["profile"]

        m2m_fields = {
            "music_genres": validated_data.pop("music_genres", []),
            "music_activities": validated_data.pop("music_activities", []),
            "reading_preferences": validated_data.pop("reading_preferences", []),
            "movie_tv_genres": validated_data.pop("movie_tv_genres", []),
        }

        lifestyle, _ = PersonalLifestyle.objects.update_or_create(
            profile=profile,
            defaults=validated_data
        )

        for field, values in m2m_fields.items():
            getattr(lifestyle, field).set(values)

        return lifestyle
    
class BaseNameSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name")

class MusicGenreSerializer(BaseNameSerializer):
    class Meta(BaseNameSerializer.Meta):
        model = MusicGenre


class MusicActivitySerializer(BaseNameSerializer):
    class Meta(BaseNameSerializer.Meta):
        model = MusicActivity


class ReadingPreferenceSerializer(BaseNameSerializer):
    class Meta(BaseNameSerializer.Meta):
        model = ReadingPreference


class MovieGenreSerializer(BaseNameSerializer):
    class Meta(BaseNameSerializer.Meta):
        model = MovieGenre


class SubscriptionPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "plan_name",
            "price",
            "validity",
            "description",
            "is_active",
        ]


# images 
class MultipleImageUploadSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False
    )


# religion 
class ReligionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caste
        fields = ["id", "name"]

# caste
class CasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caste
        fields = ["id", "name"]

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(
        source="subscription.plan_name",
        read_only=True
    )

    class Meta:
        model = SubscriptionPayment
        fields = (
            "id",
            "plan_name",
            "amount",
            "payment_method",
            "payment_status",
            "transaction_id",
            "paid_at",
            "created_at",
        )



    
# user profile serializer

class UserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    unique_id = serializers.CharField(read_only=True)
    class Meta:
        model = CustomUser
        fields = ("name", "address", "profile_image","unique_id")

    def get_profile_image(self, obj):
        request = self.context.get("request")

        if obj.profile_image:
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url

        return None

class FetchPersonalLifestyleSerializer(serializers.ModelSerializer):
    # 🔹 READ (GET → id + name)
    music_genres = MusicGenreSerializer(many=True, read_only=True)
    music_activities = MusicActivitySerializer(many=True, read_only=True)
    reading_preferences = ReadingPreferenceSerializer(many=True, read_only=True)
    movie_tv_genres = MovieGenreSerializer(many=True, read_only=True)

    # 🔹 WRITE (PATCH → IDs)
    music_genre_ids = serializers.PrimaryKeyRelatedField(
        queryset=MusicGenre.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source="music_genres"
    )

    music_activity_ids = serializers.PrimaryKeyRelatedField(
        queryset=MusicActivity.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source="music_activities"
    )

    reading_preference_ids = serializers.PrimaryKeyRelatedField(
        queryset=ReadingPreference.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source="reading_preferences"
    )

    movie_tv_genre_ids = serializers.PrimaryKeyRelatedField(
        queryset=MovieGenre.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source="movie_tv_genres"
    )

    class Meta:
        model = PersonalLifestyle
        exclude = ("id", "profile")

    def update(self, instance, validated_data):
        m2m_fields = [
            "music_genres",
            "music_activities",
            "reading_preferences",
            "movie_tv_genres",
        ]

        for field in m2m_fields:
            if field in validated_data:
                getattr(instance, field).set(validated_data.pop(field))

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    

class MatrimonyProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer()
    lifestyle = FetchPersonalLifestyleSerializer(required=False)

    class Meta:
        model = MatrimonyProfile
        exclude = ("id", "created_at")

    def update(self, instance, validated_data):
        # ---- Update User ----
        user_data = validated_data.pop("user", None)
        if user_data:
            user_serializer = UserProfileSerializer(
                instance=instance.user,
                data=user_data,
                partial=True
            )
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

        # ---- Update Matrimony Profile ----
        lifestyle_data = validated_data.pop("lifestyle", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # ---- Update / Create Lifestyle (Optional) ----
        if lifestyle_data:
            lifestyle, _ = PersonalLifestyle.objects.get_or_create(
                profile=instance
            )

            lifestyle_serializer = FetchPersonalLifestyleSerializer(
                instance=lifestyle,
                data=lifestyle_data,
                partial=True
            )
            lifestyle_serializer.is_valid(raise_exception=True)
            lifestyle_serializer.save()

        return instance
    

# user multiple images
class UserImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = UserImage
        fields = ("id", "image")

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

        
# blog serializer
class BlogListSerializer(serializers.ModelSerializer):
    cover_media_url = serializers.SerializerMethodField()
    cover_media_type = serializers.CharField(read_only=True)
    created_at_ist = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = [
            "id",
            "title",
            "short_description",
            "cover_media_url",
            "cover_media_type",
            "is_featured",
            "views_count",
            "created_at_ist",
        ]

    def get_cover_media_url(self, obj):
        request = self.context.get("request")
        if obj.cover_media and request:
            return request.build_absolute_uri(obj.cover_media.url)
        return None

    def get_created_at_ist(self, obj):
        ist = pytz.timezone("Asia/Kolkata")
        return obj.created_at.astimezone(ist).strftime("%d %b %Y, %I:%M %p")


class BlogDetailSerializer(serializers.ModelSerializer):
    cover_media_url = serializers.SerializerMethodField()
    cover_media_type = serializers.CharField(read_only=True)
    created_at_ist = serializers.SerializerMethodField()
    updated_at_ist = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = [
            "id",
            "title",
            "short_description",
            "content",
            "cover_media_url",
            "cover_media_type",
            "is_featured",
            "views_count",
            "created_at_ist",
            "updated_at_ist",
        ]

    def get_cover_media_url(self, obj):
        request = self.context.get("request")
        if obj.cover_media and request:
            return request.build_absolute_uri(obj.cover_media.url)
        return None

    def get_created_at_ist(self, obj):
        ist = pytz.timezone("Asia/Kolkata")
        return obj.created_at.astimezone(ist).strftime("%d %b %Y, %I:%M %p")

    def get_updated_at_ist(self, obj):
        ist = pytz.timezone("Asia/Kolkata")
        return obj.updated_at.astimezone(ist).strftime("%d %b %Y, %I:%M %p")



# fcm token serializer
class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["fcm_token"]

    def validate_fcm_token(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("FCM token cannot be empty")
        return value.strip()