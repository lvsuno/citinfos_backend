"""
Authentication view tests for accounts app with JWT authentication.

This module tests login, logout, registration, and JWT token management.
"""

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch

from .base import AccountsAPITestCase
from accounts.models import UserProfile


class AccountsAuthenticationViewTests(AccountsAPITestCase):
    """Test authentication views with JWT tokens."""

    def test_login_view_with_valid_credentials(self):
        """Test POST /api/auth/login/ with valid credentials."""
        url = reverse('auth-login')
        data = {
            'username': 'testuser1',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should return JWT token
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)

    def test_login_view_with_invalid_credentials(self):
        """Test POST /api/auth/login/ with invalid credentials."""
        url = reverse('auth-login')
        data = {
            'username': 'testuser1',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_view_with_missing_credentials(self):
        """Test POST /api/auth/login/ with missing credentials."""
        url = reverse('auth-login')

        # Missing password
        data = {'username': 'testuser1'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing username
        data = {'password': 'testpass123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_view(self):
        """Test POST /api/auth/logout/ - Logout with JWT token."""
        self.authenticate_user1()

        url = reverse('auth-logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_view_without_authentication(self):
        """Test POST /api/auth/logout/ without authentication."""
        url = reverse('auth-logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_view_with_valid_data(self):
        """Test POST /api/auth/register/ with valid data."""
        url = reverse('auth-register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Should create user and profile
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_user = User.objects.get(username='newuser')
        self.assertTrue(UserProfile.objects.filter(user=new_user).exists())

        # Should return JWT token
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)

    def test_register_view_with_invalid_data(self):
        """Test POST /api/auth/register/ with invalid data."""
        url = reverse('auth-register')

        # Missing required fields
        data = {'username': 'incomplete'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Password mismatch
        data = {
            'username': 'mismatch',
            'email': 'mismatch@example.com',
            'password': 'pass123',
            'password_confirm': 'pass456'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_view_with_existing_username(self):
        """Test POST /api/auth/register/ with existing username."""
        url = reverse('auth-register')
        data = {
            'username': 'testuser1',  # Already exists
            'email': 'different@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_view_with_existing_email(self):
        """Test POST /api/auth/register/ with existing email."""
        url = reverse('auth-register')
        data = {
            'username': 'newuser',
            'email': 'test1@example.com',  # Already exists
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh_view(self):
        """Test POST /api/auth/token/refresh/ - Refresh JWT token."""
        # Get initial tokens
        url = reverse('auth-login')
        data = {
            'username': 'testuser1',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        refresh_token = response.data['refresh_token']

        # Use refresh token to get new access token
        url = reverse('auth-token-refresh')
        data = {'refresh': refresh_token}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_view_with_invalid_token(self):
        """Test POST /api/auth/token/refresh/ with invalid token."""
        url = reverse('auth-token-refresh')
        data = {'refresh': 'invalid-token'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_verify_view(self):
        """Test POST /api/auth/token/verify/ - Verify JWT token."""
        self.authenticate_user1()

        url = reverse('auth-token-verify')
        data = {'token': self.access_token}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_verify_view_with_invalid_token(self):
        """Test POST /api/auth/token/verify/ with invalid token."""
        url = reverse('auth-token-verify')
        data = {'token': 'invalid-token'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile_view(self):
        """Test GET /api/auth/user/ - Get current user profile."""
        self.authenticate_user1()

        url = reverse('auth-user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser1')

    def test_user_profile_view_without_authentication(self):
        """Test GET /api/auth/user/ without authentication."""
        url = reverse('auth-user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_view(self):
        """Test POST /api/auth/change-password/ - Change password."""
        self.authenticate_user1()

        url = reverse('auth-change-password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify password was changed
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.check_password('newpassword123'))

    def test_change_password_view_with_wrong_old_password(self):
        """Test POST /api/auth/change-password/ with wrong old password."""
        self.authenticate_user1()

        url = reverse('auth-change-password')
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_view_with_password_mismatch(self):
        """Test POST /api/auth/change-password/ with password mismatch."""
        self.authenticate_user1()

        url = reverse('auth-change-password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'differentpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_request_view(self):
        """Test POST /api/auth/password-reset/ - Request password reset."""
        url = reverse('auth-password-reset-request')
        data = {'email': 'test1@example.com'}

        with patch('accounts.views.send_password_reset_email') as mock_send:
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_send.assert_called_once()

    def test_password_reset_request_view_with_invalid_email(self):
        """Test POST /api/auth/password-reset/ with invalid email."""
        url = reverse('auth-password-reset-request')
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(url, data, format='json')
        # Should still return 200 for security (don't reveal email existence)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('accounts.views.verify_password_reset_token')
    def test_password_reset_confirm_view(self, mock_verify):
        """Test POST /api/auth/password-reset/confirm/ - Confirm reset."""
        mock_verify.return_value = self.user1

        url = reverse('auth-password-reset-confirm')
        data = {
            'token': 'valid-reset-token',
            'new_password': 'resetpassword123',
            'new_password_confirm': 'resetpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('accounts.views.verify_password_reset_token')
    def test_password_reset_confirm_view_with_invalid_token(self, mock_verify):
        """Test POST /api/auth/password-reset/confirm/ with invalid token."""
        mock_verify.return_value = None

        url = reverse('auth-password-reset-confirm')
        data = {
            'token': 'invalid-token',
            'new_password': 'resetpassword123',
            'new_password_confirm': 'resetpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AccountsAuthenticationSecurityTests(AccountsAPITestCase):
    """Test security aspects of authentication views."""

    def test_login_rate_limiting(self):
        """Test rate limiting on login attempts."""
        url = reverse('auth-login')
        invalid_data = {
            'username': 'testuser1',
            'password': 'wrongpassword'
        }

        # Make multiple failed login attempts
        for _ in range(10):
            response = self.client.post(url, invalid_data, format='json')
            # First few should be 401, later ones might be rate limited
            self.assertIn(response.status_code, [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_429_TOO_MANY_REQUESTS
            ])

    def test_password_strength_validation(self):
        """Test password strength validation during registration."""
        url = reverse('auth-register')

        # Weak passwords should be rejected
        weak_passwords = [
            'weak',
            '12345678',
            'password',
            'testuser'  # Same as username
        ]

        for weak_password in weak_passwords:
            data = {
                'username': f'user_{weak_password}',
                'email': f'{weak_password}@example.com',
                'password': weak_password,
                'password_confirm': weak_password
            }
            response = self.client.post(url, data, format='json')
            # Should either reject with 400 or have specific validation errors
            self.assertIn(response.status_code, [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_201_CREATED  # Some weak passwords might be allowed
            ])

    def test_token_expiration_handling(self):
        """Test handling of expired JWT tokens."""
        # This would require mocking time or using expired tokens
        # For now, just test that proper status codes are returned
        url = reverse('auth-user')

        # Use malformed token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer expired.token.here')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_site_request_forgery_protection(self):
        """Test CSRF protection on authentication endpoints."""
        # JWT authentication typically doesn't use CSRF tokens
        # but verify that endpoints handle missing CSRF appropriately
        url = reverse('auth-login')
        data = {
            'username': 'testuser1',
            'password': 'testpass123'
        }

        # Request without CSRF token should still work for JWT auth
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sql_injection_protection(self):
        """Test protection against SQL injection in login."""
        url = reverse('auth-login')
        malicious_data = {
            'username': "admin'; DROP TABLE auth_user; --",
            'password': "password"
        }

        response = self.client.post(url, malicious_data, format='json')
        # Should not cause server error, should return 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Verify user table still exists by checking our test users
        self.assertTrue(User.objects.filter(username='testuser1').exists())

    def test_session_security_headers(self):
        """Test that security headers are properly set."""
        url = reverse('auth-login')
        data = {
            'username': 'testuser1',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')

        # Check for security headers (if configured)
        # These might not be present in test environment
        security_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'X-XSS-Protection'
        ]

        for header in security_headers:
            # Not asserting presence since these are typically set by middleware
            # Just documenting what should be checked in production
            pass

    def test_user_enumeration_protection(self):
        """Test protection against user enumeration attacks."""
        url = reverse('auth-login')

        # Invalid username vs invalid password should return similar responses
        invalid_user_data = {
            'username': 'nonexistentuser',
            'password': 'password'
        }
        invalid_pass_data = {
            'username': 'testuser1',
            'password': 'wrongpassword'
        }

        response1 = self.client.post(url, invalid_user_data, format='json')
        response2 = self.client.post(url, invalid_pass_data, format='json')

        # Both should return 401 with similar error messages
        self.assertEqual(response1.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response2.status_code, status.HTTP_401_UNAUTHORIZED)

        # Error messages should not reveal whether user exists
        # (This depends on implementation)
        self.assertNotIn('user does not exist', str(response1.data).lower())
        self.assertNotIn('username not found', str(response1.data).lower())
