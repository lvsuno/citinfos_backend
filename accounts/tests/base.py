"""Base test classes for accounts app tests with JWT authentication."""

from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from accounts.models import UserProfile
from core.jwt_test_mixin import JWTAuthTestMixin
from core.models import Country, AdministrativeDivision


class AccountsAPITestCase(JWTAuthTestMixin, APITestCase):
    """Base test case for accounts API tests with JWT authentication."""

    def setUp(self):
        """Set up test data for accounts API tests."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User1'
        )
        # Ensure profile exists (a post_save signal may auto-create it)
        self.user1_profile, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            role='normal',
            bio='Test bio for user1',
            phone_number='+1234567890',
            date_of_birth='1990-01-01',
            is_verified=True,
        )
        self.user1_profile.refresh_from_db()

        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User2'
        )
        self.user2_profile, _ = UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.filter(user=self.user2).update(
            role='normal',
            bio='Test bio for user2',
            phone_number='+1234567891',
            date_of_birth='1991-01-01',
            is_verified=True,
        )
        self.user2_profile.refresh_from_db()

        # JWT tokens for new authentication flow
        self.jwt_token1 = self._create_jwt_token_with_session(self.user1)
        self.jwt_token2 = self._create_jwt_token_with_session(self.user2)

        # Create test country and division for location tests
        self.country = Country.objects.create(
            name='Test Country',
            iso2='TC',
            iso3='TCT'
        )
        self.test_division = AdministrativeDivision.objects.create(
            name='Test Division',
            country=self.country,
            admin_level=3  # Municipality level
        )

    def authenticate_user1(self):
        """Authenticate as user1 using JWT."""
        token_data = self.authenticate(self.jwt_token1)
        # Store access token for tests that need it directly
        self.access_token = token_data['access']
        return token_data

    def authenticate_user2(self):
        """Authenticate as user2 using JWT."""
        token_data = self.authenticate(self.jwt_token2)
        # Store access token for tests that need it directly
        self.access_token = token_data['access']
        return token_data
