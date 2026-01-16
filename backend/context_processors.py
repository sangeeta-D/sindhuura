from backend.models import SidebarMenu

def sidebar_menus(request):
    if not request.user.is_authenticated:
        return {"sidebar_menus": []}

    user = request.user

    if user.role == "admin":
        menus = SidebarMenu.objects.filter(is_active=True)

    elif user.role == "sub_admin":
        menus = SidebarMenu.objects.filter(
            subadminmenupermission__sub_admin=user,
            is_active=True
        )

    else:
        menus = SidebarMenu.objects.none()

    return {"sidebar_menus": menus}
