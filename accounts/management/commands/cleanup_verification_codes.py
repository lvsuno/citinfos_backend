"""Management command to clean up expired verification codes."""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from accounts.models import VerificationCode
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up expired verification codes (HARD DELETE for security)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete codes older than this many days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--unused-only',
            action='store_true',
            help='Only delete unused codes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Delete codes in batches (default: 1000)',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        unused_only = options['unused_only']
        batch_size = options['batch_size']

        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(f'🗑️ Cleaning verification codes older than {days} days')
        self.stdout.write(f'📅 Cutoff date: {cutoff_date}')

        # Build query
        query = VerificationCode.objects.filter(expires_at__lt=cutoff_date)

        if unused_only:
            query = query.filter(is_used=False)
            self.stdout.write('🎯 Mode: Unused codes only')
        else:
            self.stdout.write('🎯 Mode: All expired codes')

        total_count = query.count()

        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ No expired codes found to delete')
            )
            return

        # Show detailed statistics
        used_count = query.filter(is_used=True).count()
        unused_count = query.filter(is_used=False).count()

        self.stdout.write(f'\n📊 CLEANUP STATISTICS:')
        self.stdout.write(f'   Total expired codes: {total_count}')
        self.stdout.write(f'   - Used codes: {used_count}')
        self.stdout.write(f'   - Unused codes: {unused_count}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n🧪 DRY RUN: Would HARD DELETE {total_count} '
                    f'verification codes'
                )
            )
            return

        # Perform hard deletion in batches for performance
        deleted_total = 0

        self.stdout.write(f'\n🔄 Performing HARD DELETE in batches of {batch_size}...')

        with transaction.atomic():
            while True:
                # Get batch of codes to delete
                batch_ids = list(
                    query.values_list('id', flat=True)[:batch_size]
                )

                if not batch_ids:
                    break

                # Log deletion for audit trail (optional)
                batch_codes = VerificationCode.objects.filter(
                    id__in=batch_ids
                )

                # Log each code deletion (for audit if required)
                for code in batch_codes:
                    logger.info(
                        f'HARD DELETE verification code: {code.id} '
                        f'for user {code.user.user.username}, '
                        f'expired: {code.expires_at}, '
                        f'used: {code.is_used}'
                    )

                # Perform hard deletion
                deleted_count = VerificationCode.objects.filter(
                    id__in=batch_ids
                ).delete()[0]

                deleted_total += deleted_count

                self.stdout.write(
                    f'   Deleted batch: {deleted_count} codes '
                    f'(Total: {deleted_total}/{total_count})'
                )

                if deleted_count < batch_size:
                    break

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ HARD DELETE COMPLETED: Removed {deleted_total} '
                f'expired verification codes'
            )
        )
        self.stdout.write(
            '🔒 Security: Expired codes permanently removed from database'
        )
        self.stdout.write(
            '📝 Audit: Deletion events logged (check application logs)'
        )
