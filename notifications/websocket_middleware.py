"""
WebSocket JWT Authentication Middleware for Django Channels

This middleware handles JWT + Session authentication for WebSocket connections.
Both session ID and JWT token are required for authentication.
If JWT expires but session is valid, it automatically renews the token.

ONE JWT TOKEN PER SESSION - can be renewed by either HTTP or WebSocket.
"""

from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from core.jwt_auth import jwt_auth_service
from core.token_renewal import token_renewal_service
import logging

logger = logging.getLogger(__name__)

class JWTSessionWebSocketMiddleware(BaseMiddleware):
    """
    WebSocket authentication middleware that requires both JWT token and session ID.

    If JWT is expired but session is valid, it automatically renews the JWT token
    using the same renewal mechanism as the main middleware.

    Expected query parameters:
    ws://localhost:8000/ws/notifications/?token=jwt_token&session_id=session_id
    """

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent usage of timed out connections
        close_old_connections()

        # Only authenticate WebSocket connections
        if scope['type'] != 'websocket':
            return await super().__call__(scope, receive, send)

        # Get both JWT token and session ID from query string
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        jwt_token = query_params.get('token', [None])[0]
        session_id = query_params.get('session_id', [None])[0]

        logger.debug(f"WebSocket auth - JWT: {bool(jwt_token)}, Session: {bool(session_id)}")

        # Both JWT token and session ID are required
        if not jwt_token or not session_id:
            scope['user'] = AnonymousUser()
            logger.warning("WebSocket connection missing JWT token or session ID")
            return await super().__call__(scope, receive, send)

        # Attempt authentication with token renewal if needed
        auth_result = await self.authenticate_with_renewal(jwt_token, session_id)

        if auth_result['success']:
            scope['user'] = auth_result['user']
            # Store renewed token info in scope for potential use
            if auth_result.get('new_token'):
                scope['renewed_token'] = auth_result['new_token']
            logger.info(f"WebSocket authenticated: {auth_result['user'].username}")
        else:
            scope['user'] = AnonymousUser()
            logger.warning(f"WebSocket authentication failed: {auth_result['error']}")

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def authenticate_with_renewal(self, jwt_token, session_id):
        """
        Authenticate with JWT token and session ID, with automatic renewal.

        Process:
        1. Try to validate JWT token
        2. If JWT is valid, authenticate user
        3. If JWT is expired but session is valid, renew token
        4. If both fail, return authentication failure
        """
        # First, try to validate the current JWT token
        user = jwt_auth_service.validate_token_and_get_user(jwt_token)

        if user:
            # JWT token is valid, verify session is also valid
            if token_renewal_service.validate_session(session_id):

                return {'success': True, 'user': user}
            else:
                logger.warning("JWT valid but session expired")
                return {'success': False, 'error': 'Session expired'}

        # JWT token is invalid/expired, check if we can renew it

        renewal_result = token_renewal_service.renew_jwt_token(jwt_token, session_id)

        if renewal_result['success']:
            logger.info(f"JWT token renewed for WebSocket: {renewal_result['user'].username}")
            return {
                'success': True,
                'user': renewal_result['user'],
                'new_token': renewal_result['access_token'],
                'session_id': renewal_result['session_id']
            }
        else:
            logger.warning(f"JWT renewal failed: {renewal_result['error']}")
            return {'success': False, 'error': renewal_result['error']}

def JWTSessionWebSocketMiddlewareStack(inner):
    """
    Middleware stack for JWT + Session WebSocket authentication.

    Requires both JWT token and session ID for authentication.
    Automatically renews JWT tokens when expired but session is valid.

    Maintains ONE JWT TOKEN per session across HTTP and WebSocket.
    """
    return JWTSessionWebSocketMiddleware(inner)

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
        scope['user'] = AnonymousUser()

        # Authenticate using shared hybrid authentication service
        if jwt_token or session_id:
            auth_result = await self.authenticate_websocket(session_id, jwt_token)
            if auth_result and auth_result.get('success'):
                user = auth_result.get('user')
                if user:
                    scope['user'] = user
                    scope['session_data'] = auth_result.get('session_data')
                    logger.info(f"WebSocket authenticated user: {user.username}")
                else:
                    logger.warning("WebSocket authentication failed: no user")
            else:
                error = auth_result.get('error', 'Unknown error') if auth_result else 'No auth result'
                logger.warning(f"WebSocket authentication failed: {error}")
        else:

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def authenticate_websocket(self, session_id, jwt_token):
        """
        Authenticate WebSocket using shared hybrid authentication service.

        This ensures WebSocket authentication follows the exact same flows
        as HTTP requests in your main middleware.
        """
        try:
            # Use the shared hybrid authentication service
            # This implements the same 3 flows as your main middleware
            auth_result = hybrid_auth_service.authenticate_hybrid(
                session_id=session_id,
                jwt_token=jwt_token
            )

            if auth_result['success']:
                logger.info(f"WebSocket hybrid auth successful for user: {auth_result['user'].username}")
            else:
                logger.warning(f"WebSocket hybrid auth failed: {auth_result.get('error')}")

            return auth_result

        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            return {'success': False, 'error': str(e)}

def HybridAuthWebSocketMiddlewareStack(inner):
    """
    Middleware stack for hybrid WebSocket authentication.

    Use this in your ASGI routing to ensure WebSocket authentication
    follows the same logic as HTTP authentication.
    """
    return HybridAuthWebSocketMiddleware(inner)
