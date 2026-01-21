import pytz
from rest_framework import serializers
from datetime import date
from auth_api.models import MatrimonyProfile,PersonalLifestyle,UserImage
from backend.models import Caste, Event
from auth_api.models import CustomUser
from .models import *
from sindhuura.datetime_utils import to_ist
from django.utils import timezone


class CasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caste
        fields = ("id", "name")


class MatchProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.name")
    profile_image = serializers.ImageField(source="user.profile_image")
    age = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    is_verified = serializers.BooleanField(source="user.is_verified", read_only=True)



    religion = CasteSerializer(read_only=True)
    caste = CasteSerializer(read_only=True)

    class Meta:
        model = MatrimonyProfile
        fields = (
            'user_id',
            'is_verified',
            'id',
            "profile_image",
            "name",
            "height",
            "occupation",
            "city",
            "state",
            "age",
            "religion",
            "caste",
        )

    def get_age(self, obj):
        if not obj.date_of_birth:
            return None

        today = date.today()
        dob = obj.date_of_birth

        return (
            today.year - dob.year
            - ((today.month, today.day) < (dob.month, dob.day))
        )


class SendMatchRequestSerializer(serializers.Serializer):
    to_user_id = serializers.IntegerField()

    def validate_to_user_id(self, value):
        request = self.context.get("request")

        if not CustomUser.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist")

        if request.user.id == value:
            raise serializers.ValidationError("You cannot send a request to yourself")

        return value


class SentMatchRequestSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = MatchRequest
        fields = (
            "id",
            "status",
            "created_at",
            "profile",
        )

    def get_created_at(self, obj):
        return to_ist(obj.created_at)

    def get_profile(self, obj):
        try:
            profile = obj.to_user.profile
            return MatchProfileSerializer(
                profile,
                context=self.context
            ).data
        except MatrimonyProfile.DoesNotExist:
            return None

class ReceivedMatchRequestSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = MatchRequest
        fields = (
            "id",
            "status",
            "created_at",
            "profile",
        )

    def get_created_at(self, obj):
        return to_ist(obj.created_at)

    def get_profile(self, obj):
        try:
            profile = obj.from_user.profile
            return MatchProfileSerializer(
                profile,
                context=self.context
            ).data
        except MatrimonyProfile.DoesNotExist:
            return None


class UserImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserImage
        fields = ["id", "image", "uploaded_at"]


class PersonalLifestyleSerializer(serializers.ModelSerializer):
    music_genres = serializers.StringRelatedField(many=True)
    music_activities = serializers.StringRelatedField(many=True)
    reading_preferences = serializers.StringRelatedField(many=True)
    movie_tv_genres = serializers.StringRelatedField(many=True)

    class Meta:
        model = PersonalLifestyle
        fields = "__all__"


class MatrimonyProfileSerializer(serializers.ModelSerializer):
    lifestyle = PersonalLifestyleSerializer(read_only=True)

    religion = serializers.StringRelatedField()
    caste = serializers.StringRelatedField()

    class Meta:
        model = MatrimonyProfile
        fields = "__all__"


class UserDetailSerializer(serializers.ModelSerializer):
    profile = MatrimonyProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "name",
            "role",
            "address",
            "profile_image",
            "is_active",
            "date_joined",
            "profile",
        ]

class PaidUserImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserImage
        fields = ["id", "image", "uploaded_at"]

class PaidHoroscopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalLifestyle
        fields = [
            "time_of_birth",
            "place_of_birth",
            "nakshatra",
            "rashi",
        ]


class RevealUserDetailsSerializer(serializers.ModelSerializer):
    user_images = PaidUserImageSerializer(many=True, read_only=True)
    horoscope = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "phone_number",
            "user_images",
            "horoscope",
        ]

    def get_horoscope(self, obj):
        try:
            lifestyle = obj.profile.lifestyle
            return PaidHoroscopeSerializer(lifestyle).data
        except AttributeError:
            return None



class SuccessStoryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuccessStoryImage
        fields = ("id", "image")

# add success story
class SuccessStoryCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = SuccessStory
        fields = (
            "groom_name",
            "bride_name",
            "wedding_date",
            "venue",
            "description",
            "images",
        )

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        user = self.context["request"].user

        story = SuccessStory.objects.create(
            created_by=user if user.is_authenticated else None,
            **validated_data
        )

        for img in images:
            SuccessStoryImage.objects.create(
                success_story=story,
                image=img
            )

        return story


# fetch success story
class SuccessStoryImageListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = SuccessStoryImage
        fields = ("id", "image")

    def get_image(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url
    
class SuccessStoryListSerializer(serializers.ModelSerializer):
    images = SuccessStoryImageListSerializer(many=True, read_only=True)
    couple_name = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = SuccessStory
        fields = (
            "id",
            "couple_name",
            "bride_name",
            "groom_name",
            "wedding_date",
            "venue",
            "description",
            "images",
            "created_at",
        )

    def get_couple_name(self, obj):
        return obj.couple_name()

    def get_created_at(self, obj):
        """
        Convert UTC time to IST and format it
        """
        ist_tz = pytz.timezone("Asia/Kolkata")

        # Ensure datetime is timezone-aware
        created_at = obj.created_at
        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, timezone.utc)

        ist_time = created_at.astimezone(ist_tz)

        return ist_time.strftime("%d %b %Y, %I:%M %p")


# my success story
class UserSuccessStorySerializer(serializers.ModelSerializer):
    images = SuccessStoryImageListSerializer(many=True, read_only=True)
    couple_name = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = SuccessStory
        fields = (
            "id",
            "couple_name",
            "bride_name",
            "groom_name",
            "wedding_date",
            "venue",
            "description",
            "images",
            "created_at",
        )

    def get_couple_name(self, obj):
        return obj.couple_name()

    def get_created_at(self, obj):
        ist = pytz.timezone("Asia/Kolkata")

        created_at = obj.created_at
        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, timezone.utc)

        return created_at.astimezone(ist).strftime("%d %b %Y, %I:%M %p")


class StoryBannerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = StoryBanner
        fields = ['id', 'image_url', 'created_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class EventSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    event_datetime_display = serializers.SerializerMethodField()
    event_status = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "event_name",
            "event_datetime",
            "event_datetime_display",
            "event_status",
            "venue",
            "city",
            "description",
            "image",
        ]

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_event_datetime_display(self, obj):
        return obj.event_datetime.strftime("%d %b %Y, %I:%M %p")

    def get_event_status(self, obj):
        now = timezone.now()
        if obj.event_datetime >= now:
            return "upcoming"
        return "completed"