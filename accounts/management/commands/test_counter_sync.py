"""Test command to verify counter synchronization system."""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Test the counter synchronization system functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing counter synchronization system...')

        # Get a sample user for testing
        sample_user = UserProfile.objects.first()

        if not sample_user:
            self.stdout.write(
                self.style.WARNING(
                    'No users found in database for testing'
                )
            )
            return

        self.stdout.write(
            f'Testing with user: {sample_user.user.username} '
            f'(ID: {sample_user.id})'
        )

        # Test counter sync methods
        with transaction.atomic():
            # Save original values
            original_counters = {
                'posts_count': sample_user.posts_count,
                'follower_count': sample_user.follower_count,
                'following_count': sample_user.following_count,
                'likes_given_count': sample_user.likes_given_count,
                'comments_made_count': sample_user.comments_made_count,
                'reposts_count': sample_user.reposts_count,
            }

            # Test individual sync methods
            try:
                sample_user.sync_posts_count()
                self.stdout.write(
                    self.style.SUCCESS('✓ sync_posts_count() works')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ sync_posts_count() failed: {e}')
                )

            try:
                sample_user.sync_followers_following_count()
                self.stdout.write(
                    self.style.SUCCESS(
                        '✓ sync_followers_following_count() works'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ sync_followers_following_count() failed: {e}'
                    )
                )

            try:
                sample_user.sync_likes_given_count()
                self.stdout.write(
                    self.style.SUCCESS('✓ sync_likes_given_count() works')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ sync_likes_given_count() failed: {e}'
                    )
                )

            # Test registration_index assignment
            if hasattr(sample_user, 'registration_index'):
                if sample_user.registration_index is None:
                    try:
                        sample_user.assign_registration_index()
                        self.stdout.write(
                            self.style.SUCCESS(
                                '✓ assign_registration_index() works'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'✗ assign_registration_index() failed: {e}'
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ User already has registration_index: '
                            f'{sample_user.registration_index}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS('Counter synchronization system test complete!')
        )
