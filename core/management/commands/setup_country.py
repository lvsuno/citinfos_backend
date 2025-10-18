"""
Django management command for setting up new countries and their geo data.

This command helps initialize new countries with their basic information
and administrative divisions.

Usage:
    python manage.py setup_country --iso3 BEN --name "Benin" --iso2 BJ
    python manage.py setup_country --from-shapefile path/to/country.shp
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from core.models import Country, AdministrativeDivision
from core.country_data import get_country_info


class Command(BaseCommand):
    help = 'Setup new countries with basic information and optional geo data'

    def add_arguments(self, parser):
        # Manual country setup
        parser.add_argument(
            '--iso3',
            type=str,
            help='ISO3 country code (e.g., BEN, CAN, FRA)'
        )

        parser.add_argument(
            '--iso2',
            type=str,
            help='ISO2 country code (e.g., BJ, CA, FR)'
        )

        parser.add_argument(
            '--name',
            type=str,
            help='Country name (e.g., "Benin", "Canada")'
        )

        parser.add_argument(
            '--code',
            type=int,
            help='Numeric country code (optional)'
        )

        parser.add_argument(
            '--default-admin-level',
            type=int,
            help='Default admin level (3=communes, 4=municipalities)'
        )

        # Shapefile-based setup
        parser.add_argument(
            '--from-shapefile',
            type=str,
            help='Setup country from ADM0 level shapefile'
        )

        parser.add_argument(
            '--data-source',
            type=str,
            help='Data source description'
        )

        # Options
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing country if it exists'
        )

    def handle(self, *args, **options):
        if options.get('from_shapefile'):
            self.setup_from_shapefile(options)
        elif options.get('iso3') and options.get('name'):
            self.setup_manual(options)
        else:
            raise CommandError(
                "Must specify either --from-shapefile or "
                "--iso3 and --name for manual setup"
            )

    def setup_manual(self, options):
        """Setup country manually with provided parameters"""
        iso3 = options['iso3'].upper()
        iso2 = options.get('iso2', '').upper()
        name = options['name']
        code = options.get('code')
        default_admin_level = options.get('default_admin_level')
        overwrite = options.get('overwrite', False)

        # Validate ISO codes
        if len(iso3) != 3:
            raise CommandError("ISO3 code must be exactly 3 characters")
        if iso2 and len(iso2) != 2:
            raise CommandError("ISO2 code must be exactly 2 characters")

        # Check if country exists
        existing = Country.objects.filter(iso3=iso3).first()
        if existing and not overwrite:
            raise CommandError(
                f"Country {iso3} already exists. Use --overwrite to update."
            )

        # Get country info from lookup table
        country_info = get_country_info(iso3)

        # Create or update country
        defaults_dict = {
            'iso2': iso2,
            'name': name,
            'code': code,
        }

        # Add phone data from country_data if available
        if country_info:
            if not iso2:
                defaults_dict['iso2'] = country_info.get('iso2')
            defaults_dict['phone_code'] = country_info.get('phone_code')
            defaults_dict['flag_emoji'] = country_info.get('flag_emoji')
            defaults_dict['region'] = country_info.get('region')

        if default_admin_level is not None:
            defaults_dict['default_admin_level'] = default_admin_level

        country, created = Country.objects.update_or_create(
            iso3=iso3,
            defaults=defaults_dict
        )

        action = "Created" if created else "Updated"
        phone_info = (
            f"{country.flag_emoji} {country.phone_code}"
            if country.flag_emoji and country.phone_code
            else ""
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} country: {country.name} ({country.iso3}) "
                f"{phone_info}"
            )
        )

    def setup_from_shapefile(self, options):
        """Setup country from ADM0 level shapefile"""
        shapefile_path = options['from_shapefile']
        data_source = options.get('data_source',
                                f'Imported from {shapefile_path}')
        overwrite = options.get('overwrite', False)

        try:
            ds = DataSource(shapefile_path)
            layer = ds[0]
        except Exception as e:
            raise CommandError(f"Error reading shapefile: {e}")

        created_countries = []
        created_divisions = []

        with transaction.atomic():
            for feature in layer:
                # Extract country information
                country_info = self.extract_country_info(feature)
                if not country_info:
                    continue

                # Check if country exists
                existing = Country.objects.filter(
                    iso3=country_info['iso3']
                ).first()

                if existing and not overwrite:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Country {country_info['iso3']} already exists, "
                            "skipping..."
                        )
                    )
                    continue

                # Create or update country
                country, created = Country.objects.update_or_create(
                    iso3=country_info['iso3'],
                    defaults={
                        'iso2': country_info.get('iso2', ''),
                        'name': country_info['name'],
                        'code': country_info.get('code'),
                    }
                )

                if created:
                    created_countries.append(country)

                # Create Level 0 administrative division with geometry
                geom = GEOSGeometry(feature.geom.wkt)

                division, div_created = AdministrativeDivision.objects.update_or_create(
                    name=country_info['name'],
                    country=country,
                    admin_level=0,
                    defaults={
                        'admin_code': country_info.get('code', ''),
                        'area_geometry': geom,
                        'boundary_type': 'international',
                        'point_type': 'office',
                        'data_source': data_source,
                    }
                )

                if div_created:
                    created_divisions.append(division)

        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(created_countries)} countries and "
                f"{len(created_divisions)} Level 0 divisions"
            )
        )

        for country in created_countries:
            self.stdout.write(f"  - {country.name} ({country.iso3})")

    def extract_country_info(self, feature):
        """Extract country information from shapefile feature"""
        # Common field names for country information
        name_fields = [
            'NAME', 'name', 'Name',
            'ADMIN', 'admin', 'Admin',
            'COUNTRY', 'country', 'Country',
            'NAME_EN', 'name_en'
        ]

        iso3_fields = [
            'ISO3', 'iso3', 'Iso3',
            'ISO_A3', 'iso_a3',
            'ADM0_A3', 'adm0_a3'
        ]

        iso2_fields = [
            'ISO2', 'iso2', 'Iso2',
            'ISO_A2', 'iso_a2',
            'ADM0_A2', 'adm0_a2'
        ]

        code_fields = [
            'CODE', 'code', 'Code',
            'ISO_N3', 'iso_n3',
            'UN_A3', 'un_a3'
        ]

        # Extract name
        name = None
        for field in name_fields:
            if hasattr(feature, field):
                value = getattr(feature, field)
                if value and str(value).strip():
                    name = str(value).strip()
                    break

        if not name:
            return None

        # Extract ISO3
        iso3 = None
        for field in iso3_fields:
            if hasattr(feature, field):
                value = getattr(feature, field)
                if value and len(str(value).strip()) == 3:
                    iso3 = str(value).strip().upper()
                    break

        if not iso3:
            return None

        # Extract ISO2 (optional)
        iso2 = ''
        for field in iso2_fields:
            if hasattr(feature, field):
                value = getattr(feature, field)
                if value and len(str(value).strip()) == 2:
                    iso2 = str(value).strip().upper()
                    break

        # Extract numeric code (optional)
        code = None
        for field in code_fields:
            if hasattr(feature, field):
                value = getattr(feature, field)
                if value:
                    try:
                        code = int(value)
                        break
                    except (ValueError, TypeError):
                        continue

        return {
            'name': name,
            'iso3': iso3,
            'iso2': iso2,
            'code': code
        }