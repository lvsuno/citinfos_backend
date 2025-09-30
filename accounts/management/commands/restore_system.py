"""
Management command for the enhanced restoration system with proper cascading.
"""
from django.core.management.base import BaseCommand
from django.apps import apps
from core.cascade_restore import EnhancedCascadeRestore, CascadeRestoreAnalyzer


class Command(BaseCommand):
    help = 'Enhanced cascading restoration utilities for soft-deleted objects'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['restore', 'list', 'history', 'cascade'],
            help='Action to perform'
        )
        parser.add_argument(
            '--model',
            help='Model name (app_label.ModelName)'
        )
        parser.add_argument(
            '--pk',
            help='Primary key of the object to restore'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Apply action to all deleted objects'
        )
        parser.add_argument(
            '--cascade',
            action='store_true',
            default=True,
            help='Enable cascading restoration (default: True)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be restored without making changes'
        )

    def handle(self, *args, **options):
        action = options['action']

        if action == 'restore':
            self.handle_restore(options)
        elif action == 'list':
            self.handle_list(options)
        elif action == 'history':
            self.handle_history(options)
        elif action == 'cascade':
            self.handle_cascade_restore(options)

    def handle_restore(self, options):
        """Restore specific or all soft-deleted objects."""
        if not options['model']:
            self.stdout.write(
                self.style.ERROR('--model is required for restore action')
            )
            return

        try:
            app_label, model_name = options['model'].split('.')
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError) as e:
            self.stdout.write(
                self.style.ERROR(f'Invalid model: {options["model"]} - {e}')
            )
            return

        # Check if model has restoration capabilities
        if not hasattr(model, 'restore_instance'):
            self.stdout.write(
                self.style.ERROR(
                    f'Model {model.__name__} does not have restoration methods'
                )
            )
            return

        if options['all']:
            # Restore all deleted objects
            deleted_objects = model.objects.filter(is_deleted=True)
            count = deleted_objects.count()

            if count == 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'No deleted {model.__name__} objects found'
                    )
                )
                return

            if options['dry_run']:
                self.stdout.write(
                    f'DRY RUN: Would restore {count} {model.__name__} objects'
                )
                for obj in deleted_objects[:5]:  # Show first 5
                    self.stdout.write(f'  - {obj}')
                if count > 5:
                    self.stdout.write(f'  ... and {count - 5} more')
                return

            total_restored, message = model.bulk_restore(
                queryset=deleted_objects,
                cascade=options['cascade']
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {message} (Total: {total_restored})'
                )
            )

        elif options['pk']:
            # Restore specific object
            try:
                obj = model.objects.get(pk=options['pk'], is_deleted=True)
            except model.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'Deleted {model.__name__} with pk={options["pk"]} not found'
                    )
                )
                return

            if options['dry_run']:
                self.stdout.write(
                    f'DRY RUN: Would restore {obj}'
                )
                return

            success, message = obj.restore_instance(cascade=options['cascade'])

            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {message}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ {message}')
                )
        else:
            self.stdout.write(
                self.style.ERROR('Either --pk or --all is required')
            )

    def handle_list(self, options):
        """List all soft-deleted objects."""
        if options['model']:
            try:
                app_label, model_name = options['model'].split('.')
                model = apps.get_model(app_label, model_name)
                models_to_check = [model]
            except (ValueError, LookupError) as e:
                self.stdout.write(
                    self.style.ERROR(f'Invalid model: {options["model"]} - {e}')
                )
                return
        else:
            # Check all models
            models_to_check = []
            for app_config in apps.get_app_configs():
                for model in app_config.get_models():
                    if hasattr(model, 'is_deleted'):
                        models_to_check.append(model)

        total_deleted = 0

        self.stdout.write(
            self.style.SUCCESS('📋 Soft-Deleted Objects Report')
        )
        self.stdout.write('=' * 50)

        for model in models_to_check:
            if hasattr(model, 'objects'):
                deleted_count = model.objects.filter(is_deleted=True).count()
                if deleted_count > 0:
                    total_deleted += deleted_count
                    self.stdout.write(
                        f'{model.__name__}: {deleted_count} deleted objects'
                    )

                    # Show restoration status
                    if hasattr(model, 'is_restored'):
                        restored_count = model.objects.filter(
                            is_deleted=True, is_restored=True
                        ).count()
                        if restored_count > 0:
                            self.stdout.write(
                                f'  └── {restored_count} previously restored'
                            )

        self.stdout.write('=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'Total deleted objects: {total_deleted}')
        )

    def handle_history(self, options):
        """Show restoration history for an object."""
        if not options['model'] or not options['pk']:
            self.stdout.write(
                self.style.ERROR('Both --model and --pk are required for history')
            )
            return

        try:
            app_label, model_name = options['model'].split('.')
            model = apps.get_model(app_label, model_name)
            obj = model.objects.get(pk=options['pk'])
        except (ValueError, LookupError) as e:
            self.stdout.write(
                self.style.ERROR(f'Invalid model: {options["model"]} - {e}')
            )
            return
        except model.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'{model.__name__} with pk={options["pk"]} not found'
                )
            )
            return

        if not hasattr(obj, 'get_restoration_history'):
            self.stdout.write(
                self.style.ERROR(
                    f'Model {model.__name__} does not have restoration history methods'
                )
            )
            return

        history = obj.get_restoration_history()

        self.stdout.write(
            self.style.SUCCESS(f'📜 Restoration History for {obj}')
        )
        self.stdout.write('=' * 50)
        self.stdout.write(f'Currently Deleted: {history["is_currently_deleted"]}')
        self.stdout.write(f'Has Been Restored: {history["is_restored"]}')

        if history['last_restoration']:
            self.stdout.write(
                f'Last Restoration: {history["last_restoration"]}'
            )

        if history['last_deletion']:
            self.stdout.write(
                f'Last Deletion: {history["last_deletion"]}'
            )

        if history['deletion_restoration_cycle']:
            cycle = history['deletion_restoration_cycle']
            self.stdout.write('--- Latest Cycle ---')
            self.stdout.write(f'Deleted: {cycle["deleted_at"]}')
            self.stdout.write(f'Restored: {cycle["restored_at"]}')
            self.stdout.write(f'Duration: {cycle["cycle_duration"]}')

    def handle_cascade_restore(self, options):
        """Perform cascading restoration analysis."""
        self.stdout.write(
            self.style.SUCCESS('🔄 Cascading Restoration Analysis')
        )
        self.stdout.write('=' * 50)

        # Find models with restoration capabilities
        restorable_models = []
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                if (hasattr(model, 'is_deleted') and
                    hasattr(model, 'restore_instance')):
                    restorable_models.append(model)

        if not restorable_models:
            self.stdout.write(
                self.style.WARNING('No models with restoration capabilities found')
            )
            return

        self.stdout.write(f'Found {len(restorable_models)} restorable models:')

        for model in restorable_models:
            deleted_count = model.objects.filter(is_deleted=True).count()
            self.stdout.write(
                f'  - {model._meta.app_label}.{model.__name__}: '
                f'{deleted_count} deleted'
            )

        if options['all'] and not options['dry_run']:
            self.stdout.write('\n🚀 Starting cascading restoration...')

            total_restored = 0
            for model in restorable_models:
                deleted_objects = model.objects.filter(is_deleted=True)
                if deleted_objects.exists():
                    count, message = model.bulk_restore(
                        queryset=deleted_objects,
                        cascade=True
                    )
                    total_restored += count
                    self.stdout.write(f'  ✅ {model.__name__}: {message}')

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Total objects restored: {total_restored}'
                )
            )
        elif options['dry_run']:
            self.stdout.write(
                '\n🔍 DRY RUN: Use --all without --dry-run to execute'
            )
