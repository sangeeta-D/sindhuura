from django.urls import path    
from .views import *

urlpatterns = [
    path("religions/", ReligionListAPIView.as_view()),
    path("castes/", CasteListByReligionAPIView.as_view()),
    path("login/", LoginAPIView.as_view(), name="login"),
    path('register/',RegisterAPIView.as_view(), name='register'),
    path('add-personal-details/', PersonalLifestyleAPIView.as_view(), name='personal_lifestyle'),
    path("drop-downs/",LifestyleMasterDataAPIView.as_view(),name="lifestyle-master-data"),

    path("subscription-plans/",SubscriptionPlanListAPI.as_view(),name="subscription-plans"),
    path("upload-images/", UserMultipleImageUploadAPI.as_view(), name="upload-images"),
    path("subscription/create-order/", CreateSubscriptionOrderAPIView.as_view()),
    path("subscription/verify-payment/", VerifySubscriptionPaymentAPIView.as_view()),

    path("user-profile/", MatrimonyProfileAPIView.as_view(), name="user-profile"),
    path("user-images/",UserImageListAPIView.as_view(),name="user-images-list"),
    path("delete-image/<int:image_id>/",UserImageDeleteAPIView.as_view(),name="user-image-delete"),

    path("blogs/", BlogListAPIView.as_view(), name="blog-list"),
    path("blogs/<int:blog_id>/", BlogDetailAPIView.as_view(), name="blog-detail")

    
]