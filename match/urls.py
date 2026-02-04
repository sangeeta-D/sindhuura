from django.urls import path    
from .views import *

urlpatterns = [
    path("matching-profiles/", MatchProfileListAPIView.as_view(), name="matching-profiles"),
    path("search/", MatrimonyProfileSearchAPIView.as_view(), name="matrimony-search"),
    path('send-interest/<int:profile_id>/', SendMatchRequestAPIView.as_view(), name='send-interest'),
    path("sent-requests/", SentMatchRequestListAPIView.as_view(), name="sent-match-requests"),
    path("received-requests/",ReceivedMatchRequestListAPIView.as_view(),name="received-match-requests"),
    path("details/<int:user_id>/",UserFullDetailAPIView.as_view(),name="user-full-details"),
    path("accept-requests/<int:request_id>/",AcceptMatchRequestAPIView.as_view(),name="accept-match-request"),
    path("reject-requests/<int:request_id>/",RejectMatchRequestAPIView.as_view(),name="reject-match-request"),

    path("add-success-stories/", AddSuccessStoryAPIView.as_view(), name="add-success-story"),
    path("success-stories/", SuccessStoryListAPIView.as_view(), name="success-stories"),
    path(
        "delete-success-stories/<int:story_id>/",
        DeleteSuccessStoryAPIView.as_view(),
        name="delete_success_story"
    ),
    path("my-success-stories/", MySuccessStoriesAPIView.as_view()),
    path('delete-success-story/<int:story_id>/', DeleteSuccessStoryAPIView.as_view(), name='delete-success-story'),
    path('banners/', StoryBannerListAPIView.as_view(), name='api_banners'),
    path('events/', GetEventsAPIView.as_view(), name='api_events'),
    path('reveal-contact/<int:user_id>/', RevealUserFullDetailAPIView.as_view(), name='reveal-contact'),

    path("report-reasons/", ReportReasonListAPIView.as_view()),
    path("report-user/", UserReportCreateAPIView.as_view()),

]