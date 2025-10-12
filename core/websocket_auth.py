"""
Reusable WebSocket Authentication Middleware for Django Channels

This middleware provides JWT + Session authentication for ALL WebSocket connections
across the entire application (notifications, messaging, communities, etc.).

Features:
- JWT token validation using JWTAuthService for consistent validation
- Automatic JWT renewal using TokenRenewalService when expired
- Session validation as master controller
- ONE JWT TOKEN per session across HTTP and WebSocket
- Graceful failure and logout on session expiration
"""

from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from core.jwt_auth import jwt_auth_service
from core.token_renewal import token_renewal_service
from core.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class UniversalWebSocketAuthMiddleware(BaseMiddleware):
    """
    Universal WebSocket authentication middleware for all WebSocket connections.

    Supports all WebSocket apps: notifications, messaging, communities, etc.

    Authentication Flow:
    1. Requires both JWT token and session ID in query params
    2. Try JWT token validation first (primary authentication)
    3. If JWT is valid → authenticate user
    4. If JWT is expired/invalid → validate session for renewal only
    5. If session is valid → renew JWT and authenticate
    6. If session is also invalid → disconnect

    Query Parameters:
    ws://localhost:8000/ws/app/?token=jwt_token&session_id=session_id
    """

    def __init__(self, inner):
        super().__init__(inner)
        self.session_manager = SessionManager()

    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent usage of timed out connections
        close_old_connections()

        # Only authenticate WebSocket connections, pass HTTP through immediately
        if scope['type'] != 'websocket':
            # For HTTP requests, don't add any async overhead
            result = await super().__call__(scope, receive, send)
            # Ensure connections are closed after HTTP request
            close_old_connections()
            return result

        # Extract authentication parameters from query string
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        jwt_token = query_params.get('token', [None])[0]
        session_id = query_params.get('session_id', [None])[0]

        # Get WebSocket path for logging context
        path = scope.get('path', 'unknown')
        logger.debug(f"WebSocket auth [{path}] - JWT: {bool(jwt_token)}, Session: {bool(session_id)}")

        # Both JWT token and session ID are required
        if not jwt_token or not session_id:
            scope['user'] = AnonymousUser()
            scope['auth_error'] = 'missing_credentials'
            logger.warning(f"WebSocket [{path}] missing credentials - JWT: {bool(jwt_token)}, Session: {bool(session_id)}")
            return await super().__call__(scope, receive, send)

        # Attempt authentication with automatic JWT renewal
        auth_result = await self.authenticate_websocket(jwt_token, session_id)

        if auth_result['success']:
            scope['user'] = auth_result['user']
            scope['session_data'] = auth_result.get('session_data')

            # If token was renewed, provide new token info for client
            if auth_result.get('token_renewed'):
                scope['new_jwt_token'] = auth_result['new_jwt_token']
                scope['token_renewed'] = True
                logger.info(f"WebSocket [{path}] authenticated with token renewal: {auth_result['user'].username}")
            else:
                logger.info(f"WebSocket [{path}] authenticated: {auth_result['user'].username}")
        else:
            scope['user'] = AnonymousUser()
            scope['auth_error'] = auth_result['error']
            logger.warning(f"WebSocket [{path}] authentication failed: {auth_result['error']}")

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def authenticate_websocket(self, jwt_token, session_id):
        """
        Authenticate WebSocket connection using JWT + Session validation.

        Returns:
            dict: {
                'success': bool,
                'user': User instance or None,
                'token': str (new token if renewed),
                'error': str or None
            }

        Flow:
        1. Try JWT token validation first (primary authentication)
        2. If JWT is valid → authenticate user
        3. If JWT is expired/invalid → validate session for renewal purpose only
        """

        try:
            # Step 1: Try JWT token validation first (primary authentication)
            user = jwt_auth_service.validate_token_and_get_user(jwt_token)

            if user:
                # JWT is valid - user authenticated successfully! ✅
                logger.debug(f"WebSocket JWT authentication successful: {user.username}")
                return {
                    'success': True,
                    'user': user,
                    'token': jwt_token,  # Use existing token
                    'error': None
                }

            # Step 2: JWT is invalid/expired, now check session for renewal purpose
            logger.debug("JWT token invalid/expired, checking session for renewal")

            # Use TokenRenewalService for consistent renewal logic
            renewal_result = token_renewal_service.renew_jwt_token(jwt_token, session_id)

            if renewal_result['success']:
                # Renewal successful
                logger.info(f"🔄 WebSocket JWT renewed for user: {renewal_result['user'].username}")
                return {
                    'success': True,
                    'user': renewal_result['user'],
                    'token': renewal_result['access_token'],  # Return new token
                    'error': None,
                    'renewed': True
                }
            else:
                # Both JWT and session are invalid
                error = renewal_result.get('error', 'Authentication failed')
                logger.debug(f"WebSocket authentication failed: {error}")
                return {
                    'success': False,
                    'user': None,
                    'token': None,
                    'error': error
                }

        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            return {
                'success': False,
                'user': None,
                'token': None,
                'error': f'Authentication error: {str(e)}'
            }

    def validate_session(self, session_id):
        """
        Validate if session is still active for WebSocket connection.
        Uses TokenRenewalService's session validation logic.
        """
        return token_renewal_service.validate_session(session_id)


def UniversalWebSocketAuthMiddlewareStack(inner):
    """
    Universal WebSocket authentication middleware stack.

    Use this for ALL WebSocket applications:
    - Notifications: /ws/notifications/
    - Messaging: /ws/messaging/
    - Communities: /ws/communities/
    - Any other WebSocket app

    Provides consistent JWT + Session authentication with automatic renewal.
    """
    return UniversalWebSocketAuthMiddleware(inner)


# Alias for backward compatibility
JWTSessionWebSocketMiddlewareStack = UniversalWebSocketAuthMiddlewareStack
