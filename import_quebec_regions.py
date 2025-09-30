#!/usr/bin/env python3
"""
Import Quebec administrative divisions with correct field mapping
"""

import os
import django
from osgeo import ogr

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from core.models import Country, AdministrativeDivision

def import_quebec_regions():
    """Import Quebec regions with correct field mapping"""
    print('🍁 IMPORTING QUEBEC REGIONS')
    print('=' * 40)

    # Get Canada and Quebec
    canada = Country.objects.get(name__icontains='Canada')
    quebec_province = AdministrativeDivision.objects.get(
        country=canada,
        admin_level=1,
        name='Quebec'
    )

    # Open shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = driver.Open('/app/shapefiles/QUEBEC_regio_s.shp', 0)
    layer = ds.GetLayer()

    print(f'Processing {layer.GetFeatureCount()} regions...')

    imported_count = 0
    skipped_count = 0

    for feature in layer:
        name = feature.GetField('RES_NM_REG')
        admin_code = feature.GetField('RES_CO_REG')
        geometry = feature.GetGeometryRef()

        if not name:
            print(f'⚠️  Skipping feature with no name')
            skipped_count += 1
            continue

        # Check if already exists
        existing = AdministrativeDivision.objects.filter(
            country=canada,
            admin_level=2,
            admin_code=admin_code
        ).first()

        if existing:
            print(f'⚠️  Already exists: {name} ({admin_code})')
            skipped_count += 1
            continue

        # Create new region
        from django.contrib.gis.geos import GEOSGeometry
        geos_geom = GEOSGeometry(geometry.ExportToWkt())

        # Ensure it's a MultiPolygon
        if geos_geom.geom_type == 'Polygon':
            from django.contrib.gis.geos import MultiPolygon
            geos_geom = MultiPolygon([geos_geom])

        region = AdministrativeDivision.objects.create(
            country=canada,
            parent=quebec_province,
            admin_level=2,
            name=name,
            admin_code=admin_code,
            data_source='Quebec Administrative Data',
            area_geometry=geos_geom
        )

        print(f'✅ Imported: {region.name} ({region.admin_code})')
        imported_count += 1

    print(f'\n📊 Import Summary:')
    print(f'   Imported: {imported_count}')
    print(f'   Skipped: {skipped_count}')
    print(f'   Total: {imported_count + skipped_count}')

    return imported_count

if __name__ == '__main__':
    try:
        count = import_quebec_regions()
        if count > 0:
            print(f'\n🎉 Successfully imported {count} Quebec regions!')
        else:
            print('\n❌ No regions were imported')
    except Exception as e:
        print(f'\n❌ Error: {e}')