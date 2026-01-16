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
            sent_requests = MatchRequest.objects.filter(
                from_user=request.user
            ).select_related(
                "to_user"
            ).order_by("-created_at")

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
                to_user=request.user,status="pending" 
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
    permission_classes = []  # add IsAuthenticated if needed

    def get(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)

        serializer = UserDetailSerializer(user)

        return self.success_response(
            message="User details fetched successfully",
            data=serializer.data,
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

        match_request.status = "accepted"
        match_request.save(update_fields=["status", "updated_at"])

        return self.success_response(
            message="Match request accepted successfully",
            data={
                "match_request_id": match_request.id,
                "from_user": match_request.from_user.email,
                "status": match_request.status
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