#!/usr/bin/env python3
"""
Import Quebec arrondissements (Level 5) as children of municipalities.
Expected: 41 arrondissements across 8 municipalities with ARS_NM_ARR (name), ARS_NM_MUN (parent municipality), ARS_CO_ARR (code) fields.
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


def import_quebec_arrondissements():
    """Import Quebec arrondissements as Level 5 administrative divisions"""

    print("🏘️ IMPORTING QUEBEC ARRONDISSEMENTS")
    print("=" * 42)

    # File path
    shapefile_path = "/app/shapefiles/QUEBEC_arron_s.shp"

    if not os.path.exists(shapefile_path):
        print(f"❌ Shapefile not found: {shapefile_path}")
        return False

    try:
        # Get Canada
        canada = Country.objects.get(name__icontains='Canada')
        print(f"📍 Country: {canada.name}")

        # Get all Quebec municipalities for parent mapping
        quebec_municipalities = {}
        municipalities = AdministrativeDivision.objects.filter(
            country=canada,
            admin_level=4
        )
        for muni in municipalities:
            quebec_municipalities[muni.name] = muni
        print(f"🏙️ Found {len(quebec_municipalities)} Quebec municipalities for parent mapping")

        # Open shapefile
        ds = DataSource(shapefile_path)
        layer = ds[0]

        print(f"📊 Found {len(layer)} arrondissement features")
        print(f"🗂️ Available fields: {layer.fields}")

        # Import counters
        imported_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for feature in layer:
                try:
                    # Get field values
                    arrondissement_name = feature.get('ARS_NM_ARR')
                    parent_municipality_name = feature.get('ARS_NM_MUN')
                    admin_code = feature.get('ARS_CO_ARR')

                    if not arrondissement_name:
                        print(f"⚠️ Skipping feature with no arrondissement name")
                        skipped_count += 1
                        continue

                    # Clean names
                    arrondissement_name = str(arrondissement_name).strip()

                    # Find parent municipality
                    parent_municipality = None
                    if parent_municipality_name:
                        parent_municipality_name_clean = str(parent_municipality_name).strip()
                        parent_municipality = quebec_municipalities.get(parent_municipality_name_clean)

                        if not parent_municipality:
                            # Try fuzzy matching
                            for muni_name, muni_obj in quebec_municipalities.items():
                                if (parent_municipality_name_clean.lower() in muni_name.lower() or
                                    muni_name.lower() in parent_municipality_name_clean.lower()):
                                    parent_municipality = muni_obj
                                    break

                    if not parent_municipality:
                        print(f"⚠️ Could not find parent municipality '{parent_municipality_name}' for arrondissement '{arrondissement_name}'")
                        continue

                    # Check if already exists
                    existing = AdministrativeDivision.objects.filter(
                        country=canada,
                        admin_level=5,
                        name=arrondissement_name,
                        parent=parent_municipality
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
                        print(f"⚠️ No geometry for arrondissement: {arrondissement_name}")
                        geos_geom = None

                    # Create arrondissement
                    arrondissement = AdministrativeDivision.objects.create(
                        country=canada,
                        admin_level=5,
                        name=arrondissement_name,
                        admin_code=str(admin_code) if admin_code else None,
                        parent=parent_municipality,
                        area_geometry=geos_geom,
                        data_source="Quebec Arrondissements Shapefile"
                    )

                    imported_count += 1
                    print(f"✅ {arrondissement_name} → {parent_municipality.name}")

                except Exception as e:
                    error_count += 1
                    arrondissement_name_safe = arrondissement_name if 'arrondissement_name' in locals() else 'unknown'
                    print(f"❌ Error processing arrondissement {arrondissement_name_safe}: {str(e)}")
                    continue

        # Final summary
        print(f"\n🎉 QUEBEC ARRONDISSEMENTS IMPORT COMPLETE")
        print(f"   ✅ Imported: {imported_count} arrondissements")
        print(f"   ⏭️ Skipped: {skipped_count} (already exist)")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total processed: {imported_count + skipped_count + error_count}")

        return True

    except Exception as e:
        print(f"❌ Fatal error during import: {str(e)}")
        return False


if __name__ == "__main__":
    success = import_quebec_arrondissements()
    sys.exit(0 if success else 1)