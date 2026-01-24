import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sindhuura.settings")

from django.core.asgi import get_asgi_application

# ✅ FIRST: fully initialize Django
django_asgi_app = get_asgi_application()

# ✅ ONLY AFTER Django is ready
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from chat.middleware import JWTAuthMiddleware
import chat.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(chat.routing.websocket_urlpatterns)
        )
    ),
})
