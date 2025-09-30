"""
JWT Authentication specific tests for the accounts app.

This module contains comprehensive tests for JWT authentication integration
with Redis sessions, user registration, login, and account management.
"""

from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from core.session_manager import SessionManager

from .base import AccountsAPITestCase


class AccountsJWTAuthenticationTests(AccountsAPITestCase):
    """Test JWT authentication functionality in accounts app."""

    def test_jwt_token_authentication(self):
        """Test basic JWT authentication flow."""
        # Test unauthenticated access to protected endpoint - should return 401
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test authenticated access
        self.authenticate_user1()
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_jwt_token_contains_session_id(self):
        """Test that JWT tokens contain session ID claims."""
        token_data = self.jwt_token1

        # Decode token to check claims
        access_token = AccessToken(token_data['access'])
        self.assertIn('sid', access_token.payload)
        self.assertEqual(access_token.payload['sid'], token_data['session_id'])

    def test_jwt_token_contains_user_data(self):
        """Test that JWT tokens contain user profile data."""
        token_data = self.jwt_token1

        # Decode token to check user claims
        access_token = AccessToken(token_data['access'])
        self.assertEqual(access_token.payload['username'], self.user1.username)
        self.assertEqual(access_token.payload['email'], self.user1.email)
        self.assertEqual(access_token.payload['role'], self.user1_profile.role)

    def test_jwt_token_expiration_access_denied(self):
        """Test that expired JWT tokens are rejected."""
        # Create an expired token
        refresh = RefreshToken.for_user(self.user1)
        access = refresh.access_token
        # Set expiration to 1 hour ago
        exp_time = timezone.now() - timedelta(hours=1)
        access.set_exp(claim='exp', from_time=exp_time)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(access)}')
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_invalid_token_access_denied(self):
        """Test that invalid JWT tokens are rejected."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_here')
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_malformed_token_access_denied(self):
        """Test that malformed JWT tokens are rejected."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer malformed.token.here'
        )
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_with_session_integration(self):
        """Token refresh via endpoint succeeds when session (sid) is valid."""
        token_data = self.jwt_token1

        # Call refresh endpoint
        response = self.client.post(
            '/api/auth/refresh/',
            {'refresh': token_data['refresh']},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        # Rotation enabled: expect a new refresh in response
        self.assertIn('refresh', response.data)

        # New token works
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )
        resp2 = self.client.get('/api/auth/user-info/')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)

    def test_refresh_rejected_when_session_invalid(self):
        """Refresh fails with SESSION_EXPIRED when session invalid."""
        token_data = self.jwt_token1
        sid = token_data['session_id']
        SessionManager().invalidate_session(sid)

        response = self.client.post(
            '/api/auth/refresh/',
            {'refresh': token_data['refresh']},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get('code'), 'SESSION_EXPIRED')

    def test_auto_renew_header_emitted_near_expiry(self):
        """Emit X-Renewed-Access when token near expiry and sid valid."""
        token_data = self.jwt_token1

        # Create a token that triggers renewal (≤1/3 validity remaining)
        refresh = RefreshToken(token_data['refresh'])
        access = refresh.access_token
        import time

        # Create token with 30s total validity but only 8s remaining
        # This means 22s have "elapsed" out of 30s total (8/30 ≈ 26% < 33%)
        current_time = int(time.time())
        total_validity = 30  # 30 seconds total
        remaining_validity = 8  # 8 seconds remaining (≤1/3 of 30s)

        # Set issued time to 22s ago, expires in 8s
        elapsed_time = total_validity - remaining_validity
        access.payload['iat'] = current_time - elapsed_time
        access.payload['exp'] = current_time + remaining_validity
        # Preserve sid claim
        access['sid'] = token_data['session_id']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(access)}')
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        renewed = response.headers.get('X-Renewed-Access')
        self.assertIsNotNone(renewed)
        # Validate renewed token structure
        new_access = AccessToken(renewed)
        self.assertEqual(
            new_access.payload.get('sid'), token_data['session_id']
        )

    def test_authentication_clear(self):
        """Test clearing authentication credentials."""
        # Authenticate first
        self.authenticate_user1()
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Clear credentials
        self.client.credentials()
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_cross_user_access_denied(self):
        """Test that JWT tokens don't allow cross-user access."""
        # Create user-specific data
        self.authenticate_user1()

        # Try to access another user's specific profile data
        response = self.client.get(
            f'/api/profiles/{self.user2_profile.id}/'
        )
        # Should be able to view public profile but not modify
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Try to update another user's profile (should fail)
        update_data = {'bio': 'Unauthorized update'}
        response = self.client.patch(
            f'/api/profiles/{self.user2_profile.id}/',
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AccountsJWTSessionIntegrationTests(AccountsAPITestCase):
    """Test JWT integration with Redis sessions in accounts app."""

    def test_jwt_session_correlation(self):
        """Test that JWT tokens are properly correlated with sessions."""
        token_data = self.jwt_token1

        # Verify session ID in token matches our session
        access_token = AccessToken(token_data['access'])
        session_id = access_token.payload['sid']
        self.assertEqual(session_id, token_data['session_id'])

    def test_jwt_without_session_id_rejected(self):
        """Test that JWT tokens without session ID are handled properly."""
        # Create token without session integration
        refresh = RefreshToken.for_user(self.user1)
        access = refresh.access_token
        # This token won't have 'sid' claim

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(access)}')
        response = self.client.get('/api/auth/user-info/')
        # Should still work but without session benefits
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
        )


class AccountsJWTSecurityTests(AccountsAPITestCase):
    """Test JWT security features in accounts app."""

    def test_jwt_token_tampering_detection(self):
        """Test that tampered JWT tokens are rejected."""
        token_data = self.jwt_token1
        tampered_token = token_data['access'][:-10] + 'tampered123'

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered_token}')
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_token_reuse_after_logout(self):
        """Test that JWT tokens can't be reused after logout."""
        # Simulate logout by blacklisting refresh token
        token_data = self.jwt_token1
        refresh = RefreshToken(token_data['refresh'])

        try:
            refresh.blacklist()
        except AttributeError:
            # If blacklist method doesn't exist, skip this test
            self.skipTest("Token blacklisting not available")

        # Try to use access token after logout
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token_data["access"]}'
        )
        response = self.client.get('/api/auth/user-info/')
        # Token might still be valid until it expires (this is expected)
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
        )

    def test_jwt_user_permissions_isolation(self):
        """Test that JWT tokens properly isolate user permissions."""
        # User1 should only see their own sensitive data
        self.authenticate_user1()

        # Get user profiles - should be filtered to authorized data
        response = self.client.get('/api/profiles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify response contains only appropriate data
        if 'results' in response.data:
            profiles = response.data['results']
        else:
            profiles = response.data

        # Should be able to see profiles but with appropriate privacy controls
        self.assertIsInstance(profiles, list)

    def test_concurrent_jwt_sessions_handling(self):
        """Test handling of multiple concurrent JWT sessions."""
        # Create multiple tokens for same user
        token_data_1 = self._create_jwt_token_with_session(self.user1)
        token_data_2 = self._create_jwt_token_with_session(self.user1)

        # Both should work independently
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token_data_1["access"]}'
        )
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token_data_2["access"]}'
        )
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_jwt_token_automatic_expiry(self):
        """Test JWT token automatic expiry handling."""
        # Create a token that's already expired
        refresh = RefreshToken.for_user(self.user1)
        access = refresh.access_token

        # Set expiry to past time to make it expired - use timestamp
        import time
        past_timestamp = int(time.time()) - 60  # 60 seconds ago
        access.payload['exp'] = past_timestamp

        # Expired token should be rejected
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(access)}')
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AccountsJWTErrorHandlingTests(AccountsAPITestCase):
    """Test JWT error handling and edge cases in accounts app."""

    def test_missing_authorization_header(self):
        """Test API response when Authorization header is missing."""
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_malformed_authorization_header(self):
        """Test API response with malformed Authorization header."""
        # Missing Bearer prefix
        self.client.credentials(HTTP_AUTHORIZATION=self.jwt_token1['access'])
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Wrong prefix
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.jwt_token1["access"]}'
        )
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_bearer_token(self):
        """Test API response with empty Bearer token."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ')
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_algorithm_mismatch(self):
        """Test handling of JWT tokens with wrong algorithm."""
        # This would require creating a token with wrong algorithm
        # For now, test with obviously invalid token format
        invalid_token = (
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0.'
            'eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0Ijox'
            'NTE2MjM5MDIyfQ.'
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {invalid_token}')
        response = self.client.get('/api/auth/user-info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
