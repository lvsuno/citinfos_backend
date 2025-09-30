"""Management command to assign registration_index to existing users."""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Assign registration_index to users who do not have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Process profiles in batches (default: 100)',
        )

    def handle(self, *args, **options):
        batch_size = options.get('batch_size', 100)

        # Get users without registration_index
        profiles_without_index = UserProfile.objects.filter(
            registration_index__isnull=True
        ).order_by('user__date_joined')

        total_profiles = profiles_without_index.count()

        if total_profiles == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    'All users already have registration_index assigned!'
                )
            )
            return

        self.stdout.write(
            f'Assigning registration_index to {total_profiles} users...'
        )

        processed = 0
        batch_start = 0

        while batch_start < total_profiles:
            batch_end = min(batch_start + batch_size, total_profiles)
            batch = profiles_without_index[batch_start:batch_end]

            with transaction.atomic():
                for profile in batch:
                    profile.assign_registration_index()
                    processed += 1

                    if processed % 50 == 0:
                        self.stdout.write(
                            f'Processed {processed}/{total_profiles} users'
                        )

            batch_start = batch_end

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully assigned registration_index to '
                f'{total_profiles} users'
            )
        )
