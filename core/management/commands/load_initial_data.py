from django.core.management.base import BaseCommand
from django.core.management import call_command
from core.models import AdministrativeDivision
import os


class Command(BaseCommand):
    """Automatically load initial shapefile data if database is empty."""
    help = 'Load initial shapefile data for first-time setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if data already exists'
        )
        parser.add_argument(
            '--shapefiles-dir',
            type=str,
            default='/app/shapefiles',
            help='Directory containing shapefile data'
        )

    def handle(self, *args, **options):
        force_reload = options['force']
        shapefiles_dir = options['shapefiles_dir']

        # Check if we already have data
        if AdministrativeDivision.objects.exists() and not force_reload:
            count = AdministrativeDivision.objects.count()
            self.stdout.write(
                self.style.WARNING(
                    f'Administrative division data already exists ({count} records). '
                    'Use --force to reload.'
                )
            )
            return

        if force_reload:
            self.stdout.write('Force reload requested. Clearing existing data...')
            AdministrativeDivision.objects.all().delete()

        # Configuration for your shapefiles
        SHAPEFILE_CONFIGS = [
            {
                'filename': 'benin_admin.shp',
                'data_source': 'Benin Administrative Boundaries 2023',
                'admin_level': 1,
                'encoding': 'utf-8',
            },
            {
                'filename': 'quebec_admin.shp',
                'data_source': 'Quebec Administrative Regions 2023',
                'admin_level': 1,
                'encoding': 'utf-8',
            },
            # Add your other shapefiles here
            # {
            #     'filename': 'benin_cities.shp',
            #     'data_source': 'Benin Cities 2023',
            #     'admin_level': 3,
            #     'parent_name': 'Benin',  # Optional parent
            #     'encoding': 'utf-8',
            # },
        ]

        self.stdout.write('Loading initial shapefile data...')

        loaded_count = 0
        total_features = 0

        for config in SHAPEFILE_CONFIGS:
            shapefile_path = os.path.join(shapefiles_dir, config['filename'])

            if not os.path.exists(shapefile_path):
                self.stdout.write(
                    self.style.WARNING(
                        f'Shapefile not found: {shapefile_path}. Skipping.'
                    )
                )
                continue

            self.stdout.write(f'Importing {config["filename"]}...')

            try:
                # Call the import_shapefile command
                call_command(
                    'import_shapefile',
                    shapefile_path,
                    data_source=config['data_source'],
                    admin_level=config['admin_level'],
                    encoding=config.get('encoding', 'utf-8'),
                    parent_name=config.get('parent_name'),
                    verbosity=0,  # Reduce verbosity for cleaner output
                )

                loaded_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully imported {config["filename"]}'
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Failed to import {config["filename"]}: {e}'
                    )
                )
                continue

        # Final summary
        total_features = AdministrativeDivision.objects.count()

        if loaded_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'🎉 Initial data loading completed! '
                    f'Loaded {loaded_count} shapefiles with {total_features} features.'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'No shapefiles were loaded. Check file paths and try again.'
                )
            )

        return f'Loaded {loaded_count} shapefiles, {total_features} features total'