"""
Management command to fix registration indices for existing users.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Fix registration indices for existing users based on creation order'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write('DRY RUN - No changes will be made')

        # Get all users ordered by creation date
        users = UserProfile.objects.all().order_by('created_at', 'id')

        self.stdout.write(f'Found {users.count()} user profiles to update')

        updated_count = 0

        with transaction.atomic():
            for index, user_profile in enumerate(users, 1):
                old_index = user_profile.registration_index

                if not dry_run:
                    user_profile.registration_index = index
                    user_profile.save(update_fields=['registration_index'])

                if old_index != index:
                    self.stdout.write(
                        f'  {user_profile.user.username}: {old_index} -> {index}'
                    )
                    updated_count += 1
                else:
                    self.stdout.write(f'  {user_profile.user.username}: {index} (no change)')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would update {updated_count} user registration indices'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} user registration indices'
                )
            )
