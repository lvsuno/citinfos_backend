"""
Fix verified users with null last_verified_at field.
This script updates all UserProfile records where is_verified=True but last_verified_at is null.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Fix verified users with null last_verified_at field'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        # Find verified users with null last_verified_at
        users_to_fix = UserProfile.objects.filter(
            is_verified=True,
            last_verified_at__isnull=True,
            is_deleted=False
        )

        count = users_to_fix.count()
        self.stdout.write(f"Found {count} verified users with null last_verified_at")

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No users need fixing!"))
            return

        if options['dry_run']:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
            for profile in users_to_fix:
                self.stdout.write(f"Would fix: {profile.user.username} (verified but no timestamp)")
            return

        # Fix the users by setting last_verified_at to their created_at date
        # This assumes they were verified when they were created
        updated_count = 0
        current_time = timezone.now()

        for profile in users_to_fix:
            # Set last_verified_at to either:
            # 1. The verification code updated_at time (if available)
            # 2. The profile created_at time (fallback)
            try:
                from accounts.models import VerificationCode

                # Try to get the verification code used date
                vcode = VerificationCode.objects.filter(
                    user=profile,
                    is_used=True
                ).order_by('-updated_at').first()

                if vcode and vcode.updated_at:
                    profile.last_verified_at = vcode.updated_at
                    source = "verification code date"
                else:
                    # Fallback to created_at
                    profile.last_verified_at = profile.created_at
                    source = "profile creation date"

                profile.save(update_fields=['last_verified_at'])
                updated_count += 1

                self.stdout.write(f"Fixed {profile.user.username}: {source}")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error fixing {profile.user.username}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully fixed {updated_count} out of {count} users"
            )
        )
