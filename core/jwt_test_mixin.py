"""Reusable JWT authentication mixin for DRF APITestCase.

Provides helper methods to generate session-aware JWT tokens consistent with the
project's authentication layer and to authenticate test clients with a concise
API. Includes a lightweight assertion ensuring the Authorization header uses
Bearer tokens as expected.
"""
from __future__ import annotations

from typing import Dict, Any
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import Mock

from accounts.models import UserProfile  # Adjust if path differs


class JWTAuthTestMixin:
    """Mixin adding JWT auth helpers for API test cases.

    Expects the concrete TestCase to define a ``client`` and any user objects
    it wants to authenticate (e.g. ``self.user1``, ``self.user2``).
    """

    def _create_jwt_token_with_session(self, user) -> Dict[str, str]:  # type: ignore[override]
        """Create a refresh/access token pair with session and store in SessionManager."""
        from core.session_manager import SessionManager

        refresh = RefreshToken.for_user(user)
        session_id = f"test_session_{user.id}_{timezone.now().timestamp()}"
        refresh['sid'] = session_id
        access = refresh.access_token
        access['sid'] = session_id
        access['username'] = user.username
        access['email'] = user.email
        try:
            profile = UserProfile.objects.get(user=user)
            access['role'] = profile.role
            access['is_verified'] = profile.is_verified
        except UserProfile.DoesNotExist:  # pragma: no cover - defensive
            access['role'] = 'normal'
            access['is_verified'] = False

        # Create a session in the SessionManager
        session_manager = SessionManager()
        mock_request = Mock()
        mock_request.session = Mock()
        mock_request.session.session_key = session_id
        mock_request.session.create = Mock(return_value=None)
        mock_request.META = {
            'HTTP_USER_AGENT': 'Test User Agent',
            'REMOTE_ADDR': '127.0.0.1'
        }

        # Create device info for tests
        device_info = {
            'browser': {
                'family': 'Test Browser',
                'version': '1.0'
            },
            'os': {
                'family': 'Test OS',
                'version': '1.0'
            },
            'device': {
                'family': 'Test Device'
            },
            'client_info': {
                'screen_resolution': '1920x1080',
                'timezone': 'UTC'
            }
        }

        try:
            profile = UserProfile.objects.get(user=user)
            session_manager.create_session(mock_request, profile, device_info)
        except Exception:
            # If session creation fails in tests, continue anyway
            pass

        return {
            'access': str(access),
            'refresh': str(refresh),
            'session_id': session_id,
        }

    # ------------------------------------------------------------------
    # Authentication helpers
    # ------------------------------------------------------------------
    def authenticate(self, token_data: Any):  # type: ignore[override]
        """Authenticate test client.

        Accepts either a pre-built token_data dict (with 'access') or a
        Django ``User`` instance, in which case a token is generated on the
        fly. Returns the token_data dict used.
        """
        if not isinstance(token_data, dict) or 'access' not in token_data:
            # Assume it's a User instance; generate token pair
            token_data = self._create_jwt_token_with_session(  # type: ignore[arg-type]
                token_data
            )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_data['access']}"
        )
        # Small assertion per requirement #4: ensure header uses Bearer
        auth_header = self.client._credentials.get(  # type: ignore[attr-defined]
            'HTTP_AUTHORIZATION'
        )
        assert (
            auth_header and auth_header.startswith('Bearer ')
        ), 'Authorization header must start with Bearer'
        return token_data

    def clear_authentication(self):
        self.client.credentials()

    # Convenience wrappers expecting jwt_token1 / jwt_token2 attributes
    def authenticate_user1(self):
        return self.authenticate(self.jwt_token1)  # type: ignore[attr-defined]

    def authenticate_user2(self):
        return self.authenticate(self.jwt_token2)  # type: ignore[attr-defined]
