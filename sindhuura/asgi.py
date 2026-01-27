import os
import django

# Set the settings module FIRST
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sindhuura.settings")

# Initialize Django BEFORE importing anything else
django.setup()

# Now import Django and Channels components
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.middleware import JWTAuthMiddleware
import chat.routing

# Get the Django ASGI application
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})