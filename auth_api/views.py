from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from .api_response import APIResponseMixin
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework import status as drf_status
from django.contrib.auth import authenticate
import razorpay
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from backend.models import Blog
from django.db.models import F

from .pagination import BlogPagination
# register API View
class RegisterAPIView(APIResponseMixin, APIView):

    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return self.error_response(
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user, profile = serializer.save()

        # 🔐 Generate JWT Tokens
        refresh = RefreshToken.for_user(user)

        response_data = {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "unique_id": user.unique_id, 
            },
            "profile": {
                "id": profile.id
            }
        }

        return self.success_response(
            message="Registration successful",
            data=response_data,
            status_code=status.HTTP_201_CREATED
        )
    
# Personal details API
class PersonalLifestyleAPIView(APIResponseMixin, APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create or Update Personal Lifestyle
        """

        try:
            profile = request.user.profile
        except:
            return self.error_response(
                "Matrimony profile not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = PersonalLifestyleSerializer(
            data=request.data,
            context={"profile": profile}
        )

        if not serializer.is_valid():
            return self.error_response(
                serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        lifestyle = serializer.save()

        return self.success_response(
            message="Personal lifestyle details saved successfully",
            data={
                "lifestyle_id": lifestyle.id
            },
            status_code=status.HTTP_201_CREATED
        )
    
class LifestyleMasterDataAPIView(APIView, APIResponseMixin):
    permission_classes = [AllowAny]   # Public API (used during registration)

    def get(self, request):
        try:
            data = {
                "music_genres": MusicGenreSerializer(
                    MusicGenre.objects.all(), many=True
                ).data,
            
                "music_activities": MusicActivitySerializer(
                    MusicActivity.objects.all(), many=True
                ).data,
            
                "reading_preferences": ReadingPreferenceSerializer(
                    ReadingPreference.objects.all(), many=True
                ).data,
            
                "movie_tv_genres": MovieGenreSerializer(
                    MovieGenre.objects.all(), many=True
                ).data,
            }


            return self.success_response(
                message="Lifestyle master data fetched successfully",
                data=data
            )

        except Exception as e:
            return self.error_response(str(e))
        
# subscription plans API
class SubscriptionPlanListAPI(APIView, APIResponseMixin):

    def get(self, request):
        try:
            plans = SubscriptionPlan.objects.filter(is_active=True)

            serializer = SubscriptionPlanSerializer(plans, many=True)

            return self.success_response(
                message="Subscription plans fetched successfully",
                data=serializer.data,
                status_code=drf_status.HTTP_200_OK
            )

        except Exception as e:
            return self.error_response(
                errors=str(e),
                status_code=drf_status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class UserMultipleImageUploadAPI(APIResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MultipleImageUploadSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        images = serializer.validated_data["images"]

        try:
            with transaction.atomic():
                image_objs = [
                    UserImage(user=request.user, image=image)
                    for image in images
                ]
                UserImage.objects.bulk_create(image_objs)

            return self.success_response(
                message="Images uploaded successfully",
                data={
                    "uploaded_count": len(images)
                }
            )

        except Exception as e:
            return self.error_response(str(e))
        

class ReligionListAPIView(APIResponseMixin, APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        religions = Caste.objects.filter(
            level="religion",
            is_active=True
        ).order_by("name")

        serializer = ReligionSerializer(religions, many=True)

        return self.success_response(
            message="Religions fetched successfully",
            data=serializer.data
        )
    

class CasteListByReligionAPIView(APIResponseMixin, APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        religion_id = request.query_params.get("religion_id")

        if not religion_id:
            return self.error_response(
                errors="religion_id is required"
            )

        castes = Caste.objects.filter(
            level="caste",
            parent_id=religion_id,
            is_active=True
        ).order_by("name")

        serializer = CasteSerializer(castes, many=True)

        return self.success_response(
            message="Castes fetched successfully",
            data=serializer.data
        )


# login API
class LoginAPIView(APIResponseMixin, APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request, email=email, password=password)

        if not user:
            return self.error_response(
                errors="Invalid email or password",
                status_code=drf_status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return self.error_response(
                errors="Account is disabled. Please contact support.",
                status_code=drf_status.HTTP_403_FORBIDDEN
            )

        # 🔐 Generate JWT Tokens
        refresh = RefreshToken.for_user(user)

        data = {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "phone_number": user.phone_number,
                "role": user.role,
                "is_email_verified": user.is_email_verified,
                "profile_image": (
                    request.build_absolute_uri(user.profile_image.url)
                    if user.profile_image else None
                )
            }
        }

        return self.success_response(
            message="Login successful",
            data=data,
            status_code=drf_status.HTTP_200_OK
        )
    

class CreateSubscriptionOrderAPIView(APIView, APIResponseMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        subscription_id = request.data.get("subscription_id")

        try:
            plan = SubscriptionPlan.objects.get(
                id=subscription_id,
                is_active=True
            )
        except SubscriptionPlan.DoesNotExist:
            return self.error_response("Invalid subscription plan")

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        razorpay_order = client.order.create({
            "amount": int(plan.price * 100),  # paise
            "currency": "INR",
            "payment_capture": 1
        })

        payment = SubscriptionPayment.objects.create(
            user=request.user,
            subscription=plan,
            amount=plan.price,
            payment_method="razorpay",
            transaction_id=razorpay_order["id"],
            payment_status="pending"
        )

        return self.success_response(
            message="Order created successfully",
            data={
                "payment_id": payment.id,
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "amount": plan.price,
                "currency": "INR",
                "plan_name": plan.plan_name
            }
        )
    

class VerifySubscriptionPaymentAPIView(APIView, APIResponseMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        try:
            payment = SubscriptionPayment.objects.get(
                transaction_id=razorpay_order_id,
                user=request.user
            )
        except SubscriptionPayment.DoesNotExist:
            return self.error_response("Payment record not found")

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            })
        except razorpay.errors.SignatureVerificationError:
            payment.payment_status = "failed"
            payment.save()
            return self.error_response("Payment verification failed")

        payment.payment_status = "success"
        payment.paid_at = timezone.now()
        payment.save()

        return self.success_response(
            message="Payment verified successfully",
            data={
                "payment_id": payment.id,
                "status": payment.payment_status,
                "paid_at": payment.paid_at
            }
        )

# user profile API
class MatrimonyProfileAPIView(APIView, APIResponseMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = MatrimonyProfile.objects.filter(user=request.user).first()

        if not profile:
            return self.error_response(
                "Profile not found",
                status.HTTP_404_NOT_FOUND
            )

        serializer = MatrimonyProfileSerializer(profile, context={"request": request})
        return self.success_response(
            message="Profile fetched successfully",
            data=serializer.data
        )

    def patch(self, request):
        profile = MatrimonyProfile.objects.filter(user=request.user).first()

        if not profile:
            return self.error_response(
                "Profile not found. Create profile first.",
                status.HTTP_404_NOT_FOUND
            )

        serializer = MatrimonyProfileSerializer(
            instance=profile,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                message="Profile updated successfully",
                data=serializer.data
            )

        return self.error_response(serializer.errors)


class UserImageListAPIView(APIResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            images = UserImage.objects.filter(
                user=request.user
            ).order_by("-uploaded_at")

            serializer = UserImageSerializer(
                images,
                many=True,
                context={"request": request}
            )

            return self.success_response(
                message="User images fetched successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return self.error_response(
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
# remove image
class UserImageDeleteAPIView(APIResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, image_id):
        try:
            image = get_object_or_404(
                UserImage,
                id=image_id,
                user=request.user  # 🔐 ownership check
            )

            image.delete()

            return self.success_response(
                message="Image deleted successfully",
                data=[],
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return self.error_response(
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )


# blog list API
class BlogListAPIView(APIView, APIResponseMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        blogs = Blog.objects.filter(status="published")

        # Optional featured filter
        if request.GET.get("featured") == "true":
            blogs = blogs.filter(is_featured=True)

        paginator = BlogPagination()
        paginated_blogs = paginator.paginate_queryset(blogs, request)

        serializer = BlogListSerializer(
            paginated_blogs,
            many=True,
            context={"request": request}
        )

        return self.success_response(
            message="Blogs fetched successfully",
            data={
                "count": blogs.count(),
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data
            }
        )
    
class BlogDetailAPIView(APIView, APIResponseMixin):
    permission_classes = [AllowAny]

    def get(self, request, blog_id):
        try:
            blog = Blog.objects.get(id=blog_id, status="published")
        except Blog.DoesNotExist:
            return self.error_response(
                "Blog not found",
                status_code=drf_status.HTTP_404_NOT_FOUND
            )

        # 🔥 Increment views count safely
        Blog.objects.filter(id=blog.id).update(
            views_count=F("views_count") + 1
        )
        blog.refresh_from_db()

        serializer = BlogDetailSerializer(
            blog,
            context={"request": request}
        )

        return self.success_response(
            message="Blog fetched successfully",
            data=serializer.data
        )