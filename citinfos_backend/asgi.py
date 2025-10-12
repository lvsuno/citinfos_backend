"""
ASGI config for citinfos_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from .asgi_lifespan import ASGILifespanHandler

# Get Django ASGI application for HTTP
django_asgi_app = get_asgi_application()

# Import WebSocket routing and authentication middleware after Django setup
from core.websocket_registry import get_websocket_urlpatterns
from core.websocket_auth import UniversalWebSocketAuthMiddlewareStack

# Create the protocol router
protocol_router = ProtocolTypeRouter({
    # Use Django's native ASGI application for HTTP requests
    # This avoids unnecessary async overhead for synchronous HTTP
    "http": django_asgi_app,

    # Use Channels routing for WebSocket connections only
    "websocket": AllowedHostsOriginValidator(
        UniversalWebSocketAuthMiddlewareStack(
            URLRouter(
                get_websocket_urlpatterns()
            )
        )
    ),
})

# Wrap with lifespan handler to properly manage connections
application = ASGILifespanHandler(protocol_router)
