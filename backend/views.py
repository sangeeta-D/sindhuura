from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from auth_api.models import CustomUser as User, SubscriptionPayment
from match.models import StoryBanner, MatchRequest, SuccessStory
from .models import *
from django.shortcuts import get_object_or_404
from auth_api.models import CustomUser
from django.contrib.auth.hashers import make_password
from django.db.models import Exists, OuterRef, Count, Sum
from django.core.mail import EmailMessage
from django.conf import settings
from match.models import SuccessStory
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt  # Only if you don't use csrf token in JS
from django.contrib.admin.views.decorators import staff_member_required
import json

def index(request):
    return render(request,'index.html')

def admin_login(request):
    # Already logged-in admin / sub-admin
    if request.user.is_authenticated and request.user.is_staff:
        if request.user.role == "admin":
            return redirect("admin_dashboard")
        elif request.user.role == "sub_admin":
            return redirect("sub_admin_dashboard")

    if request.method == "POST":
        email = request.POST.get("email_username")
        password = request.POST.get("password")
        remember_me = request.POST.get("remember_me")

        # 🔐 Authenticate using EMAIL
        user = authenticate(request, email=email, password=password)

        if user is not None:
            # Only staff users can access admin panel
            if user.is_staff:
                login(request, user)

                # Remember Me
                if remember_me:
                    request.session.set_expiry(60 * 60 * 24 * 14)  # 14 days
                else:
                    request.session.set_expiry(0)  # browser close

                # ✅ ROLE-BASED REDIRECT
                if user.role == "admin":
                    return redirect("admin_dashboard")
                elif user.role == "sub_admin":
                    return redirect("sub_admin_dashboard")
                else:
                    messages.error(request, "Invalid role access.")
                    logout(request)

            else:
                messages.error(request, "You are not authorized to access the admin panel.")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "admin_login.html")

def admin_dashboard(request):
    # if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
    #     return redirect('admin_login')

    # Statistics
    total_users = CustomUser.objects.filter(is_staff=False).count()
    verified_users = CustomUser.objects.filter(is_staff=False, is_verified=True).count()
    premium_users = SubscriptionPayment.objects.filter(payment_status='success').values('user').distinct().count()
    total_matches = MatchRequest.objects.count()
    accepted_matches = MatchRequest.objects.filter(status='accepted').count()
    success_stories = SuccessStory.objects.count()
    blogs = Blog.objects.count()
    events = Event.objects.count()
    total_revenue = SubscriptionPayment.objects.filter(payment_status='success').aggregate(total=Sum('amount'))['total'] or 0

    # Recent activities (last 10)
    recent_users = CustomUser.objects.filter(is_staff=False).order_by('-date_joined')[:5]
    recent_matches = MatchRequest.objects.select_related('from_user', 'to_user').order_by('-created_at')[:5]
    recent_payments = SubscriptionPayment.objects.select_related('user').filter(payment_status='success').order_by('-paid_at')[:5]

    context = {
        'total_users': total_users,
        'verified_users': verified_users,
        'premium_users': premium_users,
        'total_matches': total_matches,
        'accepted_matches': accepted_matches,
        'success_stories': success_stories,
        'blogs': blogs,
        'events': events,
        'total_revenue': total_revenue,
        'recent_users': recent_users,
        'recent_matches': recent_matches,
        'recent_payments': recent_payments,
    }

    return render(request, 'admin_dashboard.html', context)

def sub_admin_dashboard(request):
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_login')
    return render(request, 'sub_admin_dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('admin_login')

def castes(request):
    if request.method == "POST":
        name = request.POST.get("name")
        parent_id = request.POST.get("parent")

        parent = Caste.objects.get(id=parent_id) if parent_id else None
        level = 'caste' if parent else 'religion'

        Caste.objects.create(
            name=name,
            parent=parent,
            level=level
        )

        messages.success(request, "Saved successfully")
        return redirect('castes')

    religions = Caste.objects.filter(level='religion')

    return render(request, 'castes.html', {
        'religions': religions
    })


def edit_caste(request, pk):
    caste = get_object_or_404(Caste, pk=pk)

    if request.method == "POST":
        caste.name = request.POST.get("name")
        parent_id = request.POST.get("parent")
        caste.parent = Caste.objects.get(id=parent_id) if parent_id else None
        caste.level = 'caste' if caste.parent else 'religion'
        caste.save()

        messages.success(request, "Updated successfully")
        return redirect('castes')

    religions = Caste.objects.filter(level='religion')
    return render(request, 'edit_caste_modal.html', {
        'caste': caste,
        'religions': religions
    })

def delete_caste(request, pk):
    caste = get_object_or_404(Caste, pk=pk)

    # Prevent deleting religion if castes exist
    if caste.level == 'religion' and caste.castes.exists():
        messages.error(request, "Cannot delete religion with castes")
        return redirect('castes')

    caste.delete()
    messages.success(request, "Deleted successfully")
    return redirect('castes')

def lifestyle_master(request):
    # Map of model types
    model_map = {
        "music_genre": MusicGenre,
        "music_activity": MusicActivity,
        "reading_preference": ReadingPreference,
        "movie_genre": MovieGenre,
        "story_banner": StoryBanner,  # Added banner
    }

    if request.method == "POST":
        action = request.POST.get("action")
        model_type = request.POST.get("model_type")
        name = request.POST.get("name")
        obj_id = request.POST.get("object_id")

        model_class = model_map.get(model_type)

        if not model_class:
            messages.error(request, "Invalid type")
            return redirect("lifestyle_master")

        # ➕ ADD
        if action == "add":
            if model_type == "story_banner":
                image = request.FILES.get("image")
                if not image:
                    messages.error(request, "Image is required")
                else:
                    model_class.objects.create(image=image)
                    messages.success(request, "Banner added successfully")
            else:
                if not name:
                    messages.error(request, "Name is required")
                else:
                    model_class.objects.create(name=name)
                    messages.success(request, "Added successfully")

        # ✏️ EDIT
        elif action == "edit":
            obj = get_object_or_404(model_class, id=obj_id)
            if model_type == "story_banner":
                image = request.FILES.get("image")
                if not image:
                    messages.error(request, "Image is required")
                else:
                    obj.image = image
                    obj.save()
                    messages.success(request, "Banner updated successfully")
            else:
                obj.name = name
                obj.save()
                messages.success(request, "Updated successfully")

        # 🗑 DELETE
        elif action == "delete":
            obj = get_object_or_404(model_class, id=obj_id)
            obj.delete()
            if model_type == "story_banner":
                messages.success(request, "Banner deleted successfully")
            else:
                messages.success(request, "Deleted successfully")

        return redirect("lifestyle_master")

    # ➡ Context for rendering
    context = {
        "music_genres": MusicGenre.objects.all(),
        "music_activities": MusicActivity.objects.all(),
        "reading_preferences": ReadingPreference.objects.all(),
        "movie_genres": MovieGenre.objects.all(),
        "story_banners": StoryBanner.objects.all(),  # Added banners
    }

    return render(request, "lifestyle_master.html", context)

def subscription_plans(request):

    if request.method == "POST":
        action = request.POST.get("action")

        # ADD / EDIT
        if action in ["add", "edit"]:
            plan_id = request.POST.get("plan_id")

            plan_name = request.POST.get("plan_name")
            price = request.POST.get("price")
            validity = request.POST.get("validity")
            description = request.POST.get("description")
            is_active = request.POST.get("is_active") == "on"

            if action == "add":
                SubscriptionPlan.objects.create(
                    plan_name=plan_name,
                    price=price,
                    validity=validity,
                    description=description,
                    is_active=is_active
                )
                messages.success(request, "Subscription plan added successfully")

            else:
                plan = get_object_or_404(SubscriptionPlan, id=plan_id)
                plan.plan_name = plan_name
                plan.price = price
                plan.validity = validity
                plan.description = description
                plan.is_active = is_active
                plan.save()

                messages.success(request, "Subscription plan updated successfully")

            return redirect("subscription_plans")

        # DELETE
        if action == "delete":
            plan_id = request.POST.get("plan_id")
            plan = get_object_or_404(SubscriptionPlan, id=plan_id)
            plan.delete()
            messages.success(request, "Subscription plan deleted")
            return redirect("subscription_plans")

    plans = SubscriptionPlan.objects.all()

    return render(request, "subscription_plans.html", {
        "plans": plans
    })

def registered_user_list(request):
    users = User.objects.filter(is_staff=False).order_by("-date_joined")
    return render(request, "registered_user_list.html", {
        "users": users
    })


def user_list(request):
    users = CustomUser.objects.filter(is_staff=False).select_related("profile").annotate(is_premium=Exists(SubscriptionPayment.objects.filter(user=OuterRef('pk'), payment_status='success')))

    # Filters
    gender = request.GET.get('gender')
    city = request.GET.get('city')
    state = request.GET.get('state')
    is_premium = request.GET.get('is_premium')

    if gender:
        users = users.filter(profile__gender=gender)
    if city:
        users = users.filter(profile__city__icontains=city)
    if state:
        users = users.filter(profile__state__icontains=state)
    if is_premium:
        users = users.filter(is_premium=bool(int(is_premium)))

    users = users.order_by("-date_joined")

    return render(request, "user_list.html", {
        "users": users
    })

def user_details(request, user_id):
    user = (
        CustomUser.objects
        .select_related("profile", "profile__lifestyle")
        .prefetch_related("user_images")
        .get(id=user_id)
    )
    return render(request, "user_details.html", {"user": user})

  # Only admins can toggle
@require_POST
def toggle_user_verified(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return JsonResponse({
            "status": False,
            "message": "User not found",
            "response": []
        }, status=404)

    try:
        data = json.loads(request.body)
        is_verified = data.get("is_verified", None)
        if is_verified is None:
            return JsonResponse({
                "status": False,
                "message": "Missing 'is_verified' field",
                "response": []
            }, status=400)

        user.is_verified = bool(is_verified)
        user.save()

        return JsonResponse({
            "status": True,
            "message": f"User verification status updated to {user.is_verified}",
            "response": {"is_verified": user.is_verified}
        })

    except Exception as e:
        return JsonResponse({
            "status": False,
            "message": str(e),
            "response": []
        }, status=500)


def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect("user_list")


def sub_admin(request):
    sub_admins = CustomUser.objects.filter(role="sub_admin")

    sidebar_menus = SidebarMenu.objects.filter(is_active=True)

    for admin in sub_admins:
        admin.assigned_menu_ids = list(
            admin.menu_permissions.values_list("menu_id", flat=True)
        )

    return render(request, "sub_admin.html", {
        "sub_admins": sub_admins,
        "sidebar_menus": sidebar_menus
    })



def create_sub_admin(request):
    if request.method == "POST":

        email = request.POST.get("email")
        name = request.POST.get("name")
        password = request.POST.get("password")
        address = request.POST.get("address")

        profile_image = request.FILES.get("profile_image")
        aadhaar_card = request.FILES.get("aadhaar_card")

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("sub_admin")

        CustomUser.objects.create(
            email=email,
            name=name,
            role="sub_admin",
            address=address,
            profile_image=profile_image,
            aadhaar_card=aadhaar_card,
            is_staff=True,
            is_active=True,
            password=make_password(password),
        )

        messages.success(request, "Sub Admin created successfully")
        return redirect("sub_admin")
    

def assign_sub_admin_menu(request, sub_admin_id):
    sub_admin = get_object_or_404(CustomUser, id=sub_admin_id, role="sub_admin")

    if request.method == "POST":
        menu_ids = request.POST.getlist("menus")

        # Remove old permissions
        SubAdminMenuPermission.objects.filter(sub_admin=sub_admin).delete()

        # Add new permissions
        permissions = [
            SubAdminMenuPermission(sub_admin=sub_admin, menu_id=menu_id)
            for menu_id in menu_ids
        ]
        SubAdminMenuPermission.objects.bulk_create(permissions)

        messages.success(request, "Menu permissions updated successfully")

    return redirect("sub_admin")


def delete_sub_admin(request, id):
    admin = get_object_or_404(CustomUser, id=id, role="sub_admin")
    admin.delete()
    messages.success(request, "Sub Admin deleted successfully")
    return redirect("sub_admin")


def compose_mail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        attachments = request.FILES.getlist("attachments")

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )

        # 📎 Attach files
        for file in attachments:
            email.attach(file.name, file.read(), file.content_type)

        try:
            email.send()
            messages.success(request, "Email sent successfully!")
        except Exception as e:
            messages.error(request, f"Failed to send email: {str(e)}")

        return redirect("send_mail", user_id=user.id)

    return render(request, "compose_mail.html", {"user": user})


def blogs(request):
    if request.method == "POST":
        action = request.POST.get("action")
        
        # ADD / EDIT
        if action in ["add", "edit"]:
            blog_id = request.POST.get("blog_id")
            title = request.POST.get("title")
            short_description = request.POST.get("short_description")
            content = request.POST.get("content")
            status = request.POST.get("status")
            is_featured = request.POST.get("is_featured") == "on"
            cover_media = request.FILES.get("cover_media")
            cover_media_type = request.POST.get("cover_media_type")
            
            if action == "add":
                blog_data = {
                    "title": title,
                    "short_description": short_description,
                    "content": content,
                    "status": status,
                    "is_featured": is_featured
                }
                if cover_media and cover_media_type:
                    blog_data["cover_media"] = cover_media
                    blog_data["cover_media_type"] = cover_media_type
                
                Blog.objects.create(**blog_data)
                messages.success(request, "Blog created successfully")
            
            else:  # edit
                blog = get_object_or_404(Blog, id=blog_id)
                blog.title = title
                blog.short_description = short_description
                blog.content = content
                blog.status = status
                blog.is_featured = is_featured
                if cover_media and cover_media_type:
                    blog.cover_media = cover_media
                    blog.cover_media_type = cover_media_type
                blog.save()
                messages.success(request, "Blog updated successfully")
            
            return redirect("blogs")
        
        # DELETE
        if action == "delete":
            blog_id = request.POST.get("blog_id")
            blog = get_object_or_404(Blog, id=blog_id)
            blog.delete()
            messages.success(request, "Blog deleted successfully")
            return redirect("blogs")
    
    blogs = Blog.objects.all().order_by("-created_at")
    return render(request, "blogs.html", {
        "blogs": blogs
    })


def events(request):
    if request.method == "POST":
        action = request.POST.get("action")
        event_id = request.POST.get("event_id")
        event_name = request.POST.get("event_name")
        event_datetime = request.POST.get("event_datetime")
        venue = request.POST.get("venue")
        city = request.POST.get("city")
        description = request.POST.get("description")
        image = request.FILES.get("image")

        # ➕ ADD
        if action == "add":
            if not all([event_name, event_datetime, venue, city, image]):
                messages.error(request, "All fields including image are required!")
            else:
                Event.objects.create(
                    event_name=event_name,
                    event_datetime=event_datetime,
                    venue=venue,
                    city=city,
                    description=description,
                    image=image
                )
                messages.success(request, "Event added successfully!")

        # ✏️ EDIT
        elif action == "edit":
            obj = get_object_or_404(Event, id=event_id)
            obj.event_name = event_name
            obj.event_datetime = event_datetime
            obj.venue = venue
            obj.city = city
            obj.description = description
            if image:
                obj.image = image
            obj.save()
            messages.success(request, "Event updated successfully!")

        # 🗑 DELETE
        elif action == "delete":
            obj = get_object_or_404(Event, id=event_id)
            obj.delete()
            messages.success(request, "Event deleted successfully!")

        return redirect("events")

    context = {
        "events": Event.objects.all().order_by("-event_datetime")
    }
    return render(request, "events.html", context)


def success_story(request):
    stories = (
        SuccessStory.objects
        .select_related("created_by")
        .prefetch_related("images")
        .order_by("-created_at")
    )
    return render(request, 'success_story.html', {'stories': stories})


def chat_views(request):
    if request.method == "POST":
        action = request.POST.get("action")

        # ADD QUESTION
        if action == "add_question":
            PredefinedMessage.objects.create(
                text=request.POST.get("question"),
                order=request.POST.get("question_order")
            )
            messages.success(request, "Question added successfully")

        # EDIT QUESTION
        elif action == "edit_question":
            q = get_object_or_404(PredefinedMessage, id=request.POST.get("question_id"))
            q.text = request.POST.get("question")
            q.order = request.POST.get("question_order")
            q.save()
            messages.success(request, "Question updated successfully")

        # DELETE QUESTION
        elif action == "delete_question":
            get_object_or_404(
                PredefinedMessage,
                id=request.POST.get("question_id")
            ).delete()
            messages.success(request, "Question deleted successfully")

        # ADD ANSWER
        elif action == "add_answer":
            PredefinedAnswer.objects.create(
                message_id=request.POST.get("question_id"),
                text=request.POST.get("answer"),
                order=request.POST.get("answer_order")
            )
            messages.success(request, "Answer added successfully")

        # EDIT ANSWER
        elif action == "edit_answer":
            a = get_object_or_404(PredefinedAnswer, id=request.POST.get("answer_id"))
            a.text = request.POST.get("answer")
            a.order = request.POST.get("answer_order")
            a.save()
            messages.success(request, "Answer updated successfully")

        # DELETE ANSWER
        elif action == "delete_answer":
            get_object_or_404(
                PredefinedAnswer,
                id=request.POST.get("answer_id")
            ).delete()
            messages.success(request, "Answer deleted successfully")

        return redirect("chat")

    questions = PredefinedMessage.objects.prefetch_related("answers")
    return render(request, "chat.html", {"questions": questions})