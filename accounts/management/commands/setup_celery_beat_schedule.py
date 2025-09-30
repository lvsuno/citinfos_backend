"""
Management command to set up Celery Beat schedules in the database
This migrates from static CELERY_BEAT_SCHEDULE to dynamic database scheduling
Run with: python manage.py setup_celery_beat_schedule
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = 'Set up Celery Beat schedules in the database from settings.py'

    def add_arguments(self, parser):
        parser.add_argument('--clear-existing', action='store_true',
                          help='Clear all existing periodic tasks before creating new ones')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Setting up Celery Beat Database Schedules'))
        self.stdout.write('=' * 60)

        if options.get('clear_existing'):
            self.stdout.write('🗑️  Clearing existing periodic tasks...')
            deleted_count = PeriodicTask.objects.all().count()
            PeriodicTask.objects.all().delete()
            self.stdout.write(f'✅ Deleted {deleted_count} existing tasks')

        # Get schedules from settings
        schedules = getattr(settings, 'CELERY_BEAT_SCHEDULE', {})

        if not schedules:
            self.stdout.write(self.style.WARNING('⚠️  No CELERY_BEAT_SCHEDULE found in settings'))
            return

        created_count = 0
        updated_count = 0

        for task_name, task_config in schedules.items():
            self.stdout.write(f'\n📝 Processing: {task_name}')

            try:
                # Extract crontab schedule
                schedule_config = task_config['schedule']

                # Create or get crontab schedule
                if hasattr(schedule_config, 'minute'):
                    # It's a crontab object
                    crontab, created = CrontabSchedule.objects.get_or_create(
                        minute=schedule_config.minute,
                        hour=schedule_config.hour,
                        day_of_week=schedule_config.day_of_week,
                        day_of_month=schedule_config.day_of_month,
                        month_of_year=schedule_config.month_of_year,
                    )

                    if created:
                        self.stdout.write(f'   📅 Created crontab schedule: {crontab}')
                    else:
                        self.stdout.write(f'   📅 Found existing crontab schedule: {crontab}')

                    # Create or update periodic task
                    task, task_created = PeriodicTask.objects.get_or_create(
                        name=task_name,
                        defaults={
                            'task': task_config['task'],
                            'crontab': crontab,
                            'enabled': True,
                        }
                    )

                    if not task_created:
                        # Update existing task
                        task.task = task_config['task']
                        task.crontab = crontab
                        task.enabled = True
                        task.save()
                        updated_count += 1
                        self.stdout.write(f'   ✅ Updated task: {task_name}')
                    else:
                        created_count += 1
                        self.stdout.write(f'   ✅ Created task: {task_name}')

                    self.stdout.write(f'      Task: {task_config["task"]}')
                    self.stdout.write(f'      Schedule: {crontab}')

                else:
                    self.stdout.write(self.style.ERROR(f'   ❌ Unsupported schedule type for {task_name}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Error processing {task_name}: {e}'))

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🎉 Celery Beat Database Setup Complete!'))
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'   • Tasks created: {created_count}')
        self.stdout.write(f'   • Tasks updated: {updated_count}')
        self.stdout.write(f'   • Total tasks: {PeriodicTask.objects.count()}')

        self.stdout.write('\n💡 Next steps:')
        self.stdout.write('   1. Build and restart your Docker containers')
        self.stdout.write('   2. Run migrations: python manage.py migrate')
        self.stdout.write('   3. Start celery-beat service')
        self.stdout.write('   4. Check Django admin at /admin/django_celery_beat/')
        self.stdout.write('   5. Remove static CELERY_BEAT_SCHEDULE from settings.py (optional)')

        # Show current tasks
        self.stdout.write('\n📋 Current Database Tasks:')
        tasks = PeriodicTask.objects.all()
        for task in tasks:
            status = "✅ Enabled" if task.enabled else "❌ Disabled"
            self.stdout.write(f'   • {task.name}: {task.task} ({status})')
            self.stdout.write(f'     Schedule: {task.crontab}')
