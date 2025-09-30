"""Management command to test system announcement functionality."""

from django.core.management.base import BaseCommand
from core.announcement_utils import SystemAnnouncementManager
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Test system announcement functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-welcome',
            action='store_true',
            help='Test welcome announcement creation',
        )
        parser.add_argument(
            '--test-maintenance',
            action='store_true',
            help='Test maintenance announcement creation',
        )
        parser.add_argument(
            '--test-role-based',
            action='store_true',
            help='Test role-based announcement creation',
        )
        parser.add_argument(
            '--test-geographic',
            action='store_true',
            help='Test geographic announcement creation',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username for testing welcome messages',
        )

    def handle(self, *args, **options):
        if options['test_welcome']:
            self.test_welcome_announcement(options.get('username'))

        if options['test_maintenance']:
            self.test_maintenance_announcement()

        if options['test_role_based']:
            self.test_role_based_announcement()

        if options['test_geographic']:
            self.test_geographic_announcement()

    def test_welcome_announcement(self, username=None):
        """Test creating a welcome announcement."""
        if username:
            try:
                user_profile = UserProfile.objects.get(user__username=username)
                announcement = SystemAnnouncementManager.create_welcome_announcement(user_profile)
                self.stdout.write(
                    self.style.SUCCESS(f'Created welcome announcement for {username}: {announcement.id}')
                )
            except UserProfile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User {username} not found')
                )
        else:
            # Test with first available user
            user_profile = UserProfile.objects.first()
            if user_profile:
                announcement = SystemAnnouncementManager.create_welcome_announcement(user_profile)
                self.stdout.write(
                    self.style.SUCCESS(f'Created welcome announcement for {user_profile.user.username}: {announcement.id}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('No users found for testing')
                )

    def test_maintenance_announcement(self):
        """Test creating a maintenance announcement."""
        announcement = SystemAnnouncementManager.create_maintenance_announcement(
            title="Scheduled Maintenance",
            message="<p>We will be performing scheduled maintenance on our servers. The platform may be temporarily unavailable.</p>",
            scheduled_time="2025-09-05 02:00 UTC"
        )
        self.stdout.write(
            self.style.SUCCESS(f'Created maintenance announcement: {announcement.id}')
        )

    def test_role_based_announcement(self):
        """Test creating a role-based announcement."""
        announcement = SystemAnnouncementManager.create_role_announcement(
            title="Admin Notice",
            message="<p>This is a test announcement for administrators and moderators only.</p>",
            target_roles=['admin', 'moderator']
        )
        self.stdout.write(
            self.style.SUCCESS(f'Created role-based announcement: {announcement.id}')
        )

    def test_geographic_announcement(self):
        """Test creating a geographic announcement."""
        announcement = SystemAnnouncementManager.create_geographic_announcement(
            title="Regional Update",
            message="<p>This is a test announcement for users in specific regions.</p>",
            countries=['US', 'CA'],
            timezones=['America/New_York', 'America/Los_Angeles']
        )
        self.stdout.write(
            self.style.SUCCESS(f'Created geographic announcement: {announcement.id}')
        )
