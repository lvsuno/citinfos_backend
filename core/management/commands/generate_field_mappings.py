"""
Django management command for generating field mapping configurations.

This command analyzes shapefiles and generates JSON configuration templates
that users can customize for their specific data sources.

Usage:
    python manage.py generate_field_mappings --shapefile path/to/file.shp
    python manage.py generate_field_mappings --directory path/to/shapefiles/
    python manage.py generate_field_mappings --interactive
"""

import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.gdal import DataSource


class Command(BaseCommand):
    help = 'Generate field mapping configurations for shapefiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shapefile',
            type=str,
            help='Path to single shapefile to analyze'
        )

        parser.add_argument(
            '--directory',
            type=str,
            help='Directory containing shapefiles to analyze'
        )

        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Interactive mode to create custom mappings'
        )

        parser.add_argument(
            '--output',
            type=str,
            default='custom_field_mappings.json',
            help='Output file for generated mappings'
        )

        parser.add_argument(
            '--data-source-name',
            type=str,
            help='Name for the data source configuration'
        )

        parser.add_argument(
            '--country-code',
            type=str,
            help='Country ISO3 code for this data source'
        )

    def handle(self, *args, **options):
        if options['interactive']:
            self.interactive_mapping_generator()
        elif options['shapefile']:
            self.analyze_single_file(options)
        elif options['directory']:
            self.analyze_directory(options)
        else:
            raise CommandError(
                "Must specify --shapefile, --directory, or --interactive"
            )

    def analyze_single_file(self, options):
        """Analyze a single shapefile and generate mapping"""
        shapefile_path = Path(options['shapefile'])
        if not shapefile_path.exists():
            raise CommandError(f"Shapefile {shapefile_path} does not exist")

        self.stdout.write(f"Analyzing {shapefile_path}...")
        mapping = self.generate_mapping_for_file(
            shapefile_path,
            options.get('data_source_name'),
            options.get('country_code')
        )

        self.save_mapping(mapping, options['output'])

    def analyze_directory(self, options):
        """Analyze all shapefiles in directory"""
        directory = Path(options['directory'])
        if not directory.exists():
            raise CommandError(f"Directory {directory} does not exist")

        shapefiles = list(directory.glob("*.shp"))
        if not shapefiles:
            raise CommandError(f"No shapefiles found in {directory}")

        self.stdout.write(f"Found {len(shapefiles)} shapefiles to analyze...")

        mappings = {
            "description": f"Generated mappings for {directory.name}",
            "version": "1.0",
            "data_sources": {}
        }

        for shapefile_path in shapefiles:
            self.stdout.write(f"  Analyzing {shapefile_path.name}...")

            file_mapping = self.generate_mapping_for_file(
                shapefile_path,
                f"{directory.name}_{shapefile_path.stem}",
                options.get('country_code')
            )

            if file_mapping:
                source_name = f"{directory.name}_{shapefile_path.stem}"
                mappings['data_sources'][source_name] = file_mapping

        self.save_mapping(mappings, options['output'])

    def generate_mapping_for_file(self, shapefile_path, data_source_name=None,
                                 country_code=None):
        """Generate mapping configuration for a single file"""
        try:
            ds = DataSource(str(shapefile_path))
            layer = ds[0]

            if len(layer) == 0:
                self.stdout.write(
                    self.style.WARNING(f"  No features in {shapefile_path}")
                )
                return None

            # Get field information
            feature = layer[0]
            fields = feature.fields

            # Analyze field content
            field_analysis = {}
            for field_name in fields:
                field_value = feature.get(field_name)
                field_analysis[field_name] = {
                    'type': type(field_value).__name__,
                    'sample_value': str(field_value)[:50] if field_value else None
                }

            # Generate suggested mapping
            suggested_mapping = self.suggest_field_mapping(
                fields, field_analysis, shapefile_path.name
            )

            # Build configuration
            config = {
                'description': f'Generated from {shapefile_path.name}',
                'country_code': country_code or 'UNKNOWN',
                'detection_patterns': {
                    'filename': [shapefile_path.stem.lower()],
                    'fields': list(fields)[:5]  # First 5 fields as patterns
                },
                'admin_levels': {
                    str(suggested_mapping['admin_level']): {
                        'level': suggested_mapping['admin_level'],
                        'name_fields': suggested_mapping['name_fields'],
                        'code_fields': suggested_mapping['code_fields'],
                        'parent_field': suggested_mapping.get('parent_field'),
                        'boundary_type': suggested_mapping['boundary_type'],
                        'filename_pattern': self.extract_pattern(
                            shapefile_path.name
                        )
                    }
                },
                '_field_analysis': field_analysis  # For user reference
            }

            return config

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error analyzing {shapefile_path}: {e}")
            )
            return None

    def suggest_field_mapping(self, fields, field_analysis, filename):
        """Suggest field mappings based on field names and content"""
        # Common name field patterns
        name_patterns = ['name', 'nom', 'nm_', 'label', 'admin', 'region']
        code_patterns = ['code', 'co_', 'id', 'geo', 'cd_', 'no_']
        parent_patterns = ['parent', 'adm', 'region', 'province']

        # Find potential name fields
        name_fields = []
        for field in fields:
            field_lower = field.lower()
            if any(pattern in field_lower for pattern in name_patterns):
                name_fields.append(field)

        # Find potential code fields
        code_fields = []
        for field in fields:
            field_lower = field.lower()
            if any(pattern in field_lower for pattern in code_patterns):
                code_fields.append(field)

        # Detect admin level from filename
        filename_lower = filename.lower()
        admin_level = 3  # Default

        if any(pattern in filename_lower for pattern in ['adm0', 'country']):
            admin_level = 0
        elif any(pattern in filename_lower for pattern in ['adm1', 'state', 'province', 'regio']):
            admin_level = 2
        elif any(pattern in filename_lower for pattern in ['adm2', 'mrc', 'prefecture']):
            admin_level = 3
        elif any(pattern in filename_lower for pattern in ['adm3', 'munic', 'commune']):
            admin_level = 4
        elif any(pattern in filename_lower for pattern in ['adm4', 'arron', 'district']):
            admin_level = 5

        # Determine boundary type
        boundary_types = {
            0: 'international',
            1: 'state',
            2: 'regional',
            3: 'municipal',
            4: 'district',
            5: 'other'
        }

        return {
            'admin_level': admin_level,
            'name_fields': name_fields[:3],  # Top 3 candidates
            'code_fields': code_fields[:3],  # Top 3 candidates
            'parent_field': None,  # User needs to specify
            'boundary_type': boundary_types.get(admin_level, 'other')
        }

    def extract_pattern(self, filename):
        """Extract a pattern from filename for detection"""
        # Remove common prefixes/suffixes and extract middle part
        name = filename.lower().replace('.shp', '')

        # Common patterns to extract
        patterns = ['adm0', 'adm1', 'adm2', 'adm3', 'adm4',
                   'regio', 'munic', 'arron', 'mrc', 'country']

        for pattern in patterns:
            if pattern in name:
                return pattern

        return name.split('_')[-1] if '_' in name else name

    def interactive_mapping_generator(self):
        """Interactive mode to create custom mappings"""
        self.stdout.write(
            self.style.SUCCESS("🔧 Interactive Field Mapping Generator")
        )
        self.stdout.write("=" * 50)

        # Get basic information
        data_source_name = input("Data source name: ")
        country_code = input("Country ISO3 code (e.g., BEN, CAN): ").upper()
        description = input("Description: ")

        # Get detection patterns
        self.stdout.write("\nDetection Patterns:")
        filename_patterns = input("Filename patterns (comma-separated): ").split(',')
        filename_patterns = [p.strip() for p in filename_patterns if p.strip()]

        # Configure admin levels
        admin_levels = {}

        while True:
            level = input(f"\nAdmin level (0-5, or 'done' to finish): ")
            if level.lower() == 'done':
                break

            try:
                level_num = int(level)
                if 0 <= level_num <= 5:
                    level_config = self.configure_admin_level(level_num)
                    admin_levels[str(level_num)] = level_config
                else:
                    self.stdout.write("Please enter a level between 0-5")
            except ValueError:
                self.stdout.write("Please enter a valid number or 'done'")

        # Build final configuration
        mapping = {
            "description": "Custom field mappings",
            "version": "1.0",
            "data_sources": {
                data_source_name: {
                    "description": description,
                    "country_code": country_code,
                    "detection_patterns": {
                        "filename": filename_patterns
                    },
                    "admin_levels": admin_levels
                }
            }
        }

        # Save configuration
        output_file = input("\nOutput filename [custom_field_mappings.json]: ")
        output_file = output_file.strip() or "custom_field_mappings.json"

        self.save_mapping(mapping, output_file)

    def configure_admin_level(self, level):
        """Configure a single admin level interactively"""
        self.stdout.write(f"\nConfiguring admin level {level}:")

        # Get field mappings
        name_fields = input("Name fields (comma-separated): ").split(',')
        name_fields = [f.strip() for f in name_fields if f.strip()]

        code_fields = input("Code fields (comma-separated): ").split(',')
        code_fields = [f.strip() for f in code_fields if f.strip()]

        parent_field = input("Parent field (optional): ").strip() or None
        filename_pattern = input("Filename pattern (optional): ").strip() or None

        boundary_types = {
            0: 'international',
            1: 'state',
            2: 'regional',
            3: 'municipal',
            4: 'district',
            5: 'other'
        }

        return {
            'level': level,
            'name_fields': name_fields,
            'code_fields': code_fields,
            'parent_field': parent_field,
            'boundary_type': boundary_types.get(level, 'other'),
            'filename_pattern': filename_pattern
        }

    def save_mapping(self, mapping, output_file):
        """Save mapping configuration to file"""
        output_path = Path(output_file)

        with open(output_path, 'w') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Mapping saved to {output_path}")
        )

        self.stdout.write("\nTo use this mapping:")
        self.stdout.write(f"1. Review and edit {output_path}")
        self.stdout.write("2. Copy to geo_data_mappings.json or specify with --mapping-file")
        self.stdout.write("3. Run: python manage.py load_geo_data --auto-detect /path/to/shapefiles/")