"""Management command to test community analytics system."""

from django.core.management.base import BaseCommand
from django.utils import timezone
from communities.models import Community, CommunityMembership
from accounts.models import UserProfile
from analytics.services import online_tracker
from analytics.models import CommunityAnalytics
from analytics.tasks import update_community_analytics, cleanup_inactive_users
from analytics.signals import track_user_activity
import random


class Command(BaseCommand):
    """Test command for community analytics system."""

    help = 'Test the real-time community analytics system'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--community-id',
            type=str,
            help='Test specific community by ID',
        )
        parser.add_argument(
            '--simulate-users',
            type=int,
            default=5,
            help='Number of users to simulate (default: 5)',
        )
        parser.add_argument(
            '--test-redis',
            action='store_true',
            help='Test Redis connection and operations',
        )
        parser.add_argument(
            '--test-tasks',
            action='store_true',
            help='Test Celery tasks',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up test data',
        )

    def handle(self, *args, **options):
        """Handle the command."""
        self.stdout.write(
            self.style.SUCCESS('Starting Community Analytics System Test')
        )

        if options['cleanup']:
            self.cleanup_test_data()
            return

        if options['test_redis']:
            self.test_redis_operations()

        if options['test_tasks']:
            self.test_celery_tasks()

        # Test with specific community or first available
        if options['community_id']:
            try:
                community = Community.objects.get(
                    id=options['community_id'],
                    is_deleted=False
                )
            except Community.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Community {options["community_id"]} not found')
                )
                return
        else:
            community = Community.objects.filter(is_deleted=False).first()
            if not community:
                self.stdout.write(
                    self.style.ERROR('No communities found. Create a community first.')
                )
                return

        self.stdout.write(f'Testing with community: {community.name}')

        # Test community analytics
        self.test_community_analytics(community, options['simulate_users'])

    def test_redis_operations(self):
        """Test Redis connection and basic operations."""
        self.stdout.write(self.style.WARNING('Testing Redis operations...'))

        try:
            # Test Redis connection
            redis_client = online_tracker.redis_client
            redis_client.ping()
            self.stdout.write(self.style.SUCCESS('✓ Redis connection successful'))

            # Test basic operations
            test_key = 'test:analytics:connection'
            redis_client.set(test_key, 'test_value', ex=10)
            value = redis_client.get(test_key)

            if value and value.decode('utf-8') == 'test_value':
                self.stdout.write(self.style.SUCCESS('✓ Redis read/write operations work'))
                redis_client.delete(test_key)
            else:
                self.stdout.write(self.style.ERROR('✗ Redis read/write operations failed'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Redis connection failed: {e}')
            )

    def test_celery_tasks(self):
        """Test Celery tasks."""
        self.stdout.write(self.style.WARNING('Testing Celery tasks...'))

        try:
            # Test cleanup task
            result = cleanup_inactive_users.delay()
            self.stdout.write(f'✓ Cleanup task queued: {result.id}')

            # Test analytics update task
            result = update_community_analytics.delay()
            self.stdout.write(f'✓ Analytics update task queued: {result.id}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Celery tasks failed: {e}')
            )

    def test_community_analytics(self, community, num_users):
        """Test community analytics with simulated users."""
        self.stdout.write(
            self.style.WARNING(f'Testing analytics for {community.name}...')
        )

        # Get some users to simulate
        users = list(UserProfile.objects.all()[:num_users])
        if len(users) < num_users:
            self.stdout.write(
                self.style.WARNING(f'Only {len(users)} users available for testing')
            )

        community_id = str(community.id)

        # Test 1: Check initial state
        initial_count = online_tracker.get_online_count(community_id)
        self.stdout.write(f'Initial online count: {initial_count}')

        # Test 2: Add users to community
        self.stdout.write('Adding users to community...')
        for i, user in enumerate(users):
            user_id = str(user.id)

            # Ensure user has membership
            membership, created = CommunityMembership.objects.get_or_create(
                community=community,
                user=user,
                defaults={'status': 'active'}
            )
            if created:
                self.stdout.write(f'  Created membership for {user.user.username}')

            # Add user to online tracking
            current_count = online_tracker.add_user_to_community(user_id, community_id)
            self.stdout.write(
                f'  {user.user.username} added. Online count: {current_count}'
            )

        # Test 3: Simulate activity
        self.stdout.write('Simulating user activity...')
        for user in users[:3]:  # Simulate activity for first 3 users
            user_id = str(user.id)
            track_user_activity(user_id, community_id, 'test_activity')

            # Update activity timestamp
            current_count = online_tracker.update_user_activity(user_id, community_id)
            self.stdout.write(
                f'  {user.user.username} activity updated. Count: {current_count}'
            )

        # Test 4: Check online members
        online_members = online_tracker.get_online_members(community_id)
        self.stdout.write(f'Online members: {len(online_members)}')
        for member_id in list(online_members)[:3]:
            try:
                user = UserProfile.objects.get(id=member_id)
                self.stdout.write(f'  - {user.user.username}')
            except UserProfile.DoesNotExist:
                self.stdout.write(f'  - Unknown user ({member_id})')

        # Test 5: Check peak counts
        peaks = online_tracker.get_peak_counts(community_id)
        self.stdout.write(f'Peak counts: {peaks}')

        # Test 6: Test analytics caching
        cached_analytics = online_tracker.get_cached_analytics(community_id)
        if cached_analytics:
            self.stdout.write('✓ Analytics caching working')
            self.stdout.write(f'  Cached data: {cached_analytics}')
        else:
            self.stdout.write('ℹ No cached analytics (will be created on first request)')

        # Test 7: Database analytics
        self.stdout.write('Testing database analytics...')
        analytics, created = CommunityAnalytics.objects.get_or_create(
            community=community,
            date=timezone.now().date(),
            defaults={
                'current_online_members': len(online_members),
                'daily_active_members': len(users),
            }
        )

        if created:
            self.stdout.write('✓ Created new analytics record')
        else:
            self.stdout.write('✓ Found existing analytics record')

        self.stdout.write(f'  Current online: {analytics.current_online_members}')
        self.stdout.write(f'  Daily active: {analytics.daily_active_members}')

        # Test 8: Remove some users
        self.stdout.write('Testing user removal...')
        users_to_remove = users[:2]  # Remove first 2 users
        for user in users_to_remove:
            user_id = str(user.id)
            current_count = online_tracker.remove_user_from_community(user_id, community_id)
            self.stdout.write(
                f'  Removed {user.user.username}. Count: {current_count}'
            )

        # Final state
        final_count = online_tracker.get_online_count(community_id)
        final_members = online_tracker.get_online_members(community_id)

        self.stdout.write(
            self.style.SUCCESS(
                f'Test completed! Final online count: {final_count} '
                f'(members: {len(final_members)})'
            )
        )

    def cleanup_test_data(self):
        """Clean up test data."""
        self.stdout.write(self.style.WARNING('Cleaning up test data...'))

        try:
            # Clean up Redis test keys
            redis_client = online_tracker.redis_client

            # Get all community keys
            community_keys = redis_client.keys('community:*')
            user_keys = redis_client.keys('user:*')

            deleted_count = 0
            for key in community_keys + user_keys:
                redis_client.delete(key)
                deleted_count += 1

            self.stdout.write(f'✓ Deleted {deleted_count} Redis keys')

            # Note: We don't delete database records as they might be real data
            self.stdout.write('ℹ Database records preserved (delete manually if needed)')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Cleanup failed: {e}')
            )
