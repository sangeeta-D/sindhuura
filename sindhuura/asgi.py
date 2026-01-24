import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sindhuura.settings")

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
import chat.routing
from chat.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(chat.routing.websocket_urlpatterns)
        )
    ),
})
