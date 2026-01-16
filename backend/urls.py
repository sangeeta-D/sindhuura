from django.urls import path
from .import views

urlpatterns = [
    path('',views.index,name='index'),
    path('admin-login/',views.admin_login,name='admin_login'),
    path('admin-dashboard/',views.admin_dashboard,name='admin_dashboard'),
    path('logout/',views.logout_view,name='logout'),
    path('castes/',views.castes,name='castes'),
    path('castes/<int:pk>/edit/', views.edit_caste, name='edit_caste'),
    path('castes/<int:pk>/delete/', views.delete_caste, name='delete_caste'),
    path("lifestyle-master/", views.lifestyle_master, name="lifestyle_master"),
    path("subscriptions/", views.subscription_plans, name="subscription_plans"),
    path("user-list/", views.user_list, name="user_list"),
    path("user_details/<int:user_id>/", views.user_details, name="user_details"),
    path("delete-user/<int:user_id>/", views.delete_user, name="delete_user"),      

    path("sub-admin/", views.sub_admin, name="sub_admin"),
    path("sub-admins/create/", views.create_sub_admin, name="create_sub_admin"),
    path("sub-admins/delete/<int:id>/", views.delete_sub_admin, name="delete_sub_admin"),
    path("sub-admins/assign-menu/<int:sub_admin_id>/", views.assign_sub_admin_menu, name="assign_sub_admin_menu"),

    path("sub-admin-dashboard/", views.sub_admin_dashboard, name="sub_admin_dashboard"),
    path("send-mail/<int:user_id>/", views.compose_mail, name="send_mail"),
    path("blogs/", views.blogs, name="blogs"),

]