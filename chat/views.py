from django.db.models import Q, OuterRef, Subquery
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from chat.models import ChatRoom, ChatMessage
from auth_api.models import SubscriptionPayment
from .serializers import *
from auth_api.api_response import APIResponseMixin

class ChatUserListAPIView(APIView, APIResponseMixin):
    permission_classes = [IsAuthenticated]

    def get_active_subscription(self, user):
        """
        Check if user has an active, non-expired subscription
        Returns True if user has purchased a plan and it hasn't expired
        """
        try:
            # Get the latest successful payment
            latest_payment = (
                SubscriptionPayment.objects
                .filter(user=user, payment_status="success")
                .select_related("subscription")
                .order_by("-paid_at")
                .first()
            )

            if not latest_payment:
                return False

            # Check if subscription plan is active
            if not latest_payment.subscription.is_active:
                return False

            # Check if subscription hasn't expired
            if not latest_payment.paid_at:
                return False

            expiry_date = latest_payment.paid_at + timedelta(
                days=latest_payment.subscription.validity
            )

            return expiry_date > timezone.now()

        except Exception:
            return False

    def get(self, request):
        user = request.user

        # 🔹 Subquery to fetch last message per room
        last_message_qs = ChatMessage.objects.filter(
            chat_room=OuterRef("pk")
        ).order_by("-created_at")

        chat_rooms = (
            ChatRoom.objects
            .filter(Q(user1=user) | Q(user2=user))
            .exclude(user1__is_deleted=True)
            .exclude(user2__is_deleted=True)
            .annotate(
                last_message_text=Subquery(
                    last_message_qs.values("message_text")[:1]
                ),
                last_message_time=Subquery(
                    last_message_qs.values("created_at")[:1]
                )
            )
            .select_related("user1", "user2")
            .order_by("-last_message_time", "-created_at")
        )

        response_data = []

        for room in chat_rooms:
            other_user = room.user2 if room.user1 == user else room.user1

            response_data.append({
                "chat_room_id": room.id,
                "user_id": other_user.id,
                "unique_id": other_user.unique_id,
                "name": other_user.name,
                "profile_image": other_user.profile_image,
                "is_subscribed": self.get_active_subscription(other_user),
                "last_message": room.last_message_text,
                "last_message_time": room.last_message_time,
            })

        serializer = ChatUserListSerializer(response_data, many=True)

        return self.success_response(
            message="Chat users fetched successfully",
            data=serializer.data
        )


class ChatHistoryAPIView(APIView, APIResponseMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_room_id):
        user = request.user

        # 🔹 Validate chat room
        chat_room = get_object_or_404(ChatRoom, id=chat_room_id)

        # 🔐 Ensure user is part of the chat
        if user not in [chat_room.user1, chat_room.user2]:
            return self.error_response(
                "You are not allowed to view this chat",
                status_code=403
            )

        # 🔹 Fetch chat messages
        messages = (
            ChatMessage.objects
            .filter(chat_room=chat_room)
            .select_related("sender", "receiver")
            .order_by("created_at")
        )

        serializer = ChatMessageSerializer(
            messages,
            many=True,
            context={'current_user': user}
        )

        return self.success_response(
            message="Chat history fetched successfully",
            data=serializer.data
        )