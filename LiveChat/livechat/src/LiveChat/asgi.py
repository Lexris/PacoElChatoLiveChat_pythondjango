import os

import django
from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import personal.routing as router

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LiveChat.settings')
django.setup()

application = ProtocolTypeRouter({
    "http": AsgiHandler(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            router.websocket_urlpatterns
        )
    ),
})
