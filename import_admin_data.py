#!/usr/bin/env python3
"""
Automated import script for Benin and Quebec administrative data.
This script will automatically detect and import all administrative levels
from separate folders for each country.

Expected folder structure:
/app/shapefiles/
├── benin/
│   ├── ben_admbnda_adm1_1m_salb_20190816.shp (departments)
│   ├── ben_admbnda_adm2_1m_salb_20190816_fixed.shp (communes)
│   └── ben_admbnda_adm3_1m_salb_20190816_corrected.shp (arrondissements)
└── quebec/
    ├── QUEBEC_region_s.shp (administrative regions)
    ├── QUEBEC_mrc_s.shp (MRCs)
    ├── QUEBEC_munic_s.shp (municipalities/territories)
    └── QUEBEC_arron_s.shp (arrondissements)
"""

import os
import sys
import django
from pathlib import Path
import logging

# Setup Django
project_root = Path(__file__).parent
sys.path.append(str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.contrib.gis.gdal import DataSource
from core.models import AdministrativeDivision, Country
from django.db import transaction

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_boundary_type_by_admin_level(admin_level):
    """Determine boundary type based on administrative level"""
    boundary_type_mapping = {
        0: 'international',  # Country level (international borders)
        1: 'state',         # State/Province/Department level
        2: 'regional',      # Region/Prefecture/MRC level
        3: 'municipal',     # Municipality/Commune level
        4: 'district',      # Arrondissement/District level
        5: 'other',         # Village/Local level
    }
    return boundary_type_mapping.get(admin_level, 'other')


def get_point_type_by_admin_level(admin_level):
    """Determine point type based on administrative level"""
    point_type_mapping = {
        0: 'office',        # Country level (national capital)
        1: 'office',        # State/Province administrative office
        2: 'prefecture',    # Regional/Prefecture headquarters
        3: 'city_hall',     # Municipal city hall
        4: 'office',        # District administrative office
        5: 'center',        # Local administrative center
    }
    return point_type_mapping.get(admin_level, 'other')


class AdminDataImporter:
    """Automated importer for administrative division data"""

    def __init__(self, base_path="/app/shapefiles"):
        self.base_path = Path(base_path)
        self.benin_path = self.base_path / "benin"
        self.quebec_path = self.base_path / "quebec"

        # Import counters
        self.total_imported = 0
        self.total_skipped = 0
        self.total_errors = 0

    def get_or_create_country(self, name, code):
        """Get or create a country"""
        country, created = Country.objects.get_or_create(
            code=code,
            defaults={'name': name}
        )
        if created:
            logger.info(f"Created country: {name}")
        return country

    def convert_to_multipolygon(self, geom):
        """Convert geometry to MultiPolygon if necessary"""
        if geom:
            geos_geom = GEOSGeometry(geom.wkt)
            if isinstance(geos_geom, Polygon):
                return MultiPolygon(geos_geom)
            return geos_geom
        return None

    def import_benin_data(self):
        """Import all Benin administrative levels"""
        logger.info("🇧🇯 STARTING BENIN DATA IMPORT")
        logger.info("=" * 40)

        if not self.benin_path.exists():
            logger.error(f"Benin data folder not found: {self.benin_path}")
            return False

        try:
            # Get Benin country
            benin = self.get_or_create_country("Benin", "BEN")

            # Clear existing Benin data
            existing_count = AdministrativeDivision.objects.filter(country=benin).count()
            if existing_count > 0:
                AdministrativeDivision.objects.filter(country=benin).delete()
                logger.info(f"Cleared {existing_count} existing Benin divisions")

            # Import Level 1: Departments
            self.import_benin_departments(benin)

            # Import Level 2: Communes
            self.import_benin_communes(benin)

            # Import Level 3: Arrondissements
            self.import_benin_arrondissements(benin)

            logger.info("🎉 BENIN IMPORT COMPLETE")
            return True

        except Exception as e:
            logger.error(f"Error importing Benin data: {e}")
            return False

    def import_benin_departments(self, benin):
        """Import Benin departments (Level 1)"""
        shapefile_path = self.benin_path / "ben_admbnda_adm1_1m_salb_20190816.shp"

        if not shapefile_path.exists():
            logger.warning(f"Benin departments shapefile not found: {shapefile_path}")
            return

        logger.info("📍 Importing Benin departments...")
        ds = DataSource(str(shapefile_path))
        layer = ds[0]

        imported = 0
        with transaction.atomic():
            for feature in layer:
                try:
                    name = feature.get('adm1_name') or feature.get('ADM1_NAME')
                    code = feature.get('adm1_code') or feature.get('ADM1_CODE')

                    if not name:
                        continue

                    geometry = self.convert_to_multipolygon(feature.geom)

                    AdministrativeDivision.objects.create(
                        country=benin,
                        admin_level=1,
                        name=str(name).strip(),
                        admin_code=str(code) if code else None,
                        area_geometry=geometry,
                        boundary_type=get_boundary_type_by_admin_level(1),
                        data_source="Benin SALB 2019"
                    )
                    imported += 1

                except Exception as e:
                    logger.error(f"Error importing department {name if 'name' in locals() else 'unknown'}: {e}")
                    self.total_errors += 1

        logger.info(f"✅ Imported {imported} Benin departments")
        self.total_imported += imported

    def import_benin_communes(self, benin):
        """Import Benin communes (Level 2)"""
        shapefile_path = self.benin_path / "ben_admbnda_adm2_1m_salb_20190816_fixed.shp"

        if not shapefile_path.exists():
            logger.warning(f"Benin communes shapefile not found: {shapefile_path}")
            return

        logger.info("🏘️ Importing Benin communes...")
        ds = DataSource(str(shapefile_path))
        layer = ds[0]

        # Get departments for parent mapping
        departments = {dept.name: dept for dept in AdministrativeDivision.objects.filter(country=benin, admin_level=1)}

        imported = 0
        with transaction.atomic():
            for feature in layer:
                try:
                    name = feature.get('adm2_name') or feature.get('ADM2_NAME')
                    code = feature.get('adm2_code') or feature.get('ADM2_CODE')
                    parent_name = feature.get('adm1_name') or feature.get('ADM1_NAME')

                    if not name:
                        continue

                    parent = departments.get(str(parent_name).strip()) if parent_name else None
                    geometry = self.convert_to_multipolygon(feature.geom)

                    AdministrativeDivision.objects.create(
                        country=benin,
                        admin_level=2,
                        name=str(name).strip(),
                        admin_code=str(code) if code else None,
                        parent=parent,
                        area_geometry=geometry,
                        boundary_type=get_boundary_type_by_admin_level(2),
                        data_source="Benin SALB 2019"
                    )
                    imported += 1

                except Exception as e:
                    logger.error(f"Error importing commune {name if 'name' in locals() else 'unknown'}: {e}")
                    self.total_errors += 1

        logger.info(f"✅ Imported {imported} Benin communes")
        self.total_imported += imported

    def import_benin_arrondissements(self, benin):
        """Import Benin arrondissements (Level 3)"""
        shapefile_path = self.benin_path / "ben_admbnda_adm3_1m_salb_20190816_corrected.shp"

        if not shapefile_path.exists():
            logger.warning(f"Benin arrondissements shapefile not found: {shapefile_path}")
            return

        logger.info("🏛️ Importing Benin arrondissements...")
        ds = DataSource(str(shapefile_path))
        layer = ds[0]

        # Get communes for parent mapping
        communes = {commune.name: commune for commune in AdministrativeDivision.objects.filter(country=benin, admin_level=2)}

        imported = 0
        with transaction.atomic():
            for feature in layer:
                try:
                    name = feature.get('adm3_name') or feature.get('ADM3_NAME')
                    code = feature.get('adm3_code') or feature.get('ADM3_CODE')
                    parent_name = feature.get('adm2_name') or feature.get('ADM2_NAME')

                    if not name:
                        continue

                    parent = communes.get(str(parent_name).strip()) if parent_name else None
                    geometry = self.convert_to_multipolygon(feature.geom)

                    AdministrativeDivision.objects.create(
                        country=benin,
                        admin_level=3,
                        name=str(name).strip(),
                        admin_code=str(code) if code else None,
                        parent=parent,
                        area_geometry=geometry,
                        boundary_type=get_boundary_type_by_admin_level(3),
                        data_source="Benin SALB 2019"
                    )
                    imported += 1

                except Exception as e:
                    logger.error(f"Error importing arrondissement {name if 'name' in locals() else 'unknown'}: {e}")
                    self.total_errors += 1

        logger.info(f"✅ Imported {imported} Benin arrondissements")
        self.total_imported += imported

    def import_quebec_data(self):
        """Import all Quebec administrative levels"""
        logger.info("🍁 STARTING QUEBEC DATA IMPORT")
        logger.info("=" * 40)

        if not self.quebec_path.exists():
            logger.error(f"Quebec data folder not found: {self.quebec_path}")
            return False

        try:
            # Get Canada country
            canada = self.get_or_create_country("Canada", "CAN")

            # Clear existing Canada data
            existing_count = AdministrativeDivision.objects.filter(country=canada).count()
            if existing_count > 0:
                AdministrativeDivision.objects.filter(country=canada).delete()
                logger.info(f"Cleared {existing_count} existing Canada divisions")

            # Create Quebec province (Level 1)
            self.create_quebec_province(canada)

            # Import Level 2: Administrative regions
            self.import_quebec_regions(canada)

            # Import Level 3: MRCs
            self.import_quebec_mrcs(canada)

            # Import Level 4: Municipalities/Territories
            self.import_quebec_municipalities(canada)

            # Import Level 5: Arrondissements
            self.import_quebec_arrondissements(canada)

            logger.info("🎉 QUEBEC IMPORT COMPLETE")
            return True

        except Exception as e:
            logger.error(f"Error importing Quebec data: {e}")
            return False

    def create_quebec_province(self, canada):
        """Create Quebec province as Level 1"""
        logger.info("🍁 Creating Quebec province...")

        quebec = AdministrativeDivision.objects.create(
            country=canada,
            admin_level=1,
            name="Quebec",
            admin_code="QC",
            boundary_type=get_boundary_type_by_admin_level(1),
            data_source="Quebec Administrative Data"
        )

        logger.info("✅ Created Quebec province")
        self.total_imported += 1
        return quebec

    def import_quebec_regions(self, canada):
        """Import Quebec administrative regions (Level 2)"""
        shapefile_path = self.quebec_path / "QUEBEC_region_s.shp"

        if not shapefile_path.exists():
            logger.warning(f"Quebec regions shapefile not found: {shapefile_path}")
            return

        logger.info("🗺️ Importing Quebec regions...")
        ds = DataSource(str(shapefile_path))
        layer = ds[0]

        quebec = AdministrativeDivision.objects.get(country=canada, admin_level=1, name="Quebec")

        imported = 0
        with transaction.atomic():
            for feature in layer:
                try:
                    name = feature.get('RES_NM_REG')
                    code = feature.get('RES_CO_REG')

                    if not name:
                        continue

                    geometry = self.convert_to_multipolygon(feature.geom)

                    AdministrativeDivision.objects.create(
                        country=canada,
                        admin_level=2,
                        name=str(name).strip(),
                        admin_code=str(code) if code else None,
                        parent=quebec,
                        area_geometry=geometry,
                        boundary_type=get_boundary_type_by_admin_level(2),
                        data_source="Quebec Regions Shapefile"
                    )
                    imported += 1

                except Exception as e:
                    logger.error(f"Error importing region {name if 'name' in locals() else 'unknown'}: {e}")
                    self.total_errors += 1

        logger.info(f"✅ Imported {imported} Quebec regions")
        self.total_imported += imported

    def import_quebec_mrcs(self, canada):
        """Import Quebec MRCs (Level 3)"""
        shapefile_path = self.quebec_path / "QUEBEC_mrc_s.shp"

        if not shapefile_path.exists():
            logger.warning(f"Quebec MRCs shapefile not found: {shapefile_path}")
            return

        logger.info("🏘️ Importing Quebec MRCs...")
        ds = DataSource(str(shapefile_path))
        layer = ds[0]

        # Get regions for parent mapping
        regions = {region.name: region for region in AdministrativeDivision.objects.filter(country=canada, admin_level=2)}

        imported = 0
        with transaction.atomic():
            for feature in layer:
                try:
                    name = feature.get('MRS_NM_MRC')
                    code = feature.get('MRS_CO_MRC')
                    parent_name = feature.get('MRS_NM_REG')

                    if not name:
                        continue

                    parent = regions.get(str(parent_name).strip()) if parent_name else None
                    geometry = self.convert_to_multipolygon(feature.geom)

                    AdministrativeDivision.objects.create(
                        country=canada,
                        admin_level=3,
                        name=str(name).strip(),
                        admin_code=str(code) if code else None,
                        parent=parent,
                        area_geometry=geometry,
                        boundary_type=get_boundary_type_by_admin_level(3),
                        data_source="Quebec MRCs Shapefile"
                    )
                    imported += 1

                except Exception as e:
                    logger.error(f"Error importing MRC {name if 'name' in locals() else 'unknown'}: {e}")
                    self.total_errors += 1

        logger.info(f"✅ Imported {imported} Quebec MRCs")
        self.total_imported += imported

    def import_quebec_municipalities(self, canada):
        """Import Quebec municipalities and territories (Level 4)"""
        shapefile_path = self.quebec_path / "QUEBEC_munic_s.shp"

        if not shapefile_path.exists():
            logger.warning(f"Quebec municipalities shapefile not found: {shapefile_path}")
            return

        logger.info("🏛️ Importing Quebec municipalities...")
        ds = DataSource(str(shapefile_path))
        layer = ds[0]

        # Get MRCs and regions for parent mapping
        mrcs = {mrc.name: mrc for mrc in AdministrativeDivision.objects.filter(country=canada, admin_level=3)}
        regions = {region.name: region for region in AdministrativeDivision.objects.filter(country=canada, admin_level=2)}
        quebec = AdministrativeDivision.objects.get(country=canada, admin_level=1, name="Quebec")

        imported = 0
        with transaction.atomic():
            for feature in layer:
                try:
                    name = feature.get('MUS_NM_MUN')
                    code = feature.get('MUS_CO_GEO')
                    mrc_name = feature.get('MUS_NM_MRC')
                    region_name = feature.get('MUS_NM_REG')

                    if not name:
                        continue

                    # Determine parent (MRC vs region for independent cities)
                    parent = None
                    name_clean = str(name).strip()
                    mrc_name_clean = str(mrc_name).strip() if mrc_name else None

                    if mrc_name_clean and name_clean.lower() == mrc_name_clean.lower():
                        # Independent city - parent is region
                        parent = regions.get(str(region_name).strip()) if region_name else quebec
                    else:
                        # Regular municipality - parent is MRC
                        parent = mrcs.get(mrc_name_clean) if mrc_name_clean else None

                    geometry = self.convert_to_multipolygon(feature.geom)

                    AdministrativeDivision.objects.create(
                        country=canada,
                        admin_level=4,
                        name=name_clean,
                        admin_code=str(code) if code else None,
                        parent=parent,
                        area_geometry=geometry,
                        boundary_type=get_boundary_type_by_admin_level(4),
                        data_source="Quebec Municipalities Shapefile"
                    )
                    imported += 1

                    if imported % 200 == 0:
                        logger.info(f"  Imported {imported} municipalities...")

                except Exception as e:
                    logger.error(f"Error importing municipality {name if 'name' in locals() else 'unknown'}: {e}")
                    self.total_errors += 1

        logger.info(f"✅ Imported {imported} Quebec municipalities")
        self.total_imported += imported

    def import_quebec_arrondissements(self, canada):
        """Import Quebec arrondissements (Level 5)"""
        shapefile_path = self.quebec_path / "QUEBEC_arron_s.shp"

        if not shapefile_path.exists():
            logger.warning(f"Quebec arrondissements shapefile not found: {shapefile_path}")
            return

        logger.info("🏘️ Importing Quebec arrondissements...")
        ds = DataSource(str(shapefile_path))
        layer = ds[0]

        # Get municipalities for parent mapping
        municipalities = {muni.name: muni for muni in AdministrativeDivision.objects.filter(country=canada, admin_level=4)}

        imported = 0
        with transaction.atomic():
            for feature in layer:
                try:
                    name = feature.get('ARS_NM_ARR')
                    code = feature.get('ARS_CO_ARR')
                    parent_name = feature.get('ARS_NM_MUN')

                    if not name:
                        continue

                    parent = municipalities.get(str(parent_name).strip()) if parent_name else None
                    geometry = self.convert_to_multipolygon(feature.geom)

                    AdministrativeDivision.objects.create(
                        country=canada,
                        admin_level=5,
                        name=str(name).strip(),
                        admin_code=str(code) if code else None,
                        parent=parent,
                        area_geometry=geometry,
                        boundary_type=get_boundary_type_by_admin_level(5),
                        data_source="Quebec Arrondissements Shapefile"
                    )
                    imported += 1

                except Exception as e:
                    logger.error(f"Error importing arrondissement {name if 'name' in locals() else 'unknown'}: {e}")
                    self.total_errors += 1

        logger.info(f"✅ Imported {imported} Quebec arrondissements")
        self.total_imported += imported

    def run_complete_import(self):
        """Run the complete import process for both countries"""
        logger.info("🌍 STARTING COMPLETE ADMINISTRATIVE DATA IMPORT")
        logger.info("=" * 55)

        # Import Benin data
        benin_success = self.import_benin_data()

        # Import Quebec data
        quebec_success = self.import_quebec_data()

        # Final summary
        logger.info("\n🎉 COMPLETE IMPORT SUMMARY")
        logger.info("=" * 30)
        logger.info(f"✅ Total imported: {self.total_imported}")
        logger.info(f"⏭️ Total skipped: {self.total_skipped}")
        logger.info(f"❌ Total errors: {self.total_errors}")
        logger.info(f"🌍 Benin: {'✅ SUCCESS' if benin_success else '❌ FAILED'}")
        logger.info(f"🍁 Quebec: {'✅ SUCCESS' if quebec_success else '❌ FAILED'}")

        return benin_success and quebec_success


def main():
    """Main function to run the import"""
    importer = AdminDataImporter()

    # Check if folders exist
    if not importer.benin_path.exists() and not importer.quebec_path.exists():
        logger.error("Neither Benin nor Quebec data folders found!")
        logger.error(f"Expected paths:")
        logger.error(f"  Benin: {importer.benin_path}")
        logger.error(f"  Quebec: {importer.quebec_path}")
        return False

    success = importer.run_complete_import()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)