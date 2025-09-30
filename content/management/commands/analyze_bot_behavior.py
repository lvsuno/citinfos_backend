"""
Management command to analyze users for bot behavior and update profiles.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile
from content.utils import update_bot_detection_profile


class Command(BaseCommand):
    help = 'Analyze users for bot behavior and update detection profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Analyze all users (default: only active users)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to look back for activity (default: 30)',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Analyze specific user by username',
        )

    def handle(self, *args, **options):
        if options['username']:
            # Analyze specific user
            try:
                user = UserProfile.objects.get(user__username=options['username'])
                self.analyze_user(user)
            except UserProfile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User '{options['username']}' not found")
                )
                return
        else:
            # Analyze multiple users
            if options['all_users']:
                users = UserProfile.objects.all()
                self.stdout.write(f'Analyzing all {users.count()} users...')
            else:
                # Only analyze users with recent activity
                recent_date = timezone.now() - timedelta(days=options['days'])
                users = UserProfile.objects.filter(
                    posts__created_at__gte=recent_date
                ).distinct()
                self.stdout.write(f'Analyzing {users.count()} active users...')

            bot_count = 0
            flagged_count = 0
            blocked_count = 0

            for user in users:
                result = self.analyze_user(user, verbose=False)
                if result['is_bot']:
                    bot_count += 1
                if result['flagged']:
                    flagged_count += 1
                if result['blocked']:
                    blocked_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Analysis complete! '
                    f'Bots detected: {bot_count}, '
                    f'Flagged: {flagged_count}, '
                    f'Blocked: {blocked_count}'
                )
            )

    def analyze_user(self, user, verbose=True):
        """Analyze a single user for bot behavior."""
        if verbose:
            self.stdout.write(f'Analyzing user: {user.user.username}')

        # Update bot detection profile
        profile = update_bot_detection_profile(user)

        result = {
            'is_bot': profile.is_likely_bot,
            'flagged': profile.is_flagged_as_bot,
            'blocked': profile.auto_blocked,
            'score': profile.overall_bot_score,
        }

        if verbose:
            self.stdout.write(f'  Bot Score: {profile.overall_bot_score:.2f}')
            self.stdout.write(f'  Timing Score: {profile.timing_score:.2f}')
            self.stdout.write(f'  Content Score: {profile.content_score:.2f}')
            self.stdout.write(f'  Behavior Score: {profile.behavior_score:.2f}')

            if profile.is_flagged_as_bot:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  User flagged as potential bot')
                )

            if profile.auto_blocked:
                self.stdout.write(
                    self.style.ERROR(f'  🚫 User blocked as bot')
                )

            if profile.is_verified_human:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ User verified as human')
                )

            self.stdout.write('')  # Empty line

        return result
