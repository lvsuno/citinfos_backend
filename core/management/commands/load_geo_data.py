"""
Django management command for automated geographical data loading.

This command provides a reusable, automated way to load administrative
divisions from shapefiles with intelligent country and admin level detection.

Usage:
    python manage.py load_geo_data --shapefile path/to/file.shp --country CODE
    python manage.py load_geo_data --auto-detect path/to/directory/
    python manage.py load_geo_data --batch path/to/config.json
"""

import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal import DataSource
from django.db import transaction
from core.models import Country, AdministrativeDivision


class Command(BaseCommand):
    help = 'Load geographical administrative data with automated detection'

    def __init__(self):
        super().__init__()
        self.field_mappings = self.load_field_mappings()

    def load_field_mappings(self):
        """Load field mapping configurations"""
        mappings_file = Path('geo_data_mappings.json')
        if mappings_file.exists():
            with open(mappings_file, 'r') as f:
                return json.load(f)
        return {}

    def add_arguments(self, parser):
        # Single file loading
        parser.add_argument(
            '--shapefile',
            type=str,
            help='Path to shapefile to import'
        )

        parser.add_argument(
            '--country',
            type=str,
            help='Country ISO3 code (e.g., BEN, CAN)'
        )

        parser.add_argument(
            '--admin-level',
            type=int,
            help='Administrative level (0=country, 1=state, 2=region, etc.)'
        )

        parser.add_argument(
            '--geometry-type',
            choices=['area', 'boundary', 'point'],
            default='area',
            help='Type of geometry to import'
        )

        parser.add_argument(
            '--data-source',
            type=str,
            help='Data source description'
        )

        # Auto-detection mode
        parser.add_argument(
            '--auto-detect',
            type=str,
            help='Directory to scan for shapefiles with auto-detection'
        )

        # Batch processing mode
        parser.add_argument(
            '--batch',
            type=str,
            help='JSON file with batch import configuration'
        )

        # Options
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without making changes'
        )

        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing records'
        )

        parser.add_argument(
            '--mapping-file',
            type=str,
            help='Custom field mapping JSON file to use instead of default'
        )

    def handle(self, *args, **options):
        self.dry_run = options.get('dry_run', False)
        self.overwrite = options.get('overwrite', False)

        # Load custom mapping file if specified
        custom_mapping = options.get('mapping_file')
        if custom_mapping:
            self.field_mappings = self.load_custom_field_mappings(custom_mapping)

        if options['auto_detect']:
            self.auto_detect_and_load(options['auto_detect'])
        elif options['batch']:
            self.batch_load(options['batch'])
        elif options['shapefile']:
            self.load_single_file(options)
        else:
            raise CommandError(
                "Must specify --shapefile, --auto-detect, or --batch"
            )

    def load_custom_field_mappings(self, mapping_file):
        """Load custom field mapping file"""
        mapping_path = Path(mapping_file)
        if not mapping_path.exists():
            raise CommandError(f"Mapping file {mapping_file} does not exist")

        try:
            with open(mapping_path, 'r') as f:
                mappings = json.load(f)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Loaded custom mappings from {mapping_file}"
                    )
                )
                return mappings
        except (json.JSONDecodeError, IOError) as e:
            raise CommandError(f"Error loading mapping file: {e}")

    def load_single_file(self, options):
        """Load a single shapefile with provided parameters"""
        shapefile_path = options['shapefile']
        country_code = options['country']
        admin_level = options['admin_level']
        geometry_type = options.get('geometry_type', 'area')
        data_source = (
            options.get('data_source') or
            f'Imported from {Path(shapefile_path).name}'
        )

        if not Path(shapefile_path).exists():
            raise CommandError(f"Shapefile {shapefile_path} does not exist")

        self.stdout.write(f"Loading {shapefile_path}...")
        self.stdout.write(f"Parameters:")
        self.stdout.write(f"  Country: {country_code}")
        self.stdout.write(f"  Admin Level: {admin_level}")
        self.stdout.write(f"  Geometry Type: {geometry_type}")
        self.stdout.write(f"  Data Source: {data_source}")

        try:
            detection = {
                'shapefile_path': shapefile_path,
                'country_code': country_code,
                'admin_level': admin_level,
                'geometry_type': geometry_type,
                'data_source': data_source
            }

            if self.dry_run:
                self.stdout.write(
                    self.style.WARNING("DRY RUN - No data will be imported")
                )
                # Still try to analyze the file structure
                from django.contrib.gis.gdal import DataSource
                ds = DataSource(shapefile_path)
                layer = ds[0]
                self.stdout.write(f"  Features found: {len(layer)}")
                self.stdout.write(f"  Fields: {list(layer.fields)}")
            else:
                result = self.import_shapefile(**detection)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully imported {result['created']} records"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error loading shapefile: {e}")
            )
            raise CommandError(f"Failed to load {shapefile_path}") from e

    def auto_detect_and_load(self, directory):
        """Auto-detect and load all shapefiles in directory"""
        directory = Path(directory)
        if not directory.exists():
            raise CommandError(f"Directory {directory} does not exist")

        shapefiles = list(directory.rglob("*.shp"))
        if not shapefiles:
            raise CommandError(f"No shapefiles found in {directory}")

        self.stdout.write(f"Found {len(shapefiles)} shapefiles to analyze...")

        for shapefile_path in shapefiles:
            self.stdout.write(f"\nAnalyzing {shapefile_path}...")

            try:
                detection = self.detect_shapefile_properties(shapefile_path)
                if detection:
                    self.stdout.write(f"  Detected: {detection}")

                    if not self.dry_run:
                        result = self.import_shapefile(**detection)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  Imported {result['created']} records"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "  Could not auto-detect properties"
                        )
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  Error processing {shapefile_path}: {e}"
                    )
                )

    def detect_shapefile_properties(self, shapefile_path):
        """Enhanced detection using field mapping configurations"""
        try:
            ds = DataSource(str(shapefile_path))
            layer = ds[0]

            # Get filename for pattern matching
            filename = shapefile_path.name.lower()

            # Try to match against known data sources
            detected_source = self.detect_data_source(filename, layer)
            if not detected_source:
                return None

            # Get data source configuration
            source_config = self.field_mappings.get('data_sources', {}).get(
                detected_source
            )
            if not source_config:
                return None

            # Detect admin level based on filename patterns and fields
            detected_level = self.detect_admin_level(
                filename, layer, source_config
            )
            if detected_level is None:
                return None

            # Build detection result
            detection = {
                'shapefile_path': str(shapefile_path),
                'country_code': source_config['country_code'],
                'admin_level': detected_level,
                'data_source': f'Auto-imported from {shapefile_path.name}',
                'geometry_type': 'area'  # Default, can be enhanced
            }

            return detection

        except Exception as e:
            self.stdout.write(f"Error analyzing {shapefile_path}: {e}")
            return None

    def detect_data_source(self, filename, layer):
        """Detect which data source configuration matches"""
        if not self.field_mappings.get('data_sources'):
            return None

        for source_key, config in self.field_mappings['data_sources'].items():
            patterns = config.get('detection_patterns', {})

            # Check filename patterns
            filename_patterns = patterns.get('filename', [])
            if any(pattern in filename for pattern in filename_patterns):
                return source_key

            # Check field patterns
            field_patterns = patterns.get('fields', [])
            if field_patterns and len(layer) > 0:
                layer_fields = layer[0].fields

                matches = sum(
                    1 for pattern in field_patterns
                    if any(pattern.lower() in field.lower()
                          for field in layer_fields)
                )

                # If most patterns match, consider it a match
                if matches >= len(field_patterns) * 0.6:
                    return source_key

        return None

    def detect_admin_level(self, filename, layer, source_config):
        """Detect admin level using filename patterns and field analysis"""
        admin_levels = source_config.get('admin_levels', {})

        # First try filename patterns
        for level_str, level_config in admin_levels.items():
            filename_pattern = level_config.get('filename_pattern')
            if filename_pattern and filename_pattern in filename:
                return level_config['level']

        # Then try field analysis
        if len(layer) > 0:
            layer_fields = layer[0].fields

            for level_str, level_config in admin_levels.items():
                name_fields = level_config.get('name_fields', [])

                # Check if any expected name fields exist in the layer
                if any(field in layer_fields for field in name_fields):
                    return level_config['level']

        return None

    def import_shapefile(self, shapefile_path, country_code, admin_level,
                        geometry_type='area', data_source=None, **kwargs):
        """Import shapefile data using field mappings when available"""

        if self.dry_run:
            return {'created': 0, 'updated': 0}

        # Get or create country
        try:
            country = Country.objects.get(iso3=country_code)
        except Country.DoesNotExist:
            raise CommandError(
                f"Country {country_code} not found. Create it first."
            )

        ds = DataSource(shapefile_path)
        layer = ds[0]

        # Get field mappings for this data source if available
        field_config = self.get_field_config(
            shapefile_path, country_code, admin_level
        )

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for feature in layer:
                # Extract information using mappings or fallback
                name = self.extract_name(feature, admin_level, field_config)
                if not name:
                    continue

                admin_code = self.extract_admin_code(
                    feature, admin_level, field_config
                )

                # Find parent using mappings
                parent = self.find_parent_with_mapping(
                    feature, country, admin_level, field_config
                )

                # Get geometry
                geom = GEOSGeometry(feature.geom.wkt)

                # Convert Polygon to MultiPolygon if needed
                if geom.geom_type == 'Polygon':
                    from django.contrib.gis.geos import MultiPolygon
                    geom = MultiPolygon(geom)

                # Prepare geometry fields
                geometry_fields = {}
                if geometry_type == 'area':
                    geometry_fields['area_geometry'] = geom
                elif geometry_type == 'boundary':
                    geometry_fields['boundary_geometry'] = geom
                elif geometry_type == 'point':
                    geometry_fields['point_geometry'] = geom

                # Get boundary and point types
                boundary_type = self.get_boundary_type_by_admin_level(
                    admin_level, country_code, field_config, feature
                )
                point_type = self.get_point_type_by_admin_level(admin_level)

                # Create or update division
                # Use admin_code as primary lookup (matches DB constraint)
                lookup_fields = {
                    'admin_code': admin_code,
                    'country': country,
                    'admin_level': admin_level
                }

                division, created = (
                    AdministrativeDivision.objects.get_or_create(
                        **lookup_fields,
                        defaults={
                            'name': name,
                            'parent': parent,
                            'boundary_type': boundary_type,
                            'point_type': point_type,
                            'data_source': data_source,
                            **geometry_fields
                        }
                    )
                )

                if created:
                    created_count += 1
                elif self.overwrite:
                    # Update existing record
                    for field, value in geometry_fields.items():
                        setattr(division, field, value)
                    division.boundary_type = boundary_type
                    division.point_type = point_type
                    division.data_source = data_source
                    division.save()
                    updated_count += 1

        return {'created': created_count, 'updated': updated_count}

    def get_field_config(self, shapefile_path, country_code, admin_level):
        """Get field configuration for this shapefile using same logic as detect_data_source"""
        filename = Path(shapefile_path).name.lower()

        # Try to detect the correct data source first
        try:
            from django.contrib.gis.gdal import DataSource
            ds = DataSource(str(shapefile_path))
            layer = ds[0]
            detected_source = self.detect_data_source(filename, layer)

            if detected_source:
                source_config = self.field_mappings.get('data_sources', {}).get(detected_source)
                if source_config and source_config.get('country_code') == country_code:
                    level_config = source_config.get('admin_levels', {}).get(str(admin_level))
                    if level_config:
                        return level_config
        except Exception:
            pass

        # Fallback to original method
        for source_key, config in self.field_mappings.get(
            'data_sources', {}
        ).items():
            if config.get('country_code') != country_code:
                continue

            # Check if this source has config for this admin level
            level_config = config.get('admin_levels', {}).get(
                str(admin_level)
            )
            if not level_config:
                continue

            # Check filename pattern match
            filename_pattern = level_config.get('filename_pattern')
            if filename_pattern and filename_pattern in filename:
                return level_config

        return None

    def extract_name(self, feature, admin_level, field_config=None):
        """Extract name using field mappings or fallback"""
        if field_config:
            name_fields = field_config.get('name_fields', [])
        else:
            name_fields = [
                'name', 'NAME', 'Name',
                f'ADM{admin_level}_NAME', f'adm{admin_level}_name',
                'ADMIN_NAME', 'admin_name',
                # Quebec specific fields
                'RES_NM_REG', 'MRC_NOM', 'MUNICIP', 'NOM_ARRON'
            ]

        for field in name_fields:
            try:
                if field in feature.fields:
                    value = feature[field].value
                    if value and str(value).strip():
                        return str(value).strip()
            except Exception:
                # Try old method as fallback
                if hasattr(feature, field):
                    value = getattr(feature, field)
                    if value and str(value).strip():
                        return str(value).strip()

        return None

    def extract_admin_code(self, feature, admin_level, field_config=None):
        """Extract admin code using field mappings or fallback"""
        if field_config:
            code_fields = field_config.get('code_fields', [])
        else:
            code_fields = [
                'code', 'CODE', 'Code',
                f'ADM{admin_level}_CODE', f'adm{admin_level}_code',
                'ADMIN_CODE', 'admin_code',
                'RES_CO_REG',  # Quebec region codes
                'RES_CO_REF',  # Quebec reference codes
            ]

        for field in code_fields:
            if field in feature.fields:
                value = feature[field].value
                if value:
                    return str(value)

        return ''

    def find_parent_with_mapping(self, feature, country, admin_level,
                                 field_config=None):
        """Find parent using field mappings or fallback"""
        if admin_level <= 1:
            return None

        parent_field = None
        if field_config:
            parent_field = field_config.get('parent_field')

        if not parent_field:
            # Fallback to generic parent fields
            parent_fields = [
                f'ADM{admin_level-1}_NAME', f'adm{admin_level-1}_name',
                'PARENT_NAME', 'parent_name'
            ]
        else:
            parent_fields = [parent_field]

        for field in parent_fields:
            if field in feature.fields:
                parent_name = feature[field].value
                if parent_name and str(parent_name).strip():
                    try:
                        return AdministrativeDivision.objects.get(
                            name=str(parent_name).strip(),
                            country=country,
                            admin_level=admin_level-1
                        )
                    except AdministrativeDivision.DoesNotExist:
                        continue

        return None

    def get_boundary_type_by_admin_level(self, admin_level, country_code=None,
                                         field_config=None, feature=None):
        """Get boundary type based on admin level with dynamic country-specific types"""
        # First try to get from field config if available
        if field_config and 'boundary_type' in field_config:
            return field_config['boundary_type']

        # Try to extract from shapefile data if available
        if feature:
            boundary_type_fields = ['boundary_type', 'BOUNDARY_TYPE', 'type', 'TYPE']
            for field in boundary_type_fields:
                if field in feature.fields:
                    value = feature[field].value
                    if value and str(value).strip():
                        return str(value).strip().lower()

        # Try to get country-specific boundary type from data source config
        if country_code:
            for source_key, config in self.field_mappings.get('data_sources', {}).items():
                if config.get('country_code') == country_code:
                    boundary_types = config.get('boundary_types', {})
                    if str(admin_level) in boundary_types:
                        return boundary_types[str(admin_level)]

        # Fallback to generic mapping
        fallback_mapping = {
            0: 'international',
            1: 'state',
            2: 'regional',
            3: 'municipal',
            4: 'district',
            5: 'other',
        }
        return fallback_mapping.get(admin_level, 'other')

    def get_point_type_by_admin_level(self, admin_level):
        """Get point type based on admin level"""
        mapping = {
            0: 'office',
            1: 'office',
            2: 'prefecture',
            3: 'city_hall',
            4: 'office',
            5: 'center',
        }
        return mapping.get(admin_level, 'other')
