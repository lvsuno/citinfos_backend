#!/usr/bin/env python3
"""
Import Quebec municipalities (Level 4) with corrected parent relationships.
Independent cities (where municipality name = MRC name) should have no MRC parent.
Regular municipalities belong to MRCs.
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


def import_quebec_municipalities_corrected():
    """Import Quebec municipalities with correct parent relationships"""

    print("🏛️ IMPORTING QUEBEC MUNICIPALITIES - CORRECTED")
    print("=" * 52)

    # File path
    shapefile_path = "/app/shapefiles/QUEBEC_munic_s.shp"

    if not os.path.exists(shapefile_path):
        print(f"❌ Shapefile not found: {shapefile_path}")
        return False

    try:
        # Get Canada and Quebec
        canada = Country.objects.get(name__icontains='Canada')
        quebec = AdministrativeDivision.objects.get(
            country=canada,
            admin_level=1,
            name='Quebec'
        )
        print(f"📍 Country: {canada.name}")
        print(f"🍁 Province: {quebec.name}")

        # Get all Quebec MRCs and regions for parent mapping
        quebec_mrcs = {}
        quebec_regions = {}

        # Load MRCs (admin_level=3)
        mrcs = AdministrativeDivision.objects.filter(
            country=canada,
            admin_level=3,
            parent__parent=quebec
        )
        for mrc in mrcs:
            quebec_mrcs[mrc.name] = mrc

        # Load regions (admin_level=2) for independent cities
        regions = AdministrativeDivision.objects.filter(
            country=canada,
            admin_level=2,
            parent=quebec
        )
        for region in regions:
            quebec_regions[region.name] = region

        print(f"🏘️ Found {len(quebec_mrcs)} Quebec MRCs")
        print(f"🗺️ Found {len(quebec_regions)} Quebec regions")

        # Clear existing municipalities to re-import correctly
        existing_munis = AdministrativeDivision.objects.filter(
            country=canada,
            admin_level=4
        )
        deleted_count = existing_munis.count()
        existing_munis.delete()
        print(f"🧹 Cleared {deleted_count} existing municipalities for re-import")

        # Open shapefile
        ds = DataSource(shapefile_path)
        layer = ds[0]

        print(f"📊 Found {len(layer)} municipality features")

        # Import counters
        imported_regular = 0  # Regular municipalities with MRC parents
        imported_independent = 0  # Independent cities without MRC parents
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for feature in layer:
                try:
                    # Get field values
                    municipality_name = feature.get('MUS_NM_MUN')
                    parent_mrc_name = feature.get('MUS_NM_MRC')
                    admin_code = feature.get('MUS_CO_GEO')
                    muni_type = feature.get('MUS_CO_DES')
                    region_name = feature.get('MUS_NM_REG')

                    if not municipality_name:
                        print(f"⚠️ Skipping feature with no municipality name")
                        skipped_count += 1
                        continue

                    # Clean names
                    municipality_name = str(municipality_name).strip()
                    parent_mrc_name = str(parent_mrc_name).strip() if parent_mrc_name else None
                    region_name = str(region_name).strip() if region_name else None

                    # Determine if this is an independent city
                    is_independent = False
                    parent = None

                    if parent_mrc_name:
                        # Check if municipality name matches MRC name (independent city)
                        if municipality_name.lower() == parent_mrc_name.lower():
                            is_independent = True
                            # Independent cities are children of regions, not MRCs
                            if region_name and region_name in quebec_regions:
                                parent = quebec_regions[region_name]
                                print(f"🏙️ Independent city: {municipality_name} → {region_name}")
                            else:
                                print(f"⚠️ Independent city {municipality_name} - region '{region_name}' not found")
                                parent = quebec  # Fall back to Quebec province
                        else:
                            # Regular municipality - find MRC parent
                            parent = quebec_mrcs.get(parent_mrc_name)
                            if not parent:
                                # Try fuzzy matching
                                for mrc_name, mrc_obj in quebec_mrcs.items():
                                    if (parent_mrc_name.lower() in mrc_name.lower() or
                                        mrc_name.lower() in parent_mrc_name.lower()):
                                        parent = mrc_obj
                                        break

                            if not parent:
                                print(f"⚠️ Could not find MRC '{parent_mrc_name}' for municipality '{municipality_name}'")

                    # Get and process geometry
                    geom = feature.geom
                    if geom:
                        geos_geom = GEOSGeometry(geom.wkt)
                        if isinstance(geos_geom, Polygon):
                            geos_geom = MultiPolygon(geos_geom)
                    else:
                        geos_geom = None

                    # Create municipality
                    municipality = AdministrativeDivision.objects.create(
                        country=canada,
                        admin_level=4,
                        name=municipality_name,
                        admin_code=str(admin_code) if admin_code else None,
                        parent=parent,
                        area_geometry=geos_geom,
                        data_source="Quebec Municipalities Shapefile - Corrected"
                    )

                    if is_independent:
                        imported_independent += 1
                    else:
                        imported_regular += 1

                    # Progress indicator
                    total_imported = imported_regular + imported_independent
                    if total_imported % 100 == 0:
                        print(f"✅ Imported {total_imported} municipalities ({imported_regular} regular + {imported_independent} independent)...")

                except Exception as e:
                    error_count += 1
                    municipality_name_safe = municipality_name if 'municipality_name' in locals() else 'unknown'
                    print(f"❌ Error processing municipality {municipality_name_safe}: {str(e)}")
                    continue

        # Final summary
        total_imported = imported_regular + imported_independent
        print(f"\n🎉 QUEBEC MUNICIPALITIES IMPORT COMPLETE")
        print(f"   🏘️ Regular municipalities (with MRC parents): {imported_regular}")
        print(f"   🏙️ Independent cities (with region/province parents): {imported_independent}")
        print(f"   ✅ Total imported: {total_imported}")
        print(f"   ⏭️ Skipped: {skipped_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total processed: {total_imported + skipped_count + error_count}")

        return True

    except Exception as e:
        print(f"❌ Fatal error during import: {str(e)}")
        return False


if __name__ == "__main__":
    success = import_quebec_municipalities_corrected()
    sys.exit(0 if success else 1)