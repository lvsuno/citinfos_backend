"""
WebSocket JWT Authentication Middleware for Django Channels

This middleware handles JWT authentication for WebSocket connections using
the SAME JWT token managed by the main middleware. No separate token
management - just validation of the single JWT token per session.

ONE JWT TOKEN PER SESSION - managed centrally by main middleware.
"""

from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from core.jwt_auth import jwt_auth_service
import logging

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT authentication middleware for WebSocket connections.

    Uses the same JWT token managed by the main middleware - no duplication,
    no separate token management, just simple validation of the single token.

    Expects JWT token to be passed as 'token' query parameter:
    ws://localhost:8000/ws/notifications/?token=your_jwt_token_here
    """

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent usage of timed out connections
        close_old_connections()

        # Only authenticate WebSocket connections
        if scope['type'] != 'websocket':
            return await super().__call__(scope, receive, send)

        # Get JWT token from query string
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        logger.debug(f"WebSocket JWT - token present: {bool(token)}")

        # Authenticate using the same JWT service as main middleware
        if token:
            user = await self.validate_jwt_token(token)
            if user:
                scope['user'] = user

            else:
                scope['user'] = AnonymousUser()

        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def validate_jwt_token(self, raw_token):
        """
        Validate JWT token using the same service as main middleware.

        This ensures the same token validation logic across HTTP and WebSocket.
        No session management, no hybrid logic - just simple JWT validation.
        """
        return jwt_auth_service.validate_token_and_get_user(raw_token)

def JWTAuthMiddlewareStack(inner):
    """
    Middleware stack for JWT WebSocket authentication.

    Uses the same JWT token validation as HTTP requests to ensure
    consistent authentication across the entire application.

    ONE JWT TOKEN per session - managed centrally by main middleware.
    """
    return JWTAuthMiddleware(inner)
