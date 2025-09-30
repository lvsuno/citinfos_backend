"""
Management command to initialize badge definitions from environment variables.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.badge_evaluator import badge_evaluator


class Command(BaseCommand):
    help = 'Initialize badge definitions from environment variables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force update existing badge definitions'
        )

    def handle(self, *args, **options):
        self.stdout.write('Initializing badge definitions...')

        try:
            with transaction.atomic():
                # This will create/update badge definitions
                badge_evaluator._initialize_badge_definitions()

            from accounts.models import BadgeDefinition
            active_count = BadgeDefinition.objects.filter(
                is_active=True,
                is_deleted=False
            ).count()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully initialized {active_count} badge definitions'
                )
            )

            if options['force_update']:
                self.stdout.write(
                    self.style.WARNING(
                        'Forced update of existing badge definitions'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error initializing badge definitions: {str(e)}'
                )
            )
