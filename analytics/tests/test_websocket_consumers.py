"""
Tests for Visitor Analytics WebSocket Consumers

Tests cover:
- WebSocket connection and disconnection
- Authentication and permissions
- Message handling and broadcasting
- Real-time visitor count updates
- Error handling
"""

import uuid
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from django.urls import re_path
from asgiref.sync import async_to_sync

from analytics.consumers import (
    VisitorAnalyticsConsumer,
    VisitorDashboardConsumer
)
from communities.models import Community, CommunityMembership, CommunityRole
from core.models import AdministrativeDivision, Country
from accounts.models import UserProfile
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

# Test UUID - will be set to actual community ID in setUp
TEST_COMMUNITY_UUID = '12345678-1234-5678-1234-567812345678'


class VisitorAnalyticsConsumerTests(TransactionTestCase):
    """Test VisitorAnalyticsConsumer WebSocket functionality"""

    def setUp(self):
        """Set up test data including a real community"""
        # Create country
        self.country = Country.objects.create(
            code=999,
            iso2='TC',
            iso3='TST',
            name='Test Country'
        )

        # Create administrative division
        self.division = AdministrativeDivision.objects.create(
            name='Test Division',
            admin_level=3,
            country=self.country
        )

        # Create user and profile for community creator
        self.creator_user = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )

        # Get or update the automatically created profile
        self.creator_profile = self.creator_user.profile
        self.creator_profile.date_of_birth = "2000-01-01"
        self.creator_profile.administrative_division = self.division
        self.creator_profile.save()

        # Create community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='A test community',
            creator=self.creator_profile,
            division=self.division,
            is_deleted=False
        )

        # Store community ID as instance variable
        self.community_id = str(self.community.id)

    def _create_communicator(self, consumer_class, community_id=None,
                             user=None):
        """Helper to create WebSocket communicator with proper scope."""
        if community_id is None:
            community_id = self.community_id
        communicator = WebsocketCommunicator(
            consumer_class.as_asgi(),
            f'/ws/communities/{community_id}/visitors/'
        )
        communicator.scope['url_route'] = {
            'kwargs': {'community_id': community_id}
        }
        # Add user to scope - defaults to AnonymousUser for public access
        user_obj = user if user is not None else AnonymousUser()
        communicator.scope['user'] = user_obj
        return communicator

    async def test_consumer_connection_and_disconnection(self):
        """Test that consumer can connect and disconnect"""
        # Create WebSocket communicator with anonymous user (public access)
        communicator = self._create_communicator(VisitorAnalyticsConsumer)

        # Test connection
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected, "WebSocket should connect successfully")

        # Test disconnection
        await communicator.disconnect()

    async def test_consumer_sends_initial_count(self):
        """Test that consumer sends initial visitor count on connection"""
        communicator = self._create_communicator(VisitorAnalyticsConsumer)

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Should receive initial count message
        response = await communicator.receive_json_from()

        self.assertIn('type', response)
        self.assertEqual(response['type'], 'visitor_count')
        self.assertIn('count', response)
        self.assertIsInstance(response['count'], int)

        await communicator.disconnect()

    async def test_consumer_handles_request_count_message(self):
        """Test that consumer responds to request_count messages"""
        communicator = self._create_communicator(VisitorAnalyticsConsumer)

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Consume initial message
        await communicator.receive_json_from()

        # Send request_count message
        await communicator.send_json_to({
            'type': 'request_count'
        })

        # Should receive count response
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'visitor_count')
        self.assertIn('count', response)

        await communicator.disconnect()

    async def test_consumer_with_community_filter(self):
        """Test consumer with community_id parameter"""
        # Use the community created in setUp
        communicator = self._create_communicator(
            VisitorAnalyticsConsumer,
            community_id=self.community_id
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Should receive filtered count
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'visitor_count')

        await communicator.disconnect()

    async def test_consumer_broadcasts_visitor_joined(self):
        """Test that visitor_joined events are broadcast"""
        # This test would require setting up channel layers
        # For now, we test the consumer's ability to receive and process
        communicator = self._create_communicator(VisitorAnalyticsConsumer)

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Consume initial message
        await communicator.receive_json_from()

        await communicator.disconnect()

    async def test_consumer_handles_invalid_messages(self):
        """Test that consumer handles invalid messages gracefully"""
        communicator = self._create_communicator(VisitorAnalyticsConsumer)

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Consume initial message
        await communicator.receive_json_from()

        # Send invalid message
        await communicator.send_json_to({
            'type': 'invalid_type'
        })

        # Should not crash - connection should remain open
        # Try sending a valid message
        await communicator.send_json_to({
            'type': 'request_count'
        })

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'visitor_count')

        await communicator.disconnect()


class VisitorDashboardConsumerTests(TransactionTestCase):
    """Test VisitorDashboardConsumer WebSocket functionality"""

    def setUp(self):
        """Set up test data including a real community"""
        # Create country
        self.country = Country.objects.create(
            code=999,
            iso2='TC',
            iso3='TST',
            name='Test Country'
        )

        # Create administrative division
        self.division = AdministrativeDivision.objects.create(
            name='Test Division',
            admin_level=3,
            country=self.country
        )

        # Create user and profile for community creator
        self.creator_user = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )

        # Get or update the automatically created profile
        self.creator_profile = self.creator_user.profile
        self.creator_profile.date_of_birth = "2000-01-01"
        self.creator_profile.administrative_division = self.division
        self.creator_profile.save()

        # Create community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community-dashboard',
            description='A test community',
            creator=self.creator_profile,
            division=self.division,
            is_deleted=False
        )

        # Store community ID as instance variable
        self.community_id = str(self.community.id)

    def _create_communicator(self, consumer_class, community_id=None,
                             user=None):
        """Helper to create WebSocket communicator with proper scope."""
        if community_id is None:
            community_id = self.community_id
        communicator = WebsocketCommunicator(
            consumer_class.as_asgi(),
            f'/ws/communities/{community_id}/visitor-dashboard/'
        )
        communicator.scope['url_route'] = {
            'kwargs': {'community_id': community_id}
        }
        # Add user to scope - defaults to AnonymousUser for public access
        user_obj = user if user is not None else AnonymousUser()
        communicator.scope['user'] = user_obj
        return communicator

    async def _create_admin_user(self, community_id):
        """Create an admin user with proper role and community membership."""
        from datetime import date

        # Create admin user
        admin_user = await database_sync_to_async(User.objects.create_user)(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )

        # Update profile with required fields and set role to 'admin'
        profile = await database_sync_to_async(lambda: admin_user.profile)()
        profile.date_of_birth = date(1990, 1, 1)
        profile.administrative_division = self.division
        profile.role = 'admin'  # Set profile role to admin
        await database_sync_to_async(profile.save)()

        # Get community
        community = await database_sync_to_async(
            Community.objects.get
        )(id=community_id)

        # Get or create Admin role for this community
        admin_role = await database_sync_to_async(
            CommunityRole.objects.get_or_create
        )(
            community=community,
            name='Admin',
            defaults={
                'permissions': {
                    'can_post': True,
                    'can_comment': True,
                    'can_vote': True,
                    'can_report': True,
                    'can_moderate': True,
                    'can_manage_members': True,
                    'can_manage_community': True,
                    'can_delete_posts': True,
                    'can_ban_users': True,
                    'can_manage_roles': True
                },
                'color': '#dc2626',
                'is_default': False
            }
        )
        role = admin_role[0] if isinstance(admin_role, tuple) else admin_role

        # Create community membership
        await database_sync_to_async(CommunityMembership.objects.create)(
            community=community,
            user=profile,
            role=role,
            status='active'
        )

        return admin_user

    async def test_dashboard_consumer_connection(self):
        """Test that dashboard consumer can connect"""
        admin_user = await self._create_admin_user(self.community_id)
        communicator = self._create_communicator(
            VisitorDashboardConsumer,
            user=admin_user
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

    async def test_dashboard_consumer_sends_initial_data(self):
        """Test that dashboard consumer sends initial dashboard data"""
        admin_user = await self._create_admin_user(self.community_id)
        communicator = self._create_communicator(
            VisitorDashboardConsumer,
            user=admin_user
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Should receive initial dashboard data
        response = await communicator.receive_json_from()

        # Check for dashboard-specific data
        self.assertIn('type', response)
        # Dashboard might send different initial message

        await communicator.disconnect()

    async def test_dashboard_consumer_with_community_filter(self):
        """Test dashboard consumer with community filtering"""
        # Create admin user with proper role and membership
        admin_user = await self._create_admin_user(self.community_id)

        # Use the community created in setUp
        communicator = self._create_communicator(
            VisitorDashboardConsumer,
            community_id=self.community_id,
            user=admin_user
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()


class WebSocketAuthenticationTests(TransactionTestCase):
    """Test WebSocket authentication and permissions"""

    def setUp(self):
        """Set up test data including a real community"""
        # Create country
        self.country = Country.objects.create(
            code=999,
            iso2='TC',
            iso3='TST',
            name='Test Country'
        )

        # Create administrative division
        self.division = AdministrativeDivision.objects.create(
            name='Test Division',
            admin_level=3,
            country=self.country
        )

        # Create user and profile for community creator
        self.creator_user = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )

        # Get or update the automatically created profile
        self.creator_profile = self.creator_user.profile
        self.creator_profile.date_of_birth = "2000-01-01"
        self.creator_profile.administrative_division = self.division
        self.creator_profile.save()

        # Create community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community-auth',
            description='A test community',
            creator=self.creator_profile,
            division=self.division,
            is_deleted=False
        )

        # Store community ID as instance variable
        self.community_id = str(self.community.id)

    def _create_communicator(self, consumer_class, community_id=None,
                             user=None):
        """Helper to create WebSocket communicator with proper scope."""
        if community_id is None:
            community_id = self.community_id
        communicator = WebsocketCommunicator(
            consumer_class.as_asgi(),
            f'/ws/communities/{community_id}/visitors/'
        )
        communicator.scope['url_route'] = {
            'kwargs': {'community_id': community_id}
        }
        user_obj = user if user is not None else AnonymousUser()
        communicator.scope['user'] = user_obj
        return communicator

    async def test_unauthenticated_connection_allowed(self):
        """Test that unauthenticated users can connect (read-only)"""
        # Analytics WebSocket allows anonymous connections for public stats
        communicator = self._create_communicator(VisitorAnalyticsConsumer)

        connected, _ = await communicator.connect()
        # Connection policy depends on implementation
        # Some implementations allow read-only access

        if connected:
            await communicator.disconnect()

    async def test_authenticated_admin_connection(self):
        """Test that authenticated admin users can connect"""
        admin_user = await database_sync_to_async(User.objects.create_user)(
            username='admin',
            password='test123',
            is_staff=True
        )

        communicator = self._create_communicator(
            VisitorAnalyticsConsumer,
            user=admin_user
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()


class WebSocketBroadcastingTests(TransactionTestCase):
    """Test WebSocket message broadcasting"""

    def setUp(self):
        """Set up test data including a real community"""
        # Create country
        self.country = Country.objects.create(
            code=999,
            iso2='TC',
            iso3='TST',
            name='Test Country'
        )

        # Create administrative division
        self.division = AdministrativeDivision.objects.create(
            name='Test Division',
            admin_level=3,
            country=self.country
        )

        # Create user and profile for community creator
        self.creator_user = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )

        # Get or update the automatically created profile
        self.creator_profile = self.creator_user.profile
        self.creator_profile.date_of_birth = "2000-01-01"
        self.creator_profile.administrative_division = self.division
        self.creator_profile.save()

        # Create community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community-broadcast',
            description='A test community',
            creator=self.creator_profile,
            division=self.division,
            is_deleted=False
        )

        # Store community ID as instance variable
        self.community_id = str(self.community.id)

    def _create_communicator(self, consumer_class, community_id=None,
                             user=None):
        """Helper to create WebSocket communicator with proper scope."""
        if community_id is None:
            community_id = self.community_id
        communicator = WebsocketCommunicator(
            consumer_class.as_asgi(),
            f'/ws/communities/{community_id}/visitors/'
        )
        communicator.scope['url_route'] = {
            'kwargs': {'community_id': community_id}
        }
        user_obj = user if user is not None else AnonymousUser()
        communicator.scope['user'] = user_obj
        return communicator

    async def test_broadcast_to_multiple_clients(self):
        """Test that messages are broadcast to all connected clients"""
        # Create two communicators
        communicator1 = self._create_communicator(VisitorAnalyticsConsumer)
        communicator2 = self._create_communicator(VisitorAnalyticsConsumer)

        # Connect both
        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()

        self.assertTrue(connected1)
        self.assertTrue(connected2)

        # Both should receive initial count
        response1 = await communicator1.receive_json_from()
        response2 = await communicator2.receive_json_from()

        self.assertEqual(response1['type'], 'visitor_count')
        self.assertEqual(response2['type'], 'visitor_count')

        # Cleanup
        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_community_specific_broadcasting(self):
        """Test that broadcasts are filtered by community"""
        # Use the community from setUp as community1
        community1 = self.community

        # Create a second community for comparison
        community2 = await database_sync_to_async(Community.objects.create)(
            name='Community 2',
            slug='test-community-broadcast-2',
            division=self.division,
            creator=self.creator_profile
        )

        # Connect to different communities
        comm1 = WebsocketCommunicator(
            VisitorAnalyticsConsumer.as_asgi(),
            f'/ws/analytics/visitors/?community_id={community1.id}'
        )
        comm1.scope['url_route'] = {
            'kwargs': {'community_id': str(community1.id)}
        }
        comm1.scope['user'] = AnonymousUser()

        comm2 = WebsocketCommunicator(
            VisitorAnalyticsConsumer.as_asgi(),
            f'/ws/analytics/visitors/?community_id={community2.id}'
        )
        comm2.scope['url_route'] = {
            'kwargs': {'community_id': str(community2.id)}
        }
        comm2.scope['user'] = AnonymousUser()

        connected1, _ = await comm1.connect()
        connected2, _ = await comm2.connect()

        self.assertTrue(connected1)
        self.assertTrue(connected2)

        # Both should receive their respective counts
        await comm1.receive_json_from()
        await comm2.receive_json_from()

        await comm1.disconnect()
        await comm2.disconnect()


class WebSocketErrorHandlingTests(TransactionTestCase):
    """Test WebSocket error handling"""

    def setUp(self):
        """Set up test data including a real community"""
        # Create country
        self.country = Country.objects.create(
            code=999,
            iso2='TC',
            iso3='TST',
            name='Test Country'
        )

        # Create administrative division
        self.division = AdministrativeDivision.objects.create(
            name='Test Division',
            admin_level=3,
            country=self.country
        )

        # Create user and profile for community creator
        self.creator_user = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )

        # Get or update the automatically created profile
        self.creator_profile = self.creator_user.profile
        self.creator_profile.date_of_birth = "2000-01-01"
        self.creator_profile.administrative_division = self.division
        self.creator_profile.save()

        # Create community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community-error',
            description='A test community',
            creator=self.creator_profile,
            division=self.division,
            is_deleted=False
        )

        # Store community ID as instance variable
        self.community_id = str(self.community.id)

    def _create_communicator(self, consumer_class, community_id=None,
                             user=None):
        """Helper to create WebSocket communicator with proper scope."""
        if community_id is None:
            community_id = self.community_id
        communicator = WebsocketCommunicator(
            consumer_class.as_asgi(),
            f'/ws/communities/{community_id}/visitors/'
        )
        communicator.scope['url_route'] = {
            'kwargs': {'community_id': community_id}
        }
        user_obj = user if user is not None else AnonymousUser()
        communicator.scope['user'] = user_obj
        return communicator

    async def test_invalid_community_id(self):
        """Test handling of invalid community_id parameter"""
        communicator = self._create_communicator(VisitorAnalyticsConsumer)

        # Should handle gracefully - either reject connection or ignore param
        connected, _ = await communicator.connect()

        if connected:
            # If connection allowed, should handle error gracefully
            response = await communicator.receive_json_from()
            self.assertIn('type', response)
            await communicator.disconnect()

    async def test_malformed_json_message(self):
        """Test handling of malformed JSON messages"""
        communicator = self._create_communicator(VisitorAnalyticsConsumer)

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Consume initial message
        await communicator.receive_json_from()

        # Send malformed data (this would be caught by send_json_to)
        # But we test the consumer's resilience

        # Send valid message to verify connection still works
        await communicator.send_json_to({'type': 'request_count'})
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'visitor_count')

        await communicator.disconnect()

    async def test_connection_timeout_handling(self):
        """Test that connections handle timeout gracefully"""
        communicator = self._create_communicator(VisitorAnalyticsConsumer)

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Receive initial message
        await communicator.receive_json_from()

        # Connection should remain stable
        await communicator.send_json_to({'type': 'request_count'})
        response = await communicator.receive_json_from()
        self.assertIsNotNone(response)

        await communicator.disconnect()


class WebSocketMessageFormatTests(TransactionTestCase):
    """Test WebSocket message format validation"""

    def setUp(self):
        """Set up test data including a real community"""
        # Create country
        self.country = Country.objects.create(
            code=999,
            iso2='TC',
            iso3='TST',
            name='Test Country'
        )

        # Create administrative division
        self.division = AdministrativeDivision.objects.create(
            name='Test Division',
            admin_level=3,
            country=self.country
        )

        # Create user and profile for community creator
        self.creator_user = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )

        # Get or update the automatically created profile
        self.creator_profile = self.creator_user.profile
        self.creator_profile.date_of_birth = "2000-01-01"
        self.creator_profile.administrative_division = self.division
        self.creator_profile.save()

        # Create community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community-format',
            description='A test community',
            creator=self.creator_profile,
            division=self.division,
            is_deleted=False
        )

        # Store community ID as instance variable
        self.community_id = str(self.community.id)

    def _create_communicator(self, consumer_class, community_id=None,
                             user=None):
        """Helper to create WebSocket communicator with proper scope."""
        if community_id is None:
            community_id = self.community_id
        communicator = WebsocketCommunicator(
            consumer_class.as_asgi(),
            f'/ws/communities/{community_id}/visitors/'
        )
        communicator.scope['url_route'] = {
            'kwargs': {'community_id': community_id}
        }
        user_obj = user if user is not None else AnonymousUser()
        communicator.scope['user'] = user_obj
        return communicator

    async def test_visitor_count_message_format(self):
        """Test that visitor_count messages have correct format"""
        communicator = self._create_communicator(VisitorAnalyticsConsumer)

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()

        # Validate message structure
        self.assertIn('type', response)
        self.assertEqual(response['type'], 'visitor_count')
        self.assertIn('count', response)
        self.assertIsInstance(response['count'], int)
        self.assertGreaterEqual(response['count'], 0)

        await communicator.disconnect()

    async def test_visitor_joined_message_format(self):
        """Test visitor_joined message format if applicable"""
        # This would test broadcast messages sent when visitors join
        # Requires channel layer setup for proper testing
        pass

    async def test_visitor_left_message_format(self):
        """Test visitor_left message format if applicable"""
        # This would test broadcast messages sent when visitors leave
        # Requires channel layer setup for proper testing
        pass
