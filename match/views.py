from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.db.models import Q
from .serializers import *
from .models import *
from auth_api.models import MatrimonyProfile
from auth_api.api_response import APIResponseMixin
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework import status as drf_status
from chat.models import ChatRoom
from datetime import timedelta
from auth_api.models import CustomUser
from auth_api.models import SubscriptionPayment
from chat.firebase import send_push_notification
from django.utils import timezone

class MatchProfileListAPIView(APIResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # 🔹 Get logged-in user's matrimony profile
            try:
                my_profile = user.profile
            except MatrimonyProfile.DoesNotExist:
                return self.error_response(
                    "Matrimony profile not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # 🔹 Base gender filter
            if my_profile.gender == 'male':
                matches = MatrimonyProfile.objects.filter(gender='female')
            elif my_profile.gender == 'female':
                matches = MatrimonyProfile.objects.filter(gender='male')
            else:
                matches = MatrimonyProfile.objects.all()

            # 🔹 Exclude self
            matches = matches.exclude(user=user)
            
            # 🔹 Exclude soft-deleted users
            matches = matches.exclude(user__is_deleted=True)

            # 🔹 Religion / caste filtering
            if my_profile.religion:
                if my_profile.willing_inter_caste:
                    matches = matches.filter(religion=my_profile.religion)
                else:
                    if my_profile.caste:
                        matches = matches.filter(
                            religion=my_profile.religion,
                            caste=my_profile.caste
                        )
                    else:
                        matches = matches.filter(religion=my_profile.religion)

            # 🔹 EXCLUDE USERS WITH EXISTING MATCH REQUESTS
            requested_user_ids = MatchRequest.objects.filter(
                Q(from_user=user) | Q(to_user=user)
            ).values_list("from_user_id", "to_user_id")

            # Flatten IDs
            exclude_user_ids = set()
            for from_id, to_id in requested_user_ids:
                exclude_user_ids.add(from_id)
                exclude_user_ids.add(to_id)

            matches = matches.exclude(user__id__in=exclude_user_ids)

            # 🔹 Apply caste filter only if user is open to inter-caste marriages
            if my_profile.willing_inter_caste:
                caste = request.query_params.get('caste')
                if caste:
                    matches = matches.filter(caste__id=caste)

            # 🔹 Apply common filters
            education = request.query_params.get('education')
            if education:
                matches = matches.filter(education=education)

            annual_income = request.query_params.get('annual_income')
            if annual_income:
                matches = matches.filter(annual_income=annual_income)

            country = request.query_params.get('country')
            if country:
                matches = matches.filter(country__icontains=country)

            state = request.query_params.get('state')
            if state:
                matches = matches.filter(state__icontains=state)

            city = request.query_params.get('city')
            if city:
                matches = matches.filter(city__icontains=city)

            family_status = request.query_params.get('family_status')
            if family_status:
                matches = matches.filter(family_status=family_status)

            marital_status = request.query_params.get('marital_status')
            if marital_status:
                matches = matches.filter(marital_status=marital_status)

            # 🔹 Apply lifestyle filters
            smoking = request.query_params.get('smoking')
            if smoking:
                matches = matches.filter(lifestyle__smoking=smoking)

            drinking = request.query_params.get('drinking')
            if drinking:
                matches = matches.filter(lifestyle__drinking=drinking)

            eating_habits = request.query_params.get('eating_habits')
            if eating_habits:
                matches = matches.filter(lifestyle__eating_habits=eating_habits)

            matches = matches.order_by("-created_at")

            serializer = MatchProfileSerializer(
                matches,
                many=True,
                context={"request": request}
            )

            return self.success_response(
                message="Matching profiles fetched successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return self.error_response(
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

# search API
class MatrimonyProfileSearchAPIView(APIResponseMixin, APIView):
    """
    Search Matrimony Profiles based on:
    - Email
    - Phone Number
    - Name
    - Unique ID
    """

    def get(self, request):
        search_query = request.query_params.get("q")

        if not search_query:
            return self.error_response(
                "Search query parameter 'q' is required",
                status_code=drf_status.HTTP_400_BAD_REQUEST
            )

        profiles = (
            MatrimonyProfile.objects
            .select_related("user", "religion", "caste")
            .filter(
                Q(user__email__icontains=search_query) |
                Q(user__phone_number__icontains=search_query) |
                Q(user__name__icontains=search_query) |
                Q(user__unique_id__icontains=search_query)
            )
            .exclude(user__is_deleted=True)
        )

        if not profiles.exists():
            return self.success_response(
                message="No matching profiles found",
                data=[]
            )

        serializer = MatchProfileSerializer(profiles, many=True)

        return self.success_response(
            message="Profiles fetched successfully",
            data=serializer.data
        )


class SendMatchRequestAPIView(APIResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, profile_id):
        from_user = request.user

        # 🔍 Get opposite user's profile
        to_profile = get_object_or_404(
            MatrimonyProfile,
            id=profile_id
        )

        to_user = to_profile.user

        # ❌ Prevent sending request to self
        if from_user == to_user:
            return self.error_response(
                "You cannot send a match request to yourself",
                status_code=status.HTTP_400_BAD_REQUEST
            )        
        # ❌ Prevent sending request to deleted account
        if to_user.is_deleted:
            return self.error_response(
                "This user account has been deleted",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        # 🔒 Prevent duplicate requests
        if MatchRequest.objects.filter(
            from_user=from_user,
            to_user=to_user
        ).exists():
            return self.error_response(
                "Match request already sent",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Create match request
        match_request = MatchRequest.objects.create(
            from_user=from_user,
            to_user=to_user
        )
        Notification.objects.create(
            recipient=to_user,
            sender=from_user,
            notification_type="match_request",
            title="New Match Request",
            message=f"You have received a match request from {from_user.name or from_user.email}",
            match_request=match_request
        )

        # Debug: Print notification details
        print(f"Debug: Match request created. Sending notification to {to_user.email}, token: {to_user.fcm_token}")

        # Send FCM notification to the recipient
        send_push_notification(
            to_user.fcm_token,
            "New Match Request",
            f"You have received a match request from {from_user.name or from_user.email}"
        )

        return self.success_response(
            message="Match request sent successfully",
            data={
                "request_id": match_request.id,
                "status": match_request.status
            },
            status_code=status.HTTP_201_CREATED
        )
    

class SentMatchRequestListAPIView(APIResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            search_query = request.query_params.get("q")

            sent_requests = (
                MatchRequest.objects
                .filter(from_user=request.user)
                .select_related(
                    "to_user",
                    "to_user__profile",
                    "to_user__profile__religion",
                    "to_user__profile__caste"
                )
                .order_by("-created_at")
            )

            # 🔍 Apply search if query exists
            if search_query:
                sent_requests = sent_requests.filter(
                    Q(to_user__email__icontains=search_query) |
                    Q(to_user__phone_number__icontains=search_query) |
                    Q(to_user__name__icontains=search_query) |
                    Q(to_user__unique_id__icontains=search_query)
                )

            serializer = SentMatchRequestSerializer(
                sent_requests,
                many=True,
                context={"request": request}
            )

            return self.success_response(
                message="Sent match requests fetched successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return self.error_response(
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        

class ReceivedMatchRequestListAPIView(APIResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            received_requests = MatchRequest.objects.filter(
                to_user=request.user,status__in=["pending", "accepted"]
            ).select_related(
                "from_user"
            ).order_by("-created_at")

            serializer = ReceivedMatchRequestSerializer(
                received_requests,
                many=True,
                context={"request": request}
            )

            return self.success_response(
                message="Received interest requests fetched successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return self.error_response(
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        

class UserFullDetailAPIView(APIView, APIResponseMixin):
    permission_classes = []  # Add IsAuthenticated if needed

    def get(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)

        serializer = UserDetailSerializer(
            user,
            context={"request": request}
        )
        serializer_data = serializer.data

        # 🔹 Remove contact-related fields
        serializer_data.pop("email", None)
        serializer_data.pop("phone_number", None)
        serializer_data.pop("user_images", None)

        # 🔹 Remove horoscope / astrology details
        profile = serializer_data.get("profile")
        if profile:
            lifestyle = profile.get("lifestyle")
            if lifestyle:
                for field in [
                    "time_of_birth",
                    "place_of_birth",
                    "nakshatra",
                    "rashi"
                ]:
                    lifestyle.pop(field, None)

        return self.success_response(
            message="User details fetched successfully",
            data=serializer_data,
            status_code=status.HTTP_200_OK
        )

class RevealUserFullDetailAPIView(APIView, APIResponseMixin):
    permission_classes = [IsAuthenticated]  # ✅ Always enforce auth

    def get(self, request, user_id):
        viewer = request.user
        viewed_user = get_object_or_404(CustomUser, id=user_id)

        # ✅ Prevent viewing own profile
        if viewer.id == viewed_user.id:
            return self.error_response(
                "You cannot view your own contact details.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Prevent viewing deleted accounts
        if viewed_user.is_deleted:
            return self.error_response(
                "This user account has been deleted.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # =====================================================
        # ✅ SUBSCRIPTION VALIDATION
        # =====================================================

        # 1️⃣ Not subscribed → clean message, no data
        if not viewer.is_subscribed:
            return self.error_response(
                "Upgrade your plan to view contact details.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # 2️⃣ Subscription expired → mark and block
        if viewer.subscription_expires_at and viewer.subscription_expires_at < timezone.now():
            viewer.is_subscribed = False
            viewer.save(update_fields=["is_subscribed"])
            return self.error_response(
                "Your subscription has expired. Please upgrade your plan.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # =====================================================
        # ✅ GET ACTIVE PLAN FOR REVEAL LIMIT
        # =====================================================

        payment = SubscriptionPayment.objects.filter(
            user=viewer,
            payment_status="success"
        ).select_related("subscription").order_by("-created_at").first()

        if not payment or not payment.subscription:
            return self.error_response(
                "No active subscription plan found. Please upgrade your plan.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        reveal_limit = payment.subscription.reveal_limit

        # =====================================================
        # ✅ CHECK IF ALREADY REVEALED (re-visit = free)
        # =====================================================

        contact_view = ContactInfoView.objects.filter(
            viewer=viewer,
            viewed_user=viewed_user
        ).first()

        is_first_view = False

        if not contact_view:
            # New profile — check limit before allowing
            if viewer.profile_reveal_count >= reveal_limit:
                return self.error_response(
                    f"You've reached your reveal limit of {reveal_limit} profiles. Upgrade your plan for more.",
                    status_code=status.HTTP_403_FORBIDDEN
                )

            # ✅ First time reveal — record it and increment count
            contact_view = ContactInfoView.objects.create(
                viewer=viewer,
                viewed_user=viewed_user,
                views_count=1
            )
            viewer.profile_reveal_count += 1
            viewer.save(update_fields=["profile_reveal_count"])
            is_first_view = True

        else:
            # ✅ Already revealed before — just track visit, no count change
            contact_view.views_count += 1
            contact_view.save(update_fields=["views_count"])

        # =====================================================
        # ✅ RETURN FULL CONTACT DETAILS
        # =====================================================

        serializer = RevealUserDetailsSerializer(viewed_user)

        return self.success_response(
            message="Contact details revealed successfully.",
            data={
                **serializer.data,
                "current_count": viewer.profile_reveal_count,
                "limit": reveal_limit,
                "is_first_view": is_first_view,
            },
            status_code=status.HTTP_200_OK
        )
# accept match request
class AcceptMatchRequestAPIView(APIView, APIResponseMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        user = request.user

        match_request = get_object_or_404(
            MatchRequest,
            id=request_id,
            to_user=user
        )

        if match_request.status != "pending":
            return self.error_response(
                "This match request is already processed.",
                status_code=drf_status.HTTP_400_BAD_REQUEST
            )

        # ✅ Accept match request
        match_request.status = "accepted"
        match_request.save(update_fields=["status", "updated_at"])
        # ✅ Store notification in DB
        Notification.objects.create(
            recipient=match_request.from_user,
            sender=match_request.to_user,
            notification_type="match_accepted",
            title="Match Request Accepted",
            message=f"Your match request to {match_request.to_user.name or match_request.to_user.email} has been accepted",
            match_request=match_request
        )
        # Debug: Print notification details
        print(f"Debug: Match request accepted. Sending notification to {match_request.from_user.email}, token: {match_request.from_user.fcm_token}")

        # Send FCM notification to the sender
        send_push_notification(
            match_request.from_user.fcm_token,
            "Match Request Accepted",
            f"Your match request to {match_request.to_user.name or match_request.to_user.email} has been accepted"
        )

        # ✅ Ensure consistent user order
        user1, user2 = sorted(
            [match_request.from_user, match_request.to_user],
            key=lambda u: u.id
        )

        # ✅ Create chat room if not exists
        chat_room, created = ChatRoom.objects.get_or_create(
            user1=user1,
            user2=user2,
            defaults={
                "match_request": match_request
            }
        )

        return self.success_response(
            message="Match request accepted and chat room created",
            data={
                "match_request_id": match_request.id,
                "chat_room_id": chat_room.id,
                "chat_created": created,
                "users": {
                    "user1": chat_room.user1.email,
                    "user2": chat_room.user2.email
                }
            },
            status_code=drf_status.HTTP_200_OK
        )
    

# reject match request
class RejectMatchRequestAPIView(APIView, APIResponseMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        user = request.user

        match_request = get_object_or_404(
            MatchRequest,
            id=request_id,
            to_user=user
        )

        if match_request.status != "pending":
            return self.error_response(
                "This match request is already processed.",
                status_code=drf_status.HTTP_400_BAD_REQUEST
            )

        match_request.status = "rejected"
        match_request.save(update_fields=["status", "updated_at"])

        return self.success_response(
            message="Match request rejected successfully",
            data={
                "match_request_id": match_request.id,
                "from_user": match_request.from_user.email,
                "status": match_request.status
            },
            status_code=drf_status.HTTP_200_OK
        )


class AddSuccessStoryAPIView(APIResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SuccessStoryCreateSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            story = serializer.save()
            return self.success_response(
                message="Success story added successfully",
                data={
                    "id": story.id,
                    "couple_name": story.couple_name(),
                    "wedding_date": story.wedding_date,
                },
                status_code=drf_status.HTTP_201_CREATED
            )

        return self.error_response(serializer.errors)
    

class DeleteSuccessStoryAPIView(APIView, APIResponseMixin):
    permission_classes = [IsAuthenticated]

    def delete(self, request, story_id):
        # Get story created by logged-in user only
        success_story = get_object_or_404(
            SuccessStory,
            id=story_id,
            created_by=request.user
        )

        success_story.delete()

        return self.success_response(
            message="Success story deleted successfully",
            status_code=drf_status.HTTP_200_OK
        )

class SuccessStoryListAPIView(APIResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = SuccessStory.objects.all().order_by("-created_at")

        # Exclude logged-in user's own success stories
        if request.user.is_authenticated:
            queryset = queryset.exclude(created_by=request.user)

        serializer = SuccessStoryListSerializer(
            queryset,
            many=True,
            context={"request": request}
        )

        return self.success_response(
            message="Success stories fetched successfully",
            data=serializer.data,
            status_code=drf_status.HTTP_200_OK
        )
    

class MySuccessStoriesAPIView(APIResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stories = SuccessStory.objects.filter(
            created_by=request.user
        ).order_by("-created_at")

        serializer = UserSuccessStorySerializer(
            stories,
            many=True,
            context={"request": request}
        )

        return self.success_response(
            message="Your success stories fetched successfully",
            data=serializer.data,
            status_code=drf_status.HTTP_200_OK
        )


# delete succcess story
class DeleteSuccessStoryAPIView(APIResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, story_id):
        story = get_object_or_404(
            SuccessStory,
            id=story_id,
            created_by=request.user  # 🔐 ownership check
        )

        story.delete()

        return self.success_response(
            message="Success story deleted successfully",
            status_code=drf_status.HTTP_200_OK
        )
    

class StoryBannerListAPIView(APIView, APIResponseMixin):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        banners = StoryBanner.objects.all().order_by('-created_at')
        serializer = StoryBannerSerializer(banners, many=True, context={'request': request})
        return self.success_response(
            message="Banner images fetched successfully",
            data=serializer.data
        )
    

class GetEventsAPIView(APIResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        events = Event.objects.all().order_by("-event_datetime")

        serializer = EventSerializer(
            events,
            many=True,
            context={"request": request}
        )

        return self.success_response(
            message="Events fetched successfully",
            data=serializer.data
        )


class ReportReasonListAPIView(APIView, APIResponseMixin):
    """
    GET: Fetch active report reasons
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reasons = ReportReason.objects.filter(is_active=True)
        serializer = ReportReasonSerializer(reasons, many=True)

        return self.success_response(
            message="Report reasons fetched successfully",
            data=serializer.data
        )


class UserReportCreateAPIView(APIView, APIResponseMixin):
    """
    POST: Report a user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserReportCreateSerializer(
            data=request.data,
            context={"request": request}
        )

        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        try:
            report = serializer.save()
        except Exception as e:
            return self.error_response(
                str(e),
                status_code=drf_status.HTTP_400_BAD_REQUEST
            )

        return self.success_response(
            message="User reported successfully",
            data={
                "report_id": report.id,
                "status": report.status
            },
            status_code=drf_status.HTTP_201_CREATED
        )


class NotificationListAPIView(APIResponseMixin, APIView):
    """
    GET: Fetch all notifications for the authenticated user with pagination
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            
            # Get notifications for the user
            notifications = Notification.objects.filter(
                recipient=user
            ).select_related('sender', 'match_request').order_by('-created_at')

            # Pagination
            from auth_api.pagination import BlogPagination
            paginator = BlogPagination()
            paginated_notifications = paginator.paginate_queryset(notifications, request)

            serializer = NotificationSerializer(
                paginated_notifications,
                many=True,
                context={"request": request}
            )

            return self.success_response(
                message="Notifications fetched successfully",
                data={
                    "count": notifications.count(),
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": serializer.data
                },
                status_code=drf_status.HTTP_200_OK
            )

        except Exception as e:
            return self.error_response(
                str(e),
                status_code=drf_status.HTTP_500_INTERNAL_SERVER_ERROR
            )