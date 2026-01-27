import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sindhuura.settings")

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.middleware import JWTAuthMiddleware
import chat.routing

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})
