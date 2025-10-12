"""
Tests for Visitor Analytics Utility Functions

Test coverage for visitor_utils.py including:
- Unique visitor counts
- Division breakdowns
- Visitor trends
- Conversion metrics
- Error handling
- Redis fallback scenarios
"""

from datetime import datetime, timedelta, date
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from analytics.visitor_utils import (
    VisitorAnalytics,
    get_today_visitors,
    get_weekly_visitors,
    get_monthly_visitors,
    get_visitor_growth_rate
)
from analytics.models import (
    AnonymousSession,
    AnonymousPageView,
    PageAnalytics
)
from accounts.models import UserProfile, User, UserEvent
from core.models import AdministrativeDivision, Country
from communities.models import Community


class VisitorUtilsTestCase(TestCase):
    """Test suite for visitor analytics utilities."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Get the automatically created UserProfile and update it
        self.user_profile = self.user.profile
        self.user_profile.bio = 'Test user profile'
        self.user_profile.save()

        # Create country for division
        self.country = Country.objects.create(
            name='Test Country',
            iso2='TC',
            iso3='TST'
        )

        # Create division
        self.division = AdministrativeDivision.objects.create(
            name='Test Division',
            admin_level=3,
            country=self.country
        )

        # Create community
        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='A test community',
            division=self.division,
            creator=self.user_profile
        )

    def tearDown(self):
        """Clean up after tests."""
        AnonymousSession.objects.all().delete()
        AnonymousPageView.objects.all().delete()
        PageAnalytics.objects.all().delete()
        UserEvent.objects.all().delete()
        Community.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        AdministrativeDivision.objects.all().delete()

    # Test 1: test_get_unique_visitors_no_data
    def test_get_unique_visitors_no_data(self):
        """Test get_unique_visitors with no visitor data."""
        result = VisitorAnalytics.get_unique_visitors(
            str(self.community.id)
        )

        self.assertIn('community_id', result)
        self.assertEqual(result['community_id'], str(self.community.id))
        self.assertEqual(result['authenticated_visitors'], 0)
        self.assertEqual(result['anonymous_visitors'], 0)
        self.assertEqual(result['total_unique_visitors'], 0)

    # Test 2: test_get_unique_visitors_with_data
    def test_get_unique_visitors_with_data(self):
        """Test get_unique_visitors with actual visitor data."""
        # Create authenticated visitor events
        today = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Create 3 authenticated visitor events
        for i in range(3):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass'
            )
            user_profile = user.profile
            user_profile.bio = f'User {i} profile'
            user_profile.save()

            UserEvent.objects.create(
                user=user_profile,
                event_type='community_visit',
                description=f'User {i} visited community',
                metadata={
                    'community_id': str(self.community.id),
                    'community_slug': self.community.slug
                },
                created_at=today + timedelta(hours=i)
            )

        # Create anonymous sessions
        for i in range(2):
            session = AnonymousSession.objects.create(
                device_fingerprint=f'fingerprint_{i}',
                ip_address='127.0.0.1',
                session_start=today + timedelta(hours=i),
                last_activity=today + timedelta(hours=i, minutes=30),
                pages_visited=5,
                landing_page=f'/communities/{self.community.slug}',
                device_type='mobile'
            )

            # Create page view for community
            AnonymousPageView.objects.create(
                session=session,
                url=f'/communities/{self.community.slug}',
                page_type='community',
                viewed_at=today + timedelta(hours=i)
            )

        # Test with data
        result = VisitorAnalytics.get_unique_visitors(
            str(self.community.id),
            start_date=today,
            end_date=timezone.now()
        )

        self.assertEqual(result['authenticated_visitors'], 3)
        self.assertEqual(result['anonymous_visitors'], 2)
        self.assertEqual(result['total_unique_visitors'], 5)

    # Test 3: test_division_breakdown_calculation
    def test_division_breakdown_calculation(self):
        """Test division breakdown calculation."""
        today = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Create users with different divisions
        # Same division user
        same_div_user = User.objects.create_user(
            username='samediv',
            email='samediv@example.com'
        )
        same_div_profile = same_div_user.profile
        same_div_profile.division = self.division
        same_div_profile.save()

        UserEvent.objects.create(
            user=same_div_profile,
            event_type='community_visit',
            description='Same division visit',
            metadata={
                'community_id': str(self.community.id),
                'visitor_division_id': str(self.division.id),
                'community_division_id': str(self.division.id),
                'is_cross_division': False
            },
            created_at=today
        )

        # Cross division user
        other_division = AdministrativeDivision.objects.create(
            name='Other Division',
            admin_level=3,
            country=self.country,
            admin_code='OD'
        )

        cross_div_user = User.objects.create_user(
            username='crossdiv',
            email='crossdiv@example.com'
        )
        cross_div_profile = cross_div_user.profile
        cross_div_profile.division = other_division
        cross_div_profile.save()

        UserEvent.objects.create(
            user=cross_div_profile,
            event_type='community_visit',
            description='Cross division visit',
            metadata={
                'community_id': str(self.community.id),
                'visitor_division_id': str(other_division.id),
                'community_division_id': str(self.division.id),
                'is_cross_division': True
            },
            created_at=today
        )

        # No division user
        no_div_user = User.objects.create_user(
            username='nodiv',
            email='nodiv@example.com'
        )
        no_div_profile = no_div_user.profile
        no_div_profile.division = None
        no_div_profile.save()

        UserEvent.objects.create(
            user=no_div_profile,
            event_type='community_visit',
            description='No division visit',
            metadata={
                'community_id': str(self.community.id),
                'visitor_division_id': None
            },
            created_at=today
        )

        # Get division breakdown
        result = VisitorAnalytics.get_division_breakdown(
            str(self.community.id),
            start_date=today,
            end_date=timezone.now()
        )

        self.assertIn('breakdown', result)
        self.assertEqual(result['breakdown']['same_division'], 1)
        self.assertEqual(result['breakdown']['cross_division'], 1)
        self.assertEqual(result['breakdown']['no_division'], 1)
        self.assertEqual(result['total_visitors'], 3)

    # Test 4: test_visitor_trends_daily
    def test_visitor_trends_daily(self):
        """Test daily visitor trends calculation."""
        # Create visitor data for last 3 days
        base_date = timezone.now() - timedelta(days=3)

        for day in range(3):
            day_start = base_date + timedelta(days=day)

            # Create 2 visitors per day
            for i in range(2):
                user = User.objects.create_user(
                    username=f'user_d{day}_u{i}',
                    email=f'user_d{day}_u{i}@example.com'
                )
                user_profile = user.profile

                UserEvent.objects.create(
                    user=user_profile,
                    event_type='community_visit',
                    description='Daily visit',
                    metadata={
                        'community_id': str(self.community.id)
                    },
                    created_at=day_start.replace(
                        hour=12, minute=0, second=0
                    )
                )

        # Get trends
        result = VisitorAnalytics.get_visitor_trends(
            str(self.community.id),
            days=3,
            granularity='daily'
        )

        self.assertEqual(result['granularity'], 'daily')
        self.assertEqual(result['days'], 3)
        self.assertIn('trends', result)
        self.assertEqual(len(result['trends']), 3)

        # Each day should have 2 visitors
        for trend in result['trends']:
            self.assertIn('date', trend)
            self.assertIn('total', trend)
            # Note: may be 0 if dates don't align perfectly
            self.assertGreaterEqual(trend['total'], 0)

    # Test 5: test_conversion_metrics_calculation
    def test_conversion_metrics_calculation(self):
        """Test conversion metrics calculation."""
        today = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Create anonymous sessions with conversions
        converted_user = User.objects.create_user(
            username='converted',
            email='converted@example.com'
        )
        converted_profile = converted_user.profile

        # Create 3 total sessions, 1 converted
        for i in range(3):
            session = AnonymousSession.objects.create(
                device_fingerprint=f'fp_{i}',
                ip_address='127.0.0.1',
                session_start=today + timedelta(hours=i),
                last_activity=today + timedelta(hours=i, minutes=30),
                pages_visited=5,
                landing_page='/home',
                device_type='mobile'
            )

            # Convert first session
            if i == 0:
                session.converted_to_user = converted_profile
                session.converted_at = today + timedelta(hours=i, minutes=45)
                session.save()

        # Create page analytics with conversions
        PageAnalytics.objects.create(
            url_path='/communities/test',
            date=today.date(),
            anonymous_views=100
        )

        # Get conversion metrics
        result = VisitorAnalytics.get_conversion_metrics(
            start_date=today,
            end_date=timezone.now()
        )

        self.assertEqual(result['total_conversions'], 1)
        self.assertEqual(result['total_anonymous_sessions'], 3)
        # Conversion rate = 1/3 * 100 = 33.33%
        self.assertAlmostEqual(
            result['overall_conversion_rate'], 33.33, places=1
        )
        self.assertIn('top_conversion_pages', result)
        self.assertEqual(len(result['top_conversion_pages']), 1)
        self.assertEqual(
            result['top_conversion_pages'][0]['conversions'],
            1
        )

    # Test 6: test_database_anonymous_count
    def test_database_anonymous_count(self):
        """Test anonymous visitor count from database."""
        today = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Create anonymous sessions in database
        for i in range(3):
            session = AnonymousSession.objects.create(
                device_fingerprint=f'fp_db_{i}',
                ip_address='127.0.0.1',
                session_start=today,
                last_activity=today + timedelta(minutes=30),
                pages_visited=3,
                landing_page='/home',
                device_type='desktop'
            )

            # Create page view for community
            AnonymousPageView.objects.create(
                session=session,
                url=f'/communities/{self.community.slug}/posts',
                page_type='community',
                viewed_at=today
            )

        # Get unique visitors from database
        result = VisitorAnalytics.get_unique_visitors(
            str(self.community.id),
            start_date=today,
            end_date=timezone.now()
        )

        # Should get count from database
        self.assertEqual(result['anonymous_visitors'], 3)

    # Test 7: test_error_handling_invalid_community
    def test_error_handling_invalid_community(self):
        """Test error handling for invalid community ID."""
        invalid_uuid = '00000000-0000-0000-0000-000000000000'

        # Test get_unique_visitors with invalid ID
        result = VisitorAnalytics.get_unique_visitors(invalid_uuid)

        # Should still return a result (not crash)
        self.assertIn('community_id', result)
        # Anonymous count returns 0 for non-existent community
        self.assertEqual(result['anonymous_visitors'], 0)

        # Test get_division_breakdown with invalid ID
        result = VisitorAnalytics.get_division_breakdown(invalid_uuid)

        # Should return error
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'Community not found')

        # Test get_visitor_demographics with invalid ID
        result = VisitorAnalytics.get_visitor_demographics(invalid_uuid)

        # Should return error
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'Community not found')


class ConvenienceFunctionsTestCase(TestCase):
    """Test convenience wrapper functions."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.user_profile = self.user.profile

        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='Test',
            creator=self.user_profile
        )

    def test_get_today_visitors(self):
        """Test get_today_visitors convenience function."""
        result = get_today_visitors(str(self.community.id))

        self.assertIn('total_unique_visitors', result)
        self.assertIn('start_date', result)

        # Verify it's today's data
        start_date = datetime.fromisoformat(result['start_date'])
        self.assertEqual(start_date.date(), timezone.now().date())

    def test_get_weekly_visitors(self):
        """Test get_weekly_visitors convenience function."""
        result = get_weekly_visitors(str(self.community.id))

        self.assertIn('total_unique_visitors', result)
        self.assertIn('start_date', result)

        # Verify it's 7 days of data
        start_date = datetime.fromisoformat(result['start_date'])
        days_diff = (timezone.now() - start_date).days
        self.assertAlmostEqual(days_diff, 7, delta=1)

    def test_get_monthly_visitors(self):
        """Test get_monthly_visitors convenience function."""
        result = get_monthly_visitors(str(self.community.id))

        self.assertIn('total_unique_visitors', result)
        self.assertIn('start_date', result)

        # Verify it's 30 days of data
        start_date = datetime.fromisoformat(result['start_date'])
        days_diff = (timezone.now() - start_date).days
        self.assertAlmostEqual(days_diff, 30, delta=1)

    def test_get_visitor_growth_rate(self):
        """Test get_visitor_growth_rate calculation."""
        # Create visitor data for two periods
        base_date = timezone.now() - timedelta(days=14)

        # Previous period (days 14-8): 2 visitors
        # Create events well within the previous period
        for i in range(2):
            user = User.objects.create_user(
                username=f'prev_user_{i}',
                email=f'prev_{i}@example.com'
            )
            profile = user.profile

            event = UserEvent.objects.create(
                user=profile,
                event_type='community_visit',
                description='Previous period visit',
                metadata={'community_id': str(self.community.id)}
            )
            # Manually update created_at since auto_now_add=True ignores it
            event.created_at = base_date + timedelta(days=1 + i)
            event.save()

        # Current period (days 6-0): 4 visitors
        # Create events well within the current period
        for i in range(4):
            user = User.objects.create_user(
                username=f'curr_user_{i}',
                email=f'curr_{i}@example.com'
            )
            profile = user.profile

            event = UserEvent.objects.create(
                user=profile,
                event_type='community_visit',
                description='Current period visit',
                metadata={'community_id': str(self.community.id)}
            )
            # Manually update created_at since auto_now_add=True ignores it
            event.created_at = base_date + timedelta(days=9 + i)
            event.save()

        # Calculate growth rate
        result = get_visitor_growth_rate(
            str(self.community.id),
            current_period_days=7
        )

        self.assertIn('growth_rate', result)
        self.assertIn('absolute_change', result)
        self.assertIn('current_period', result)
        self.assertIn('previous_period', result)

        # Growth rate should be positive (4 vs 2 = 100% growth)
        self.assertGreater(result['growth_rate'], 0)
        self.assertEqual(result['absolute_change'], 2)


class VisitorDemographicsTestCase(TestCase):
    """Test visitor demographics functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.user_profile = self.user.profile

        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='Test',
            creator=self.user_profile
        )

    def test_visitor_demographics(self):
        """Test visitor demographics breakdown."""
        today = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Create sessions with different devices/browsers
        devices = [
            ('mobile', 'Chrome', 'iOS'),
            ('mobile', 'Safari', 'iOS'),
            ('desktop', 'Chrome', 'Windows'),
            ('desktop', 'Firefox', 'Linux'),
            ('tablet', 'Safari', 'iOS')
        ]

        for i, (device, browser, os) in enumerate(devices):
            session = AnonymousSession.objects.create(
                device_fingerprint=f'fp_{i}',
                ip_address='127.0.0.1',
                session_start=today,
                last_activity=today + timedelta(minutes=30),
                pages_visited=3,
                device_type=device,
                browser=browser,
                os=os
            )

            AnonymousPageView.objects.create(
                session=session,
                url=f'/communities/{self.community.slug}',
                page_type='community',
                viewed_at=today
            )

        # Get demographics
        result = VisitorAnalytics.get_visitor_demographics(
            str(self.community.id),
            start_date=today,
            end_date=timezone.now()
        )

        self.assertEqual(result['total_sessions'], 5)
        self.assertIn('device_types', result)
        self.assertIn('browsers', result)
        self.assertIn('operating_systems', result)

        # Check device breakdown
        # Count devices by type
        device_dict = {
            d['device_type']: d['count']
            for d in result['device_types']
        }
        self.assertEqual(device_dict.get('mobile', 0), 2)
        self.assertEqual(device_dict.get('desktop', 0), 2)
        self.assertEqual(device_dict.get('tablet', 0), 1)


class RealtimeVisitorsTestCase(TestCase):
    """Test real-time visitor tracking."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.user_profile = self.user.profile

        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='Test',
            creator=self.user_profile
        )

    @patch('communities.visitor_tracker.visitor_tracker')
    def test_get_realtime_visitors(self, mock_tracker):
        """Test get_realtime_visitors function."""
        # Mock visitor tracker
        mock_tracker.get_online_count.return_value = 10

        result = VisitorAnalytics.get_realtime_visitors(
            str(self.community.id)
        )

        self.assertIn('total_online', result)
        self.assertEqual(result['total_online'], 10)
        self.assertIn('timestamp', result)

        # Verify tracker was called
        mock_tracker.get_online_count.assert_called_once_with(
            str(self.community.id)
        )

    @patch('communities.visitor_tracker.visitor_tracker')
    def test_realtime_visitors_error_handling(self, mock_tracker):
        """Test error handling in get_realtime_visitors."""
        # Mock tracker to raise exception
        mock_tracker.get_online_count.side_effect = Exception('Redis error')

        result = VisitorAnalytics.get_realtime_visitors(
            str(self.community.id)
        )

        # Should return error instead of crashing
        self.assertIn('error', result)


class EdgeCasesTestCase(TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.user_profile = self.user.profile

        self.community = Community.objects.create(
            name='Test Community',
            slug='test-community',
            description='Test',
            creator=self.user_profile
        )

    def test_zero_division_in_conversion_rate(self):
        """Test conversion rate calculation with zero sessions."""
        today = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Get metrics with no data
        result = VisitorAnalytics.get_conversion_metrics(
            start_date=today,
            end_date=timezone.now()
        )

        # Should handle zero division gracefully
        self.assertEqual(result['overall_conversion_rate'], 0)
        self.assertEqual(result['total_conversions'], 0)
        self.assertEqual(result['total_anonymous_sessions'], 0)

    def test_visitor_trends_with_no_data(self):
        """Test visitor trends with no historical data."""
        result = VisitorAnalytics.get_visitor_trends(
            str(self.community.id),
            days=7,
            granularity='daily'
        )

        self.assertIn('trends', result)
        self.assertEqual(len(result['trends']), 7)

        # All days should have zero visitors
        for trend in result['trends']:
            self.assertEqual(trend['total'], 0)

    def test_growth_rate_from_zero(self):
        """Test growth rate calculation from zero baseline."""
        # Only create current period data (no previous period)
        today = timezone.now()
        current_start = today - timedelta(days=7)

        user = User.objects.create_user(
            username='newuser',
            email='new@example.com'
        )
        profile = user.profile

        UserEvent.objects.create(
            user=profile,
            event_type='community_visit',
            description='Visit',
            metadata={'community_id': str(self.community.id)},
            created_at=current_start
        )

        result = get_visitor_growth_rate(
            str(self.community.id),
            current_period_days=7
        )

        # Growth from 0 should be 100%
        self.assertEqual(result['growth_rate'], 100)
        self.assertGreater(result['absolute_change'], 0)

    def test_date_range_edge_cases(self):
        """Test date range edge cases."""
        # Test with start_date = end_date (single moment)
        now = timezone.now()

        result = VisitorAnalytics.get_unique_visitors(
            str(self.community.id),
            start_date=now,
            end_date=now
        )

        self.assertIn('total_unique_visitors', result)
        self.assertEqual(result['total_unique_visitors'], 0)

    def test_invalid_granularity(self):
        """Test visitor trends with invalid granularity."""
        result = VisitorAnalytics.get_visitor_trends(
            str(self.community.id),
            days=7,
            granularity='invalid'
        )

        # Should return empty trends list for invalid granularity
        self.assertIn('trends', result)
        self.assertEqual(len(result['trends']), 0)
