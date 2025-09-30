"""
ASGI config for citinfos_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django.setup()

django_asgi_app = get_asgi_application()

# Import WebSocket routing and universal authentication middleware after Django setup
from core.websocket_registry import get_websocket_urlpatterns
from core.websocket_auth import UniversalWebSocketAuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        UniversalWebSocketAuthMiddlewareStack(
            URLRouter(
                get_websocket_urlpatterns()
            )
        )
    ),
})
