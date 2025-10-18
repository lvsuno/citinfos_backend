"""Comprehensive API tests for all accounts app views and actions."""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from accounts.models import UserProfile, UserSession, UserEvent
from core.jwt_test_mixin import JWTAuthTestMixin


class AccountsComprehensiveAPITests(JWTAuthTestMixin, APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='apitest',
            password='TestPass123!'
        )
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            phone_number='+1999000001',
            date_of_birth='1990-01-01'
        )
        self.profile.refresh_from_db()

        # Set up JWT authentication
        self.jwt_token = self._create_jwt_token_with_session(self.user)
        self.authenticate(self.jwt_token)

        # Create session with required fields
        self.session = UserSession.objects.create(
            user=self.profile,
            session_id='sess1',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        self.event = UserEvent.objects.create(
            user=self.profile,
            event_type='login'
        )

    def test_user_session_active(self):
        url = reverse('session-active')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_session_by_device(self):
        url = reverse('session-by-device')
        response = self.client.get(url, {'device_type': 'desktop'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_user_session_statistics(self):
        url = reverse('session-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_session_current_sessions(self):
        url = reverse('session-current-sessions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_session_clear_all(self):
        url = reverse('session-clear-all-sessions')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_event_by_type(self):
        url = reverse('event-by-type')
        response = self.client.get(url, {'event_type': 'login'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_user_event_by_category(self):
        url = reverse('event-by-category')
        response = self.client.get(url, {'category': 'auth'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_user_event_timeline(self):
        url = reverse('event-timeline')
        response = self.client.get(url, {'days': 7})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_user_event_summary(self):
        url = reverse('event-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_event_user_activity(self):
        url = reverse('event-user-activity')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_event_event_types(self):
        url = reverse('event-event-types')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
