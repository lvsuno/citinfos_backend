"""Tests for anonymous-to-authenticated conversion tracking."""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from analytics.models import AnonymousSession, AnonymousPageView, PageAnalytics
from accounts.models import UserProfile
from communities.models import Community

User = get_user_model()


class ConversionTrackingTestCase(TestCase):
    """Test conversion tracking functionality."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.user_profile = self.user.profile

        # Create test community
        self.community = Community.objects.create(
            name='Test Community',
            description='Test Description',
            creator=self.user_profile
        )

        # Create device fingerprint
        self.device_fingerprint = 'fp_test_12345678'

        # Create anonymous session
        self.session_start = timezone.now() - timedelta(hours=1)
        self.anonymous_session = AnonymousSession.objects.create(
            device_fingerprint=self.device_fingerprint,
            pages_visited=5,
            landing_page='/communities',
            referrer='https://google.com',
            device_type='desktop',
            browser='Chrome',
            os='Windows',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        )
        # Update session_start manually (auto_now_add prevents setting on create)
        AnonymousSession.objects.filter(id=self.anonymous_session.id).update(
            session_start=self.session_start
        )
        self.anonymous_session.refresh_from_db()

        # Create some page views for the session
        for i in range(5):
            AnonymousPageView.objects.create(
                session=self.anonymous_session,
                url=f'/page{i}',
                viewed_at=self.session_start + timedelta(minutes=i*10)
            )

    def tearDown(self):
        """Clean up test data."""
        AnonymousPageView.objects.all().delete()
        AnonymousSession.objects.all().delete()
        PageAnalytics.objects.all().delete()
        Community.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()

    def test_mark_conversion_basic(self):
        """Test basic conversion marking."""
        # Verify session is not converted initially
        self.assertIsNone(self.anonymous_session.converted_to_user)
        self.assertIsNone(self.anonymous_session.converted_at)

        # Mark conversion
        self.anonymous_session.mark_conversion(self.user_profile)
        self.anonymous_session.save()

        # Verify conversion was marked
        self.assertEqual(
            self.anonymous_session.converted_to_user,
            self.user_profile
        )
        self.assertIsNotNone(self.anonymous_session.converted_at)
        self.assertTrue(
            timezone.now() - self.anonymous_session.converted_at <
            timedelta(seconds=5)
        )

    def test_mark_conversion_idempotent(self):
        """Test that marking conversion multiple times is idempotent."""
        # First conversion
        self.anonymous_session.mark_conversion(self.user_profile)
        self.anonymous_session.save()

        # Wait a moment
        from time import sleep
        sleep(0.1)

        # Try converting again
        self.anonymous_session.mark_conversion(self.user_profile)
        self.anonymous_session.save()

        # Conversion time should be updated
        self.assertIsNotNone(self.anonymous_session.converted_at)
        # But user should remain the same
        self.assertEqual(
            self.anonymous_session.converted_to_user,
            self.user_profile
        )

    def test_session_duration_before_conversion(self):
        """Test calculating session duration before conversion."""
        # Mark conversion
        self.anonymous_session.mark_conversion(self.user_profile)
        self.anonymous_session.save()

        # Calculate duration
        session_duration = (
            self.anonymous_session.converted_at -
            self.anonymous_session.session_start
        )

        # Should be approximately 1 hour (when session started)
        self.assertGreater(session_duration.total_seconds(), 3590)  # ~1 hour
        self.assertLess(session_duration.total_seconds(), 3610)

    def test_find_unconverted_sessions(self):
        """Test finding sessions that haven't converted yet."""
        # Create another unconverted session
        AnonymousSession.objects.create(
            device_fingerprint='fp_other_12345',
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            landing_page="/",
            session_start=timezone.now(),
            last_activity=timezone.now(),
            pages_visited=3
        )

        # Find unconverted sessions
        unconverted = AnonymousSession.objects.filter(
            converted_to_user__isnull=True
        )

        # Should have 2 unconverted sessions
        self.assertEqual(unconverted.count(), 2)

        # Convert one
        self.anonymous_session.mark_conversion(self.user_profile)
        self.anonymous_session.save()

        # Now should have only 1 unconverted
        unconverted = AnonymousSession.objects.filter(
            converted_to_user__isnull=True
        )
        self.assertEqual(unconverted.count(), 1)

    def test_find_converted_sessions(self):
        """Test finding converted sessions."""
        # Create another session and convert it
        session2 = AnonymousSession.objects.create(
            device_fingerprint='fp_another',
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            landing_page="/",
            session_start=timezone.now(),
            last_activity=timezone.now(),
            pages_visited=2
        )
        session2.mark_conversion(self.user_profile)
        session2.save()

        # Convert first session too
        self.anonymous_session.mark_conversion(self.user_profile)
        self.anonymous_session.save()

        # Find all converted sessions for this user
        converted = AnonymousSession.objects.filter(
            converted_to_user=self.user_profile
        )

        self.assertEqual(converted.count(), 2)

    def test_conversion_with_page_views(self):
        """Test that conversion preserves page view history."""
        # Get page view count before conversion
        page_view_count = self.anonymous_session.page_views.count()
        self.assertEqual(page_view_count, 5)

        # Mark conversion
        self.anonymous_session.mark_conversion(self.user_profile)
        self.anonymous_session.save()

        # Reload session
        self.anonymous_session.refresh_from_db()

        # Page views should still be there
        self.assertEqual(
            self.anonymous_session.page_views.count(),
            5
        )

        # Should be able to access page views through converted session
        page_views = list(
            self.anonymous_session.page_views.all()
                .order_by('viewed_at')
        )
        self.assertEqual(len(page_views), 5)
        self.assertEqual(page_views[0].url, '/page0')
        self.assertEqual(page_views[4].url, '/page4')


class FingerprintMatchingTestCase(TestCase):
    """Test device fingerprint matching for conversion detection."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='converter',
            email='converter@example.com',
            password='TestPass123!'
        )
        self.user_profile = self.user.profile
        self.fingerprint = 'fp_unique_abc123'

    def tearDown(self):
        """Clean up test data."""
        AnonymousSession.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()

    def test_find_session_by_fingerprint(self):
        """Test finding anonymous sessions by fingerprint."""
        # Create session with fingerprint
        session = AnonymousSession.objects.create(
            device_fingerprint=self.fingerprint,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            landing_page="/",
            session_start=timezone.now(),
            last_activity=timezone.now(),
            pages_visited=1
        )

        # Should be able to find it
        found_session = AnonymousSession.objects.filter(
            device_fingerprint=self.fingerprint,
            converted_to_user__isnull=True
        ).first()

        self.assertIsNotNone(found_session)
        self.assertEqual(found_session.id, session.id)

    def test_find_multiple_sessions_same_fingerprint(self):
        """Test finding multiple sessions with same fingerprint."""
        # Create 3 sessions with same fingerprint over 3 days
        for i in range(3):
            AnonymousSession.objects.create(
                device_fingerprint=self.fingerprint,
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0",
                landing_page="/",
                session_start=timezone.now() - timedelta(days=2-i),
                last_activity=timezone.now() - timedelta(days=2-i),
                pages_visited=i+1
            )

        # Find all sessions for this fingerprint
        sessions = AnonymousSession.objects.filter(
            device_fingerprint=self.fingerprint
        ).order_by('session_start')

        self.assertEqual(sessions.count(), 3)
        self.assertEqual(sessions[0].pages_visited, 1)
        self.assertEqual(sessions[2].pages_visited, 3)

    def test_find_most_recent_session(self):
        """Test finding most recent session for conversion."""
        # Create multiple sessions
        AnonymousSession.objects.create(
            device_fingerprint=self.fingerprint,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            landing_page="/",
            session_start=timezone.now() - timedelta(days=5),
            last_activity=timezone.now() - timedelta(days=5),
            pages_visited=1
        )

        recent_session = AnonymousSession.objects.create(
            device_fingerprint=self.fingerprint,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            landing_page="/",
            session_start=timezone.now() - timedelta(hours=1),
            last_activity=timezone.now(),
            pages_visited=5
        )

        # Find most recent unconverted session
        most_recent = AnonymousSession.objects.filter(
            device_fingerprint=self.fingerprint,
            converted_to_user__isnull=True
        ).order_by('-session_start').first()

        self.assertEqual(most_recent.id, recent_session.id)
        self.assertEqual(most_recent.pages_visited, 5)

    def test_ignore_already_converted_sessions(self):
        """Test that already converted sessions are excluded."""
        # Create and convert old session
        old_session = AnonymousSession.objects.create(
            device_fingerprint=self.fingerprint,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            landing_page="/",
            session_start=timezone.now() - timedelta(days=2),
            last_activity=timezone.now() - timedelta(days=2),
            pages_visited=2
        )
        old_session.mark_conversion(self.user_profile)
        old_session.save()

        # Create new unconverted session
        new_session = AnonymousSession.objects.create(
            device_fingerprint=self.fingerprint,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            landing_page="/",
            session_start=timezone.now(),
            last_activity=timezone.now(),
            pages_visited=3
        )

        # Find unconverted sessions
        unconverted = AnonymousSession.objects.filter(
            device_fingerprint=self.fingerprint,
            converted_to_user__isnull=True
        )

        # Should only find the new session
        self.assertEqual(unconverted.count(), 1)
        self.assertEqual(unconverted.first().id, new_session.id)


class ConversionRateCalculationTestCase(TestCase):
    """Test conversion rate calculations."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123!'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='TestPass123!'
        )

    def tearDown(self):
        """Clean up test data."""
        AnonymousSession.objects.all().delete()
        User.objects.all().delete()

    def test_overall_conversion_rate(self):
        """Test calculating overall conversion rate."""
        # Create 10 anonymous sessions
        for i in range(10):
            AnonymousSession.objects.create(
                device_fingerprint=f'fp_{i}',
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0",
                landing_page="/",
                session_start=timezone.now(),
                last_activity=timezone.now(),
                pages_visited=i+1
            )

        # Convert 3 of them
        sessions_to_convert = AnonymousSession.objects.all()[:3]
        for session in sessions_to_convert:
            session.mark_conversion(self.user1.profile)
            session.save()

        # Calculate conversion rate
        total_sessions = AnonymousSession.objects.count()
        converted_sessions = AnonymousSession.objects.filter(
            converted_to_user__isnull=False
        ).count()

        conversion_rate = (converted_sessions / total_sessions) * 100

        self.assertEqual(total_sessions, 10)
        self.assertEqual(converted_sessions, 3)
        self.assertEqual(conversion_rate, 30.0)

    def test_conversion_rate_by_date_range(self):
        """Test conversion rate within a date range."""
        today = timezone.now()

        # Create sessions over 7 days
        for day in range(7):
            date = today - timedelta(days=day)
            for session_num in range(5):
                session = AnonymousSession.objects.create(
                    device_fingerprint=f'fp_day{day}_s{session_num}',
                    ip_address="127.0.0.1",
                    user_agent="Mozilla/5.0",
                    landing_page="/",
                    last_activity=date,
                    pages_visited=1
                )
                # Update session_start (can't set on create due to auto_now_add)
                AnonymousSession.objects.filter(id=session.id).update(
                    session_start=date
                )

        # Convert some sessions from last 3 days
        recent_sessions = AnonymousSession.objects.filter(
            session_start__gte=today - timedelta(days=3)
        )[:8]  # Convert 8 out of 15 from last 3 days

        for session in recent_sessions:
            session.mark_conversion(self.user1.profile)
            session.save()

        # Calculate conversion rate for last 3 days
        start_date = today - timedelta(days=3)
        total_in_range = AnonymousSession.objects.filter(
            session_start__gte=start_date
        ).count()
        converted_in_range = AnonymousSession.objects.filter(
            session_start__gte=start_date,
            converted_to_user__isnull=False
        ).count()

        conversion_rate = (converted_in_range / total_in_range) * 100

        self.assertEqual(total_in_range, 20)  # 4 days * 5 sessions (days 0-3 inclusive)
        self.assertEqual(converted_in_range, 8)
        self.assertAlmostEqual(conversion_rate, 40.0, places=1)

    def test_zero_conversion_rate(self):
        """Test conversion rate when no conversions."""
        # Create sessions without converting any
        for i in range(5):
            AnonymousSession.objects.create(
                device_fingerprint=f'fp_{i}',
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0",
                landing_page="/",
                session_start=timezone.now(),
                last_activity=timezone.now(),
                pages_visited=1
            )

        total = AnonymousSession.objects.count()
        converted = AnonymousSession.objects.filter(
            converted_to_user__isnull=False
        ).count()

        conversion_rate = (converted / total) * 100 if total > 0 else 0

        self.assertEqual(total, 5)
        self.assertEqual(converted, 0)
        self.assertEqual(conversion_rate, 0.0)

    def test_hundred_percent_conversion_rate(self):
        """Test 100% conversion rate."""
        # Create 5 sessions
        sessions = []
        for i in range(5):
            session = AnonymousSession.objects.create(
                device_fingerprint=f'fp_{i}',
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0",
                landing_page="/",
                session_start=timezone.now(),
                last_activity=timezone.now(),
                pages_visited=1
            )
            sessions.append(session)

        # Convert all of them
        for session in sessions:
            session.mark_conversion(self.user1.profile)
            session.save()

        total = AnonymousSession.objects.count()
        converted = AnonymousSession.objects.filter(
            converted_to_user__isnull=False
        ).count()

        conversion_rate = (converted / total) * 100

        self.assertEqual(total, 5)
        self.assertEqual(converted, 5)
        self.assertEqual(conversion_rate, 100.0)


class ConversionTimeAnalysisTestCase(TestCase):
    """Test time-to-conversion analysis."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='timetest',
            email='time@example.com',
            password='TestPass123!'
        )
        self.user_profile = self.user.profile

    def tearDown(self):
        """Clean up test data."""
        AnonymousSession.objects.all().delete()
        User.objects.all().delete()

    def test_average_time_to_conversion(self):
        """Test calculating average time to conversion."""
        # Create sessions with different durations before conversion
        durations_minutes = [10, 30, 60, 120]

        for minutes in durations_minutes:
            session_start = timezone.now() - timedelta(minutes=minutes)
            session = AnonymousSession.objects.create(
                device_fingerprint=f'fp_{minutes}',
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0",
                landing_page="/",
                last_activity=timezone.now(),
                pages_visited=5
            )
            # Update session_start (can't set on create due to auto_now_add)
            AnonymousSession.objects.filter(id=session.id).update(
                session_start=session_start
            )
            session.refresh_from_db()
            session.mark_conversion(self.user_profile)
            session.save()

        # Calculate average time to conversion
        converted_sessions = AnonymousSession.objects.filter(
            converted_to_user__isnull=False
        )

        total_duration = timedelta(0)
        for session in converted_sessions:
            duration = session.converted_at - session.session_start
            total_duration += duration

        avg_duration = total_duration / converted_sessions.count()

        # Average of [10, 30, 60, 120] = 55 minutes
        avg_minutes = avg_duration.total_seconds() / 60
        self.assertAlmostEqual(avg_minutes, 55.0, delta=5.0)

    def test_conversion_within_time_window(self):
        """Test finding conversions within a time window."""
        # Create session that converts quickly (5 minutes)
        quick_start = timezone.now() - timedelta(minutes=5)
        quick_session = AnonymousSession.objects.create(
            device_fingerprint='fp_quick',
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            landing_page="/",
            last_activity=timezone.now(),
            pages_visited=2
        )
        # Update session_start (can't set on create due to auto_now_add)
        AnonymousSession.objects.filter(id=quick_session.id).update(
            session_start=quick_start
        )
        quick_session.refresh_from_db()
        quick_session.mark_conversion(self.user_profile)
        quick_session.save()

        # Create session that converts slowly (2 hours)
        slow_start = timezone.now() - timedelta(hours=2)
        slow_session = AnonymousSession.objects.create(
            device_fingerprint='fp_slow',
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            landing_page="/",
            last_activity=timezone.now(),
            pages_visited=10
        )
        # Update session_start (can't set on create due to auto_now_add)
        AnonymousSession.objects.filter(id=slow_session.id).update(
            session_start=slow_start
        )
        slow_session.refresh_from_db()
        slow_session.mark_conversion(self.user_profile)
        slow_session.save()

        # Find sessions that converted within 30 minutes
        quick_converters = []
        for session in AnonymousSession.objects.filter(
            converted_to_user__isnull=False
        ):
            time_to_convert = session.converted_at - session.session_start
            if time_to_convert <= timedelta(minutes=30):
                quick_converters.append(session)

        # Should only find the quick session
        self.assertEqual(len(quick_converters), 1)
        self.assertEqual(quick_converters[0].device_fingerprint, 'fp_quick')

    def test_pages_visited_before_conversion(self):
        """Test analyzing pages visited before conversion."""
        # Create sessions with varying page visits
        for pages in [2, 5, 10, 15]:
            session = AnonymousSession.objects.create(
                device_fingerprint=f'fp_pages_{pages}',
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0",
                landing_page="/",
                session_start=timezone.now(),
                last_activity=timezone.now(),
                pages_visited=pages
            )
            session.mark_conversion(self.user_profile)
            session.save()

        # Calculate average pages before conversion
        converted = AnonymousSession.objects.filter(
            converted_to_user__isnull=False
        )

        total_pages = sum(s.pages_visited for s in converted)
        avg_pages = total_pages / converted.count()

        # Average of [2, 5, 10, 15] = 8
        self.assertEqual(avg_pages, 8.0)

    def test_conversion_funnel_stages(self):
        """Test analyzing conversion funnel stages."""
        # Stage 1: Landing (all anonymous sessions)
        for i in range(100):
            AnonymousSession.objects.create(
                device_fingerprint=f'fp_funnel_{i}',
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0",
                landing_page="/",
                session_start=timezone.now(),
                last_activity=timezone.now(),
                pages_visited=1 if i < 50 else 5  # Half view multiple pages
            )

        # Stage 2: Engagement (visited 5+ pages)
        engaged = AnonymousSession.objects.filter(pages_visited__gte=5)

        # Stage 3: Conversion (convert 20% of engaged users)
        sessions_to_convert = list(engaged)[:10]  # 10 out of 50 engaged
        for session in sessions_to_convert:
            session.mark_conversion(self.user_profile)
            session.save()

        # Analyze funnel
        total_sessions = AnonymousSession.objects.count()
        engaged_count = engaged.count()
        converted_count = AnonymousSession.objects.filter(
            converted_to_user__isnull=False
        ).count()

        # Calculate drop-off rates
        engagement_rate = (engaged_count / total_sessions) * 100
        conversion_rate_from_engaged = (
            (converted_count / engaged_count) * 100
        )

        self.assertEqual(total_sessions, 100)
        self.assertEqual(engaged_count, 50)
        self.assertEqual(converted_count, 10)
        self.assertEqual(engagement_rate, 50.0)
        self.assertEqual(conversion_rate_from_engaged, 20.0)
