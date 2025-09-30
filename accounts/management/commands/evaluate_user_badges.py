"""
Management command to evaluate badges for all users or specific user.
"""

from django.core.management.base import BaseCommand
from accounts.models import UserProfile
from accounts.badge_evaluator import badge_evaluator


class Command(BaseCommand):
    help = 'Evaluate badges for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=str,
            help='Evaluate badges for specific user by UUID'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Evaluate badges for specific user by username'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for processing all users (default: 100)'
        )

    def handle(self, *args, **options):
        if options['user_id']:
            self._evaluate_single_user_by_id(options['user_id'])
        elif options['username']:
            self._evaluate_single_user_by_username(options['username'])
        else:
            self._evaluate_all_users(options['batch_size'])

    def _evaluate_single_user_by_id(self, user_id):
        """Evaluate badges for a single user by UUID."""
        try:
            profile = UserProfile.objects.get(id=user_id)
            username = profile.user.username
            self.stdout.write(f'Evaluating badges for user: {username}')

            result = badge_evaluator.evaluate_user_badges(profile)
            awarded_count, new_badges = result

            if awarded_count > 0:
                badge_list = ", ".join(new_badges)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Awarded {awarded_count} new badges: {badge_list}'
                    )
                )
            else:
                self.stdout.write('No new badges awarded')

        except UserProfile.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {user_id} not found')
            )

    def _evaluate_single_user_by_username(self, username):
        """Evaluate badges for a single user by username."""
        try:
            profile = UserProfile.objects.get(user__username=username)
            self.stdout.write(f'Evaluating badges for user: {username}')

            result = badge_evaluator.evaluate_user_badges(profile)
            awarded_count, new_badges = result

            if awarded_count > 0:
                badge_list = ", ".join(new_badges)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Awarded {awarded_count} new badges: {badge_list}'
                    )
                )
            else:
                self.stdout.write('No new badges awarded')

        except UserProfile.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} not found')
            )

    def _evaluate_all_users(self, batch_size):
        """Evaluate badges for all users."""
        message = f'Evaluating badges for all users (batch size: {batch_size})'
        self.stdout.write(message)

        stats = badge_evaluator.evaluate_all_users(batch_size=batch_size)

        result_message = (
            f"Badge evaluation complete:\n"
            f"  Users processed: {stats['users_processed']}\n"
            f"  Total badges awarded: {stats['total_badges_awarded']}\n"
            f"  Errors: {stats['errors']}"
        )
        self.stdout.write(self.style.SUCCESS(result_message))
