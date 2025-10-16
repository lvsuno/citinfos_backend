#!/usr/bin/env python3
"""
Import Quebec municipalities (Level 4) with proper parent MRC relationships.
Expected: ~1345 municipalities with MUS_NM_MUN (name), MUS_NM_MRC (parent MRC), MUS_CO_GEO (code) fields.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
project_root = Path(__file__).parent
sys.path.append(str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.contrib.gis.gdal import DataSource
from core.models import AdministrativeDivision, Country
from django.db import transaction

def import_quebec_municipalities():
    """Import Quebec municipalities from QUEBEC_munic_s.shp"""

    print("🏛️ IMPORTING QUEBEC MUNICIPALITIES")
    print("=" * 45)

    # File path
    shapefile_path = "/app/shapefiles/quebec_adm/QUEBEC_munic_s.shp"

    if not os.path.exists(shapefile_path):
        print(f"❌ Shapefile not found: {shapefile_path}")
        return False

    try:
        # Get Canada
        canada = Country.objects.get(name__icontains='Canada')
        print(f"📍 Country: {canada.name}")

        # Get Quebec province (our Level 1)
        quebec = AdministrativeDivision.objects.get(
            country=canada,
            admin_level=1,
            name__in=['Quebec', 'Québec']
        )
        print(f"🍁 Province: {quebec.name}")

        # Get all Quebec MRCs for parent mapping
        quebec_mrcs = {}
        mrcs = AdministrativeDivision.objects.filter(
            country=canada,
            admin_level=3,
            parent__parent=quebec  # MRCs are children of regions, which are children of Quebec
        )
        for mrc in mrcs:
            quebec_mrcs[mrc.name] = mrc
        print(f"🏘️ Found {len(quebec_mrcs)} Quebec MRCs for parent mapping")

        # Open shapefile
        ds = DataSource(shapefile_path)
        layer = ds[0]

        print(f"📊 Found {len(layer)} municipality features")
        print(f"🗂️ Available fields: {layer.fields}")

        # Import counters
        imported_count = 0
        skipped_count = 0
        error_count = 0

        for feature in layer:
            try:
                with transaction.atomic():
                    # Get field values
                    municipality_name = feature.get('MUS_NM_MUN')
                    parent_mrc_name = feature.get('MUS_NM_MRC')
                    admin_code = feature.get('MUS_CO_GEO')

                    if not municipality_name:
                        print(f"⚠️ Skipping feature with no municipality name")
                        skipped_count += 1
                        continue

                    # Clean municipality name
                    municipality_name = str(municipality_name).strip()

                    # Find parent MRC
                    parent_mrc = None
                    if parent_mrc_name:
                        parent_mrc_name_clean = str(parent_mrc_name).strip()
                        parent_mrc = quebec_mrcs.get(parent_mrc_name_clean)

                        if not parent_mrc:
                            # Try fuzzy matching
                            for mrc_name, mrc_obj in quebec_mrcs.items():
                                if parent_mrc_name_clean.lower() in mrc_name.lower() or mrc_name.lower() in parent_mrc_name_clean.lower():
                                    parent_mrc = mrc_obj
                                    break

                    if not parent_mrc:
                        print(f"⚠️ Could not find parent MRC '{parent_mrc_name}' for municipality '{municipality_name}'")
                        # Still import without parent for now

                    # Check if already exists
                    existing = AdministrativeDivision.objects.filter(
                        country=canada,
                        admin_level=4,
                        name=municipality_name,
                        parent=parent_mrc
                    ).first()

                    if existing:
                        skipped_count += 1
                        continue

                    # Get and process geometry
                    geom = feature.geom
                    if geom:
                        geos_geom = GEOSGeometry(geom.wkt)

                        # Convert to MultiPolygon if necessary
                        if isinstance(geos_geom, Polygon):
                            geos_geom = MultiPolygon(geos_geom)
                    else:
                        print(f"⚠️ No geometry for municipality: {municipality_name}")
                        geos_geom = None

                    # Create municipality
                    municipality = AdministrativeDivision.objects.create(
                        country=canada,
                        admin_level=4,
                        name=municipality_name,
                        admin_code=str(admin_code) if admin_code else None,
                        parent=parent_mrc,
                        area_geometry=geos_geom,
                        data_source="Quebec Municipalities Shapefile"
                    )

                    imported_count += 1

                    # Progress indicator
                    if imported_count % 100 == 0:
                        print(f"✅ Imported {imported_count} municipalities...")

            except Exception as e:
                error_count += 1
                print(f"❌ Error processing municipality {municipality_name if 'municipality_name' in locals() else 'unknown'}: {str(e)}")
                continue

        # Final summary
        print(f"\n🎉 QUEBEC MUNICIPALITIES IMPORT COMPLETE")
        print(f"   ✅ Imported: {imported_count} municipalities")
        print(f"   ⏭️ Skipped: {skipped_count} (already exist)")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total processed: {imported_count + skipped_count + error_count}")

        return True

    except Exception as e:
        print(f"❌ Fatal error during import: {str(e)}")
        return False

if __name__ == "__main__":
    success = import_quebec_municipalities()
    sys.exit(0 if success else 1)