"""
JWT Token Validation Service

Simple JWT token validation service that works with the main middleware's
token management. This service ONLY validates tokens - it does NOT create,
renew, or manage tokens. All token lifecycle is handled by the main middleware.

ONE JWT TOKEN PER SESSION - managed centrally by main middleware.
"""

import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

try:
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


class JWTAuthService:
    """
    Simple JWT token validation service.

    This service validates JWT tokens using the same logic as the main middleware
    but does NOT handle token creation, renewal, or session management.
    All token lifecycle is managed by the main middleware.

    ONE JWT TOKEN per session - no duplication, no separate token management.
    """

    @staticmethod
    def validate_token_and_get_user(raw_token):
        """
        Validate JWT token and return user if valid.

        This uses the SAME validation logic as main middleware but simplified:
        - Validates JWT token signature and expiration
        - Validates user exists and is active
        - Validates user profile is not deleted

        Args:
            raw_token (str): JWT token string from main middleware

        Returns:
            User instance if token is valid, None otherwise
        """
        if not raw_token or not JWT_AVAILABLE:
            logger.debug("No token provided or JWT not available")
            return None

        try:
            # Validate and decode JWT token (same as main middleware)
            token = AccessToken(raw_token)
            user_id = token.payload.get('user_id')

            if not user_id:
                logger.debug("No user_id in JWT payload")
                return None

            # Get user from database with same validation as main middleware
            try:
                user = User.objects.select_related('profile').get(id=user_id)
            except User.DoesNotExist:
                logger.debug(f"User with ID {user_id} does not exist")
                return None

            # Check if user is active (same as main middleware)
            if not user.is_active:
                logger.debug(f"User {user.username} is not active")
                return None

            # Check user profile soft deletion (same as main middleware)
            if hasattr(user, 'profile'):
                profile = user.profile
                if getattr(profile, 'is_deleted', False):
                    logger.debug(f"User profile {profile.id} is deleted")
                    return None

            logger.debug(f"JWT validation successful for user: {user.username}")
            return user

        except (TokenError, InvalidToken) as e:
            logger.debug(f"JWT token validation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected JWT validation error: {e}")
            return None

    @staticmethod
    def is_token_expired(raw_token):
        """
        Check if JWT token is expired without full validation.

        Args:
            raw_token (str): JWT token string

        Returns:
            True if token is expired, False if valid, None if invalid
        """
        if not raw_token or not JWT_AVAILABLE:
            return None

        try:
            AccessToken(raw_token)
            return False  # Token is valid (not expired)
        except TokenError:
            return True   # Token is expired
        except Exception:
            return None   # Token is invalid


# Global instance for easy importing
jwt_auth_service = JWTAuthService()
