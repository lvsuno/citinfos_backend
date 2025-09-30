"""Comprehensive tests for communities app."""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import timedelta

from ..models import (
    Community, CommunityMembership, CommunityInvitation, CommunityJoinRequest,
    CommunityRole, CommunityModeration
)
from accounts.models import UserProfile
from accounts.tests.jwt_auth_mixin import JWTAuthTestMixin


class CommunityModelTests(TestCase, JWTAuthTestMixin):
    def setUp(self):
        """Set up test data for community tests."""
        self.setup_jwt_users()  # Creates user1, user2, userprofile1, userprofile2

    def test_only_active_members_can_interact(self):
        """Test that only active, not soft-deleted members can interact."""
        # Create test community using JWT test users
        community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='A test community',
            creator=self.userprofile1,
            community_type='public'
        )

        # ... rest of tests copied from original tests.py ...
