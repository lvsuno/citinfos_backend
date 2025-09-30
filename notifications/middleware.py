"""
WebSocket JWT Authentication Middleware.

This module provides JWT authentication for Django Channels WebSocket connections.
Uses JWTAuthService and TokenRenewalService for consistent token management.
"""

import logging
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from core.jwt_auth import jwt_auth_service
from core.token_renewal import token_renewal_service
from core.session_manager import SessionManager

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT Authentication middleware for Django Channels WebSockets.

    Uses JWTAuthService and TokenRenewalService for consistent authentication
    logic across HTTP requests and WebSocket connections.
    """

    def __init__(self, inner):
        self.inner = inner
        self.session_manager = SessionManager()

    async def __call__(self, scope, receive, send):
        # Extract token and session_id from query parameters
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        session_id = query_params.get('session_id', [None])[0]

        # Authenticate user if token is provided
        if token:
            try:
                # Use JWTAuthService for consistent validation
                user = await self.authenticate_user(token, session_id)
                scope['user'] = user

                if user and not isinstance(user, AnonymousUser):
                    logger.info(f"WebSocket authenticated user: {user.username}")
                else:
                    logger.warning("WebSocket authentication failed: invalid user")
                    scope['user'] = AnonymousUser()

            except Exception as e:
                logger.error(f"WebSocket authentication error: {e}")
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def authenticate_user(self, token, session_id=None):
        """
        Authenticate user using JWTAuthService and TokenRenewalService.
        """
        try:
            # First, try JWT validation
            user = jwt_auth_service.validate_token_and_get_user(token)
            if user:
                return user

            # If JWT is invalid/expired, try renewal if session_id is provided
            if session_id:
                renewal_result = token_renewal_service.renew_jwt_token(token, session_id)
                if renewal_result['success']:
                    return renewal_result['user']

            # Authentication failed
            return AnonymousUser()

        except Exception as e:
            logger.error(f"User authentication error: {e}")
            return AnonymousUser()


def JWTAuthMiddlewareStack(inner):
    """
    JWT Authentication middleware stack for WebSocket connections.

    This provides the same authentication logic as HTTP requests
    to ensure consistent user authentication across the application.
    """
    return JWTAuthMiddleware(inner)
