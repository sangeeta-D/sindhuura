from django.http import JsonResponse
from django.urls import resolve


class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated and not active
        if request.user.is_authenticated and not request.user.is_active:
            # Allow admin login/logout and admin pages
            try:
                resolver_match = resolve(request.path)
                if not (resolver_match.url_name in ['admin_login', 'logout'] or 
                        request.path.startswith('/admin/') or
                        request.path.startswith('/static/') or
                        request.path.startswith('/media/')):
                    # For API requests, return JSON error
                    if request.path.startswith('/api/') or request.META.get('HTTP_ACCEPT', '').startswith('application/json'):
                        return JsonResponse({
                            'status': False,
                            'message': 'Your account has been deactivated. Please contact support.',
                            'response': []
                        }, status=403)
                    else:
                        # For web pages, redirect to login or show message
                        from django.shortcuts import redirect
                        from django.contrib import messages
                        messages.error(request, 'Your account has been deactivated.')
                        from django.contrib.auth import logout
                        logout(request)
                        return redirect('admin_login')
            except:
                pass

        response = self.get_response(request)
        return response