from django.urls import path    
from .views import *

urlpatterns = [
   path("chat-rooms/", ChatUserListAPIView.as_view(), name="chat-user-list"),
   path("chat-history/<int:chat_room_id>/",ChatHistoryAPIView.as_view(),name="chat-history"),
]