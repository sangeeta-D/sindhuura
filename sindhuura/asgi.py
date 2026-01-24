import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sindhuura.settings")

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from chat.middleware import JWTAuthMiddleware
import chat.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": OriginValidator(
        JWTAuthMiddleware(
            URLRouter(chat.routing.websocket_urlpatterns)
        ),
        [
            "https://admin.sindhuura.com",
            "http://admin.sindhuura.com",
        ]
    ),
})
