"""
Optimized Authentication Middleware

Implements efficient JWT-first authentication with session fallback.
Only checks Redis session when JWT is expired for renewal purposes.
Uses TokenRenewalService and JWTAuthService for consistent token management.
"""

import logging
import time
import hashlib
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from core.session_manager import session_manager
from core.token_renewal import token_renewal_service
from core.jwt_auth import jwt_auth_service
from core.utils import get_client_ip

logger = logging.getLogger(__name__)
User = get_user_model()


class OptimizedAuthenticationMiddleware(MiddlewareMixin):
    """
    Optimized authentication middleware for JWT-first authentication.
    Provides significant performance improvements by validating JWT tokens first,
    falling back to session-based authentication only when tokens are expired.
    Includes comprehensive analytics tracking for performance monitoring.
    """

    # Paths that don't require authentication
    EXEMPT_PATHS = [
            '/api/auth/csrf/',  # CSRF token endpoint
            '/api/auth/register/',
            '/api/auth/login-with-verification-check/',
            '/api/auth/verify/',  # Email verification
            '/api/auth/resend-code/',  # Resend verification code
            '/api/auth/request-verification/',  # Request verification
            '/api/auth/register-professional/',
            '/api/auth/verification-status/',  # Check verification status
            '/api/auth/generate-passwords/',  # Password generation endpoint
            '/api/auth/validate-password/',   # Password validation endpoint
            '/api/auth/password-reset-confirm/',  # Password reset (public)

            # Geolocation endpoints (for registration and anonymous browsing)
            '/api/auth/location-data/',  # IP-based location detection
            '/api/auth/search-divisions/',  # Administrative division search
            '/api/auth/countries/',  # List available countries
            '/api/auth/divisions/',  # Browse divisions by country/level
            '/api/auth/division-neighbors/',  # Get neighboring divisions

            # Social authentication endpoints (Django AllAuth)
            '/api/auth/social/',
            '/api/auth/social/url/',
            '/api/auth/social/apps/',

            # Public profile endpoints (no authentication required)
            '/api/public-profiles/',
            '/api/public/profiles/',
            '/api/public/users/',

            # Debug endpoints (no authentication required)
            '/api/debug/',

            '/admin/',
            '/swagger/',
            '/redoc/',
            '/static/',
            '/media/',
    ]

    def process_request(self, request):
        """
        Consolidated JWT-first authentication with session fallback.

        Authentication Flow:
        1. Always use JWT for authentication
        2. If JWT expires, check associated session and renew if session is active
        3. To check session, we use Redis (never database)
        4. Smart renewal: JWT (1/3 validity), Session (10% validity)
        5. Check renewal frequency (not too often to avoid performance issues)
        """
        # DEBUG: Log that middleware is running
        logger.info(f"🔍 OptimizedAuthenticationMiddleware processing: {request.path}")

        # Track analytics start time
        start_time = time.time()
        auth_method = 'jwt_primary'
        success = False
        error_message = ''
        jwt_validation_time = None
        session_lookup_time = None
        jwt_renewed = False

        try:
            # Skip authentication during tests to allow force_authenticate
            import sys
            if 'test' in sys.argv:
                # In test mode, let Django REST Framework handle authentication
                logger.info(f"🔍 Test mode detected, skipping middleware auth")
                return None

            # Check if user is already authenticated (for tests using force_authenticate)
            if hasattr(request, 'user') and request.user and request.user.is_authenticated:
                logger.info(f"🔍 User already authenticated: {request.user}")
                auth_method = 'pre_authenticated'
                success = True
                self._track_auth_analytics(
                    request, start_time, auth_method, success
                )
                return None

            # Skip validation for exempt paths
            if self._is_exempt_path(request.path):
                auth_method = 'exempt_path'
                success = True
                self._track_auth_analytics(
                    request, start_time, auth_method, success
                )
                return None

            # Skip validation for non-API requests
            if not request.path.startswith('/api/'):
                auth_method = 'non_api'
                success = True
                self._track_auth_analytics(
                    request, start_time, auth_method, success
                )
                return None

            # REQUIREMENT 1: Always use JWT for auth - require Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            logger.info(f"🔍 Auth header present: {bool(auth_header.startswith('Bearer '))}")
            logger.info(f"🔍 [DEBUG] Full auth header: {auth_header[:50]}..." if auth_header else "🔍 [DEBUG] No auth header found")

            if not auth_header.startswith('Bearer '):
                # FALLBACK: Try to find existing session using device fingerprint
                auth_method = 'session_fingerprint_fallback'
                logger.info(
                    "No JWT token provided, attempting session-based "
                    "authentication using device fingerprint"
                )

                # Try to authenticate using fast fingerprint to find session
                fallback_result = self._authenticate_with_fingerprint_fallback(
                    request, start_time
                )
                if fallback_result is None:  # None means success
                    return None  # Authentication successful, continue processing

                # Return the specific error response from fallback
                return fallback_result

            # Extract JWT token
            token = auth_header.split(' ')[1]
            logger.info(f"🔍 JWT token extracted: {token[:20]}...")

            # STEP 1: Primary JWT validation (fast path)
            jwt_start_time = time.time()
            try:
                # Use JWTAuthService for consistent validation
                user = jwt_auth_service.validate_token_and_get_user(token)
                if not user:
                    raise InvalidToken("Invalid token or user")

                # Decode token to get session info (for subsequent processing)
                import jwt as pyjwt
                decoded = pyjwt.decode(token, options={"verify_signature": False})
                user_id = decoded.get('user_id')
                session_id = decoded.get('sid')

                if not session_id:
                    raise InvalidToken("Token missing session information")

                jwt_validation_time = (time.time() - jwt_start_time) * 1000

                # JWT is valid - set authenticated user
                request.user = user
                request.auth = token
                request.validated_session_id = session_id
                request.jwt_user_id = user_id

                logger.debug(f"✅ JWT valid for user {user_id}, session {session_id}")

                # REQUIREMENT 5: Periodic session renewal check (avoid session expiry)
                # Hash session_id before using with Redis
                hashed_session_id = self._hash_session_id(session_id)
                self._check_periodic_session_renewal(hashed_session_id)

                success = True
                auth_method = 'jwt_primary_success'
                self._track_auth_analytics(
                    request, start_time, auth_method, success,
                    jwt_validation_time=jwt_validation_time,
                    jwt_renewed=jwt_renewed
                )

                # Track session analytics and usage patterns (async to avoid blocking)
                self._track_session_analytics(request)

                return None  # JWT authentication successful

            except (InvalidToken, TokenError) as jwt_error:
                # STEP 2: REQUIREMENT 2 - JWT expired, check associated session and renew if active
                jwt_validation_time = (time.time() - jwt_start_time) * 1000
                logger.info(f"🔍 JWT invalid/expired: {jwt_error}")
                error_message = str(jwt_error)
                auth_method = 'jwt_expired_session_renewal'

                # Handle JWT expiry with session-based renewal
                logger.info("🔍 Attempting JWT expiry with session renewal...")
                result = self._handle_jwt_expiry_with_session_renewal(request, token)
                logger.info(f"🔍 Session renewal result: {result}")

                # Get session lookup timing if available
                if hasattr(request, 'session_lookup_time'):
                    session_lookup_time = request.session_lookup_time

                # Check if renewal was successful
                if hasattr(request, 'jwt_renewed') and request.jwt_renewed:
                    success = True
                    jwt_renewed = True
                    auth_method = 'jwt_renewed_from_session'
                    error_message = ''  # Clear error on successful renewal
                    logger.info("🎉 JWT renewal successful!")
                else:
                    success = (result is None)  # None means success

                self._track_auth_analytics(
                    request, start_time, auth_method, success,
                    error_message=error_message,
                    jwt_validation_time=jwt_validation_time,
                    session_lookup_time=session_lookup_time,
                    jwt_renewed=jwt_renewed
                )
                return result

        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            success = False
            error_message = str(e)
            self._track_auth_analytics(
                request, start_time, auth_method, success,
                error_message=error_message,
                jwt_validation_time=jwt_validation_time
            )
            return self._auth_error_response(
                'Authentication validation failed',
                'VALIDATION_ERROR'
            )

    def _hash_session_id(self, session_id):
        """
        Hash session ID using the algorithm defined in settings.
        Same logic as used in SessionManager.
        """
        try:
            from django.conf import settings
            hash_algo = getattr(settings, 'SESSION_TOKEN_HASH_ALGO', 'sha256')
            return hashlib.new(hash_algo, session_id.encode()).hexdigest()
        except Exception:
            # Fallback to sha256 if anything fails
            return hashlib.sha256(session_id.encode()).hexdigest()

    def _validate_jwt_session_sync(self, session_id, user_id):
        """
        REQUIREMENT 3: Check session via Redis (never DB) to ensure JWT-session sync.
        Only called during JWT renewal process, not for valid JWT validation.
        """
        try:
            # Hash the session ID before using with Redis
            hashed_session_id = self._hash_session_id(session_id)

            # Check if session exists and is valid via Redis
            if not session_manager.is_session_valid_for_jwt(hashed_session_id):
                logger.debug(f"Session {session_id} invalid for JWT validation")

                # Track session expiry analytics
                self._track_session_renewal_analytics(
                    session_id, user_id, 'expired'
                )

                return False

            # Get session data from Redis (never database)
            session_data = session_manager.get_session(hashed_session_id)
            if not session_data:
                logger.debug(f"Session data not found for {session_id}")

                # Track session expiry (session was cleaned up)
                self._track_session_renewal_analytics(
                    session_id, user_id, 'expired'
                )

                return False

            # Validate session belongs to token user
            session_user_id = session_data.get('user_id')
            if str(session_user_id) != str(user_id):
                logger.warning(f"Session mismatch: session_user={session_user_id}, token_user={user_id}")
                return False

            return True

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False

    def _get_session_duration_seconds(self):
        """
        Get session duration in seconds from settings.
        Default to 4 hours if not configured.
        """
        try:
            from django.conf import settings
            # Try to get from settings, default to 4 hours
            duration_hours = getattr(settings, 'SESSION_DURATION_HOURS', 4)
            return duration_hours * 3600  # Convert hours to seconds
        except Exception:
            return 4 * 3600  # Default 4 hours in seconds

    def _check_periodic_session_renewal(self, session_id):
        """
        Periodic session renewal check to prevent session expiry.
        Checks every session_duration/10 to ensure maximum 10 checks per session.
        For 4h session = check every 24 minutes.
        """
        try:
            current_time = time.time()

            # Calculate check interval dynamically based on session duration
            session_duration = self._get_session_duration_seconds()
            check_interval = session_duration / 10  # Check every 1/10 of session duration

            # Check frequency control key
            last_check_key = f"session_renewal_check:{session_id}"
            last_check = session_manager.redis_client.get(last_check_key)

            # Skip if we checked recently (within the check interval)
            if last_check and (current_time - float(last_check)) < check_interval:
                return

            # Mark this check attempt
            session_manager.redis_client.setex(
                last_check_key,
                int(check_interval),
                str(current_time)
            )

            # Get session data to check if renewal is needed
            session_data = session_manager.get_session(session_id)
            if not session_data:
                return

            session_expires_at = session_data.get('expires_at')
            if not session_expires_at:
                return

            # Convert to timestamp if it's a datetime object
            if hasattr(session_expires_at, 'timestamp'):
                session_expires_at = session_expires_at.timestamp()

            remaining_validity = session_expires_at - current_time
            renewal_threshold = session_duration * 0.1  # 10% of session duration

            # Renew if 10% or less validity remaining
            if remaining_validity <= renewal_threshold and remaining_validity > 0:
                try:
                    session_manager.smart_renew_session_if_needed(session_id, check_renew=False)
                    logger.debug(f"🔄 Session proactively renewed: {session_id}")

                    # Track session renewal analytics
                    self._track_session_renewal_analytics(
                        session_id, session_data.get('user_id'), 'renewed'
                    )

                except Exception as e:
                    logger.warning(f"Proactive session renewal failed for {session_id}: {e}")

        except Exception as e:
            logger.warning(f"Periodic session renewal check failed: {e}")

    def _handle_jwt_expiry_with_session_renewal(self, request, expired_token):
        """
        Handle JWT expiry using session-based renewal (REQUIREMENT 2).
        """
        session_lookup_start = time.time()
        try:
            logger.info(f"🔍 [DEBUG] Starting JWT renewal with expired token: {expired_token[:30]}...")

            # Use TokenRenewalService to handle the renewal logic
            renewal_result = token_renewal_service.renew_jwt_token(expired_token)
            logger.info(f"🔍 [DEBUG] TokenRenewalService result: {renewal_result}")

            session_lookup_time = (time.time() - session_lookup_start) * 1000
            request.session_lookup_time = session_lookup_time

            if renewal_result['success']:
                # Renewal successful
                user = renewal_result['user']
                session_id = renewal_result['session_id']

                # Set response headers for frontend to pick up new token
                request.META['HTTP_X_NEW_ACCESS_TOKEN'] = renewal_result['access_token']
                request.META['HTTP_X_NEW_REFRESH_TOKEN'] = renewal_result['refresh_token']

                # Set authenticated user for downstream processing
                request.user = user
                request.auth = renewal_result['access_token']

                # *** CRITICAL FIX: Update Authorization header for DRF ***
                # DRF's JWTAuthentication reads from Authorization header
                # We must update it so DRF uses the renewed token
                new_access_token = renewal_result['access_token']
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'

                # Store tokens for response headers
                request.META['HTTP_X_NEW_ACCESS_TOKEN'] = new_access_token
                if 'refresh_token' in renewal_result:
                    request.META['HTTP_X_NEW_REFRESH_TOKEN'] = renewal_result['refresh_token']

                # Add session info to request
                request.validated_session_id = session_id
                request.jwt_user_id = str(user.id)
                request.jwt_renewed = True

                logger.info(f"🔄 JWT renewed for user {user.id} from session {session_id}")
                logger.debug(f"✅ Updated Authorization header with renewed token for DRF")

                # Track JWT renewal analytics
                self._track_session_renewal_analytics(
                    session_id, str(user.id), 'smart_renewal'
                )

                # Track session analytics for renewed sessions too
                self._track_session_analytics(request)

                return None  # Continue processing with renewed JWT
            else:
                # Renewal failed - return appropriate error
                error_msg = renewal_result.get('error', 'Token renewal failed')

                if 'Session expired' in error_msg:
                    return self._auth_error_response(
                        'Session expired. Please login again.',
                        'SESSION_EXPIRED'
                    )
                elif 'User not found' in error_msg:
                    return self._auth_error_response(
                        'User not found for session',
                        'USER_NOT_FOUND'
                    )
                else:
                    return self._auth_error_response(
                        error_msg,
                        'RENEWAL_FAILED'
                    )

        except Exception as e:
            logger.error(f"Token renewal failed: {e}")
            return self._auth_error_response(
                'Token renewal failed',
                'RENEWAL_FAILED'
            )

    def _authenticate_with_fingerprint_fallback(self, request, start_time):
        """
        Authenticate using fast device fingerprint when JWT is absent.
        Finds existing session by fingerprint and generates new JWT tokens.

        Args:
            request: Django request object
            start_time: Analytics start time

        Returns:
            None if successful, error response if failed
        """
        try:
            # Get fast device fingerprint
            from core.device_fingerprint import OptimizedDeviceFingerprint
            fast_fingerprint = OptimizedDeviceFingerprint.get_fast_fingerprint(
                request
            )

            # DEBUG: Log the fingerprint we're generating and the headers used
            logger.info(f"🔍 Generated fingerprint: {fast_fingerprint}")
            logger.info(f"🔍 Headers used for fingerprint:")
            logger.info(f"  - User-Agent: {request.META.get('HTTP_USER_AGENT', 'None')}")
            logger.info(f"  - Accept: {request.META.get('HTTP_ACCEPT', 'None')}")
            logger.info(f"  - Accept-Language: {request.META.get('HTTP_ACCEPT_LANGUAGE', 'None')}")
            logger.info(f"  - Accept-Encoding: {request.META.get('HTTP_ACCEPT_ENCODING', 'None')}")
            logger.info(f"🔍 Looking for session with this fingerprint in Redis...")

            if not fast_fingerprint:
                logger.debug("Could not generate device fingerprint")
                return self._auth_error_response(
                    'Device identification failed. Please login again.',
                    'FINGERPRINT_FAILED'
                )

            # SOLUTION: Find ANY active session by fingerprint (post-restart scenario)
            # This handles the case where Django sessions are lost after restart
            # but our custom sessions remain valid in Redis/Database
            existing_session = session_manager.find_any_active_session_by_fingerprint(
                fast_fingerprint
            )

            if not existing_session:
                logger.debug(f"No valid session found for fingerprint {fast_fingerprint[:8]}...")
                return self._auth_error_response(
                    'No active session found. Please login again.',
                    'SESSION_NOT_FOUND'
                )

            # Get user from found session
            user_profile = existing_session['user_profile']
            session_id = existing_session['session_id']

            logger.info(f"Found active session for user {user_profile.user.username} via fingerprint")

            # Generate new JWT tokens using the found session
            try:
                # Use TokenRenewalService to create new tokens from session
                renewal_result = token_renewal_service.create_tokens_from_session(
                    session_id, user_profile
                )

                if not renewal_result['success']:
                    logger.error(f"Failed to create JWT from session: {renewal_result.get('error')}")
                    return self._auth_error_response(
                        'Failed to create authentication tokens',
                        'TOKEN_CREATION_FAILED'
                    )                # Set authentication context
                new_access_token = renewal_result['access_token']
                user = user_profile.user
                request.user = user
                request.auth = new_access_token
                request.validated_session_id = session_id
                request.jwt_user_id = str(user.id)
                request.jwt_renewed = True

                # Update Authorization header for DRF compatibility
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'

                # Store tokens for response headers
                request.META['HTTP_X_NEW_ACCESS_TOKEN'] = new_access_token
                if 'refresh_token' in renewal_result:
                    request.META['HTTP_X_NEW_REFRESH_TOKEN'] = renewal_result['refresh_token']

                logger.info(f"✅ JWT created from fingerprint session for user {user.id}")

                # Track analytics for fingerprint-based authentication
                self._track_auth_analytics(
                    request, start_time, 'fingerprint_fallback_success', True,
                    jwt_renewed=True
                )

                # Track session analytics
                self._track_session_analytics(request)

                return None  # Success - continue processing

            except Exception as token_error:
                logger.error(f"Token creation from fingerprint session failed: {token_error}")
                return self._auth_error_response(
                    'Failed to create authentication tokens',
                    'TOKEN_CREATION_FAILED'
                )

        except Exception as e:
            logger.error(f"Fingerprint fallback authentication error: {e}")
            return self._auth_error_response(
                'Authentication failed. Please login again.',
                'FINGERPRINT_AUTH_FAILED'
            )

    def _get_user_from_django_session(self, request):
        """
        Try to get user from Django session data.

        Args:
            request: Django request object

        Returns:
            UserProfile instance if found, None otherwise
        """
        try:
            # Check if Django session has user_id
            user_id = request.session.get('_auth_user_id')
            if user_id:
                from django.contrib.auth.models import User
                from accounts.models import UserProfile

                user = User.objects.get(id=user_id)
                user_profile = UserProfile.objects.get(user=user)
                return user_profile

            # Alternative: check if user is already set in request
            if hasattr(request, 'user') and request.user.is_authenticated:
                from accounts.models import UserProfile
                user_profile = UserProfile.objects.get(user=request.user)
                return user_profile

            return None

        except Exception as e:
            logger.debug(f"Could not get user from Django session: {e}")
            return None

    def process_response(self, request, response):
        """
        Add new JWT tokens to response headers if renewal occurred.
        """
        if hasattr(request, 'jwt_renewed') and request.jwt_renewed:
            new_access = request.META.get('HTTP_X_NEW_ACCESS_TOKEN')
            new_refresh = request.META.get('HTTP_X_NEW_REFRESH_TOKEN')

            if new_access:
                response['X-New-Access-Token'] = new_access
                response['X-Token-Renewed'] = 'true'
                logger.info("✅ Added renewed access token to response")
            if new_refresh:
                response['X-New-Refresh-Token'] = new_refresh
                logger.info("✅ Added renewed refresh token to response")

            logger.debug("🔄 JWT renewal tokens added to response headers")

        # Add session ID for debugging and tracing (MEDIUM PRIORITY)
        if hasattr(request, 'validated_session_id'):
            response['X-Session-ID'] = request.validated_session_id

        return response

    def _is_exempt_path(self, path):
        """Check if path is exempt from authentication."""
        # Check exact matches and prefix matches
        for exempt in self.EXEMPT_PATHS:
            if path == exempt or path.startswith(exempt):
                return True
        return False

    def _auth_error_response(self, message, code):
        """Return standardized authentication error response."""
        return JsonResponse({
            'error': 'Authentication failed',
            'detail': message,
            'code': code,
            'action': 'login_required'
        }, status=401)

    def _track_auth_analytics(self, request, start_time, auth_method, success,
                              error_message='', jwt_validation_time=None,
                              session_lookup_time=None, jwt_renewed=False,
                              token_age_seconds=None,
                              token_remaining_seconds=None):
        """
        Track authentication performance analytics asynchronously.
        """
        try:
            from analytics.tasks import track_authentication_performance

            total_auth_time = (time.time() - start_time) * 1000  # ms

            auth_data = {
                'auth_method': auth_method,
                'user_id': getattr(request, 'jwt_user_id', None),
                'session_id': getattr(request, 'validated_session_id', ''),
                'jwt_validation_time': jwt_validation_time,
                'session_lookup_time': session_lookup_time,
                'total_auth_time': total_auth_time,
                'endpoint': request.path,
                'http_method': request.method,
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'success': success,
                'error_message': error_message,
                'jwt_renewed': jwt_renewed,
                'token_age_seconds': token_age_seconds,
                'token_remaining_seconds': token_remaining_seconds,
                'additional_data': {
                    'timestamp': time.time(),
                    'middleware_version': '1.0.0'
                }
            }

            # Track analytics asynchronously
            track_authentication_performance.delay(auth_data)

        except Exception as e:
            logger.warning(f"Failed to track authentication analytics: {e}")

    def _track_session_analytics(self, request):
        """
        Track comprehensive session analytics.
        Consolidates functionality from SessionAnalyticsMiddleware.
        """
        # Skip if no validated session
        if not hasattr(request, 'validated_session_id'):
            return

        try:
            # Use the comprehensive session tracking
            from analytics.tasks import track_session_comprehensive

            # Get user ID if available
            user_id = getattr(request, 'jwt_user_id', None)
            if not user_id:
                return

            # Determine session event type based on context
            event_type = 'page_visit'  # Default for regular page visits

            # Map middleware events to SessionAnalytic.SESSION_EVENTS
            if hasattr(request, 'jwt_renewed') and request.jwt_renewed:
                event_type = 'smart_renewal'  # Custom event for JWT renewals
            elif (hasattr(request, 'session_renewed') and
                  request.session_renewed):
                event_type = 'renewed'  # Maps to SESSION_EVENTS
            elif (hasattr(request, 'session_expired') and
                  request.session_expired):
                event_type = 'expired'  # Maps to SESSION_EVENTS
            elif (hasattr(request, 'renewal_skipped') and
                  request.renewal_skipped):
                event_type = 'renewal_skipped'  # Custom tracking

            # Get location data from SessionContextMiddleware
            location_data = {}
            if hasattr(request, 'location_context'):
                location_data = request.location_context

            # Get creation time from session timing data if available
            creation_time_ms = getattr(request, 'session_creation_time', 0.0)

            # Prepare session data for comprehensive tracking
            session_data = {
                'session_id': request.validated_session_id,
                'user_id': user_id,
                'event_type': event_type,
                'creation_time_ms': creation_time_ms,
                'path': request.path,
                'http_method': request.method,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'location_data': location_data,
                'additional_metadata': {
                    'timestamp': time.time(),
                    'middleware_version': '1.0.0'
                }
            }

            # Track session lifecycle asynchronously
            track_session_comprehensive.delay(session_data)

        except Exception as e:
            logger.warning(f"Session analytics tracking failed: {e}")

    def _track_session_renewal_analytics(self, session_id, user_id,
                                         event_type):
        """
        Track session renewal events (renewed, smart_renewal, expired).
        """
        if not session_id or not user_id:
            return

        try:
            from analytics.tasks import track_session_comprehensive

            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'event_type': event_type,
                'additional_metadata': {
                    'timestamp': time.time(),
                    'source': 'optimized_auth_middleware'
                }
            }

            # Track renewal event asynchronously
            track_session_comprehensive.delay(session_data)
            logger.debug(
                f"Session {event_type} analytics tracked for {session_id}"
            )

        except Exception as e:
            logger.warning(
                f"Failed to track session {event_type} analytics: {e}"
            )

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        return get_client_ip(request)


class SessionContextMiddleware(MiddlewareMixin):
    """
    Lightweight middleware to inject session context into requests.
    Only runs after successful authentication.
    """

    def process_request(self, request):
        """
        Add session context to authenticated requests.
        """
        # Skip if no validated session
        if not hasattr(request, 'validated_session_id'):
            return None

        try:
            # Hash session ID before using with Redis (same logic as authentication middleware)
            from django.conf import settings
            import hashlib

            raw_session_id = request.validated_session_id
            hash_algo = getattr(settings, 'SESSION_TOKEN_HASH_ALGO', 'sha256')
            hashed_session_id = hashlib.new(hash_algo, raw_session_id.encode()).hexdigest()

            # Get session data efficiently (uses Redis cache)
            session_data = session_manager.get_session(hashed_session_id)

            if session_data:
                # Add location context to request
                location_data = session_data.get('location_data', {})
                request.user_location = {
                    'administrative_division_id': location_data.get(
                        'administrative_division_id'
                    ),
                    'division_name': location_data.get('division_name'),
                    'region': location_data.get('region'),
                    'latitude': location_data.get('latitude'),
                    'longitude': location_data.get('longitude'),
                    'user_timezone': location_data.get('user_timezone'),
                    'detected_timezone': location_data.get(
                        'detected_timezone'
                    ),
                }

                # Add to request META for middleware compatibility
                if location_data.get('division_name'):
                    request.META['HTTP_X_USER_DIVISION'] = (
                        location_data['division_name']
                    )

                # Add device context
                request.user_device = session_data.get('device_info', {})

                # Add session context
                request.session_data = session_data

        except Exception as e:
            logger.warning(f"Failed to inject session context: {e}")
            request.user_location = {}
            request.user_device = {}

        return None
