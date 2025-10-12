"""
Authentication Middleware with Automatic Session Recovery.

This middleware handles automatic session recovery for users who lost their JWT tokens
but still have an active session in Redis (identified by device fingerprint).

Flow:
1. Request arrives without Authorization header (no JWT)
2. Check if X-Device-Fingerprint header is present
3. Look up active session in Redis by fingerprint
4. If valid session found, generate new JWT tokens
5. Add tokens to response headers for client to pick up
6. Client stores tokens and uses them for future requests

This eliminates the need for a separate /recover-session/ endpoint.
"""

import logging
import redis
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User, AnonymousUser
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)


class AutoSessionRecoveryMiddleware(MiddlewareMixin):
    """
    Automatically recover user sessions using device fingerprint.

    This middleware runs AFTER JWT authentication middleware.
    If user is anonymous but has a fingerprint with an active session,
    it generates new JWT tokens and sends them in response headers.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=0,
                decode_responses=True,
                socket_timeout=2
            )
        except Exception as e:
            logger.error(f"Failed to initialize Redis for session recovery: {e}")
            self.redis_client = None

    def process_response(self, request, response):
        """
        Check for session recovery opportunity and add tokens to response if found.

        Only attempts recovery if:
        - User is anonymous (no JWT token)
        - Request has X-Device-Fingerprint header
        - Redis has active session for this fingerprint
        """
        if not self.redis_client:
            return response

        try:
            # Only attempt recovery for anonymous users
            user = getattr(request, 'user', None)
            if user and not isinstance(user, AnonymousUser):
                # User already authenticated, skip recovery
                return response

            # Check if request has fingerprint
            fingerprint = request.META.get('HTTP_X_DEVICE_FINGERPRINT')
            if not fingerprint:
                # No fingerprint, cannot recover session
                return response

            # Try to find active session by fingerprint
            session_data = self._find_session_by_fingerprint(fingerprint)
            if not session_data:
                # No active session found
                return response

            # Get user from session
            user_id = session_data.get('user_id')
            if not user_id:
                # Session is not authenticated
                return response

            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"Session recovery failed: User {user_id} not found")
                return response

            # Generate new JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Add tokens to response headers
            response['X-New-Access-Token'] = access_token
            response['X-New-Refresh-Token'] = refresh_token
            response['X-Session-Recovered'] = 'true'

            # Update session last_activity
            from django.utils import timezone
            session_key = session_data.get('session_key')
            if session_key:
                self.redis_client.hset(
                    session_key,
                    'last_activity',
                    str(timezone.now().timestamp())
                )
                self.redis_client.expire(session_key, 1800)  # 30 minutes

            logger.info(
                f"✅ Auto-recovered session for user {user.username} "
                f"via fingerprint {fingerprint[:16]}..."
            )

        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error during auto session recovery: {e}")
        except Exception as e:
            logger.error(f"Error during auto session recovery: {e}")

        return response

    def _find_session_by_fingerprint(self, fingerprint):
        """
        Find active session by device fingerprint.

        Returns session data dict if found, None otherwise.
        """
        try:
            # Try session ID from header first (if client sent it)
            session_id = request.META.get('HTTP_X_SESSION_ID') if hasattr(self, 'request') else None

            if session_id:
                session_key = f"session:{session_id}"
                session_data = self.redis_client.hgetall(session_key)

                # Validate fingerprint matches
                if session_data and session_data.get('device_fingerprint') == fingerprint:
                    session_data['session_key'] = session_key
                    return session_data

            # Try anonymous session that was converted
            anon_session_key = f"anon_session:{fingerprint}"
            anon_session_data = self.redis_client.hgetall(anon_session_key)

            if anon_session_data and anon_session_data.get('converted_to_user_id'):
                user_id = anon_session_data.get('converted_to_user_id')

                # Find authenticated session for this user with matching fingerprint
                user_sessions = self.redis_client.keys(f"session:*")
                for key in user_sessions:
                    sess_data = self.redis_client.hgetall(key)
                    if (sess_data.get('user_id') == user_id and
                        sess_data.get('device_fingerprint') == fingerprint):
                        sess_data['session_key'] = key
                        return sess_data

            return None

        except Exception as e:
            logger.error(f"Error finding session by fingerprint: {e}")
            return None


class FingerprintHeaderMiddleware(MiddlewareMixin):
    """
    Simple middleware to add device fingerprint to response headers.

    This allows clients to cache the fingerprint without generating it themselves.
    Only runs for anonymous users to avoid exposing authenticated user fingerprints.
    """

    def process_response(self, request, response):
        """
        Add X-Device-Fingerprint header to response for anonymous users.
        """
        try:
            # Only for anonymous users
            user = getattr(request, 'user', None)
            if user and not isinstance(user, AnonymousUser):
                return response

            # Check if fingerprint is cached on request
            fingerprint = getattr(request, '_cached_device_fingerprint', None)

            if fingerprint:
                response['X-Device-Fingerprint'] = fingerprint

        except Exception as e:
            logger.error(f"Error adding fingerprint to response: {e}")

        return response
