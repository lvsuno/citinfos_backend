"""
Shared JWT Token Renewal Service

This service handles JWT token renewal for both HTTP middleware and WebSocket middleware.
It ensures ONE JWT TOKEN per session that can be renewed by either component.

The renewal logic is extracted from the main middleware to be reusable.
"""

import jwt
import logging
from django.contrib.auth import get_user_model
from core.session_manager import SessionManager

logger = logging.getLogger(__name__)
User = get_user_model()

try:
    from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
    from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


class TokenRenewalService:
    """
    Shared service for JWT token renewal using active sessions.

    This implements the same renewal logic as your main middleware
    but can be used by both HTTP middleware and WebSocket middleware.
    """

    def __init__(self):
        self.session_manager = SessionManager()

    def renew_jwt_token(self, expired_token, session_id=None):
        """
        Renew JWT token using the same logic as main middleware.

        Args:
            expired_token (str): The expired JWT token
            session_id (str, optional): Session ID if available

        Returns:
            dict: {
                'success': bool,
                'access_token': str or None,
                'refresh_token': str or None,
                'user': User instance or None,
                'session_id': str or None,
                'error': str or None
            }
        """
        if not JWT_AVAILABLE:
            return {'success': False, 'error': 'JWT not available'}

        try:
            # Try to decode the expired token without verification to get payload
            payload = jwt.decode(
                expired_token,
                options={"verify_signature": False, "verify_exp": False}
            )
            token_session_id = payload.get('sid')
            user_id = payload.get('user_id')

            logger.debug(f"Token renewal - session_id: {token_session_id}, user_id: {user_id}")

            # Use session_id from token if not provided
            if not session_id:
                session_id = token_session_id

            if not session_id:
                logger.debug("No session ID available for token renewal")
                
                # Special handling for admin users - try to get user first to check if admin
                if user_id:
                    try:
                        user = User.objects.select_related('profile').get(id=user_id)
                        
                        # Check if user is admin - admins can renew tokens without session ID
                        if hasattr(user, 'profile') and user.profile.role == 'admin':
                            logger.info(f"🔧 Admin user {user.username} renewing token without session ID")
                            
                            # Generate new tokens for admin without session dependency
                            refresh = RefreshToken.for_user(user)
                            access_token = refresh.access_token
                            
                            # Add basic claims
                            access_token['username'] = user.username
                            access_token['email'] = user.email
                            access_token['role'] = user.profile.role
                            access_token['is_verified'] = user.profile.is_verified
                            
                            return {
                                'success': True,
                                'access_token': str(access_token),
                                'refresh_token': str(refresh),
                                'user': user,
                                'session_id': None,  # No session for admin
                                'error': None
                            }
                            
                    except User.DoesNotExist:
                        pass
                
                return {'success': False, 'error': 'No session ID for renewal'}

            # Hash the session ID before lookup (same logic as middleware)
            import hashlib
            from django.conf import settings
            hash_algo = getattr(settings, 'SESSION_TOKEN_HASH_ALGO', 'sha256')
            hashed_session_id = hashlib.new(hash_algo, session_id.encode()).hexdigest()

            logger.debug(f"Token renewal - raw session_id: {session_id}, hashed: {hashed_session_id[:20]}...")

            # Check if the associated session is still valid
            session_data = self.session_manager.get_session(hashed_session_id)
            if not session_data or not session_data.get('is_active', False):
                logger.debug("Associated session not found or inactive")
                return {'success': False, 'error': 'Session expired'}

            # Get user for token generation
            try:
                user = User.objects.select_related('profile').get(id=user_id)

                # Check if user is still active
                if not user.is_active:
                    logger.debug(f"User {user.username} is no longer active")
                    return {'success': False, 'error': 'User inactive'}

                # Check user profile soft deletion
                if hasattr(user, 'profile'):
                    profile = user.profile
                    if getattr(profile, 'is_deleted', False):
                        logger.debug(f"User profile {profile.id} is deleted")
                        return {'success': False, 'error': 'User profile deleted'}

            except User.DoesNotExist:
                logger.debug(f"User with ID {user_id} not found")
                return {'success': False, 'error': 'User not found'}

            # Generate new JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Add session ID to the access token payload (same as main middleware)
            access_token['sid'] = session_id

            # Smart renew session if needed
            self.session_manager.smart_renew_session_if_needed(session_id)

            logger.info(f"JWT token renewed successfully for user: {user.username}")

            return {
                'success': True,
                'access_token': str(access_token),
                'refresh_token': str(refresh),
                'user': user,
                'session_id': session_id,
                'error': None
            }

        except Exception as e:
            logger.error(f"Token renewal failed: {e}")
            return {'success': False, 'error': f'Token renewal failed: {str(e)}'}

    def validate_session(self, session_id):
        """
        Validate if a session is still active.

        Args:
            session_id (str): Session ID to validate

        Returns:
            bool: True if session is valid and active
        """
        if not session_id:
            return False

        try:
            session_data = self.session_manager.get_session(session_id)
            return session_data and session_data.get('is_active', False)
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False

    def create_tokens_from_session(self, session_id, user_profile):
        """
        Create new JWT tokens from valid session when JWT is absent.

        Args:
            session_id (str): Raw session ID from header
            user_profile: UserProfile instance

        Returns:
            dict: {
                'success': bool,
                'access_token': str or None,
                'refresh_token': str or None,
                'error': str or None
            }
        """
        if not JWT_AVAILABLE:
            return {
                'success': False,
                'error': 'JWT libraries not available'
            }

        try:
            # Note: session_id is already hashed when coming from
            # find_any_active_session_by_fingerprint
            # No need to hash again as it's already in the stored format

            # DEBUG: Log session validation details
            logger.info(f"🔍 Validating session for JWT creation: {session_id[:20]}...")
            logger.info(f"🔍 User profile: {user_profile.user.username}")

            # Validate session is still active
            session_valid = self.session_manager.is_session_valid_for_jwt(
                session_id  # Use session_id directly - it's already hashed
            )

            logger.info(f"🔍 Session validation result: {session_valid}")

            if not session_valid:
                logger.error(f"❌ Session validation failed for {session_id[:20]}...")
                return {
                    'success': False,
                    'error': 'Session expired or invalid'
                }

            # Create new JWT tokens
            user = user_profile.user
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            # Add session ID to token payload
            access['sid'] = session_id
            refresh['sid'] = session_id

            # Add user profile ID to token payload
            access['profile_id'] = str(user_profile.id)
            refresh['profile_id'] = str(user_profile.id)

            logger.info(
                f"Created new JWT tokens from session for user {user.id}"
            )

            return {
                'success': True,
                'access_token': str(access),
                'refresh_token': str(refresh),
                'error': None
            }

        except Exception as e:
            logger.error(f"Failed to create tokens from session: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance for shared use
token_renewal_service = TokenRenewalService()
