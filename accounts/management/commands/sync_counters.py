"""Management command to synchronize UserProfile counters with model counts."""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Synchronize all UserProfile counters with actual model counts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--profile-id',
            type=str,
            help='Sync counters for specific UserProfile ID only',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Process profiles in batches (default: 100)',
        )

    def handle(self, *args, **options):
        profile_id = options.get('profile_id')
        batch_size = options.get('batch_size', 100)

        if profile_id:
            # Sync specific profile
            try:
                profile = UserProfile.objects.get(id=profile_id)
                self.sync_profile_counters(profile)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully synced counters for profile '
                        f'{profile_id}'
                    )
                )
            except UserProfile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'UserProfile with ID {profile_id} not found'
                    )
                )
                return
        else:
            # Sync all profiles in batches
            total_profiles = UserProfile.objects.count()
            self.stdout.write(
                f'Syncing counters for {total_profiles} profiles...'
            )

            processed = 0
            while processed < total_profiles:
                batch_end = processed + batch_size
                batch = UserProfile.objects.all()[processed:batch_end]

                for profile in batch:
                    self.sync_profile_counters(profile)
                    processed += 1

                    if processed % 50 == 0:
                        self.stdout.write(
                            f'Processed {processed}/{total_profiles} profiles'
                        )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully synced counters for {total_profiles} '
                    f'profiles'
                )
            )

    def sync_profile_counters(self, profile):
        """Sync counters for a specific profile."""
        with transaction.atomic():
            # Sync all counter types
            profile.sync_posts_count()
            profile.sync_followers_following_count()
            profile.sync_likes_given_count()
            profile.sync_comments_made_count()
            profile.sync_reposts_count()
            profile.sync_shares_count()
            profile.sync_equipments_added_count()
            profile.sync_polls_and_votes_count()
            profile.sync_communities_joined_count()

            # Save all updated counter fields
            profile.save(update_fields=[
                'posts_count', 'follower_count', 'following_count',
                'likes_given_count', 'comments_made_count', 'reposts_count',
                'shares_sent_count', 'shares_received_count',
                'equipments_added_count', 'polls_created_count',
                'poll_votes_count', 'communities_joined_count'
            ])
