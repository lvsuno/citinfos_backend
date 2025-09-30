#!/usr/bin/env python3
"""
Import Quebec MRCs (Regional County Municipalities) with correct field mapping
"""

import os
import django
from osgeo import ogr

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from core.models import Country, AdministrativeDivision


def import_quebec_mrcs():
    """Import Quebec MRCs with correct field mapping"""
    print('🍁 IMPORTING QUEBEC MRCs (Regional County Municipalities)')
    print('=' * 65)

    # Get Canada
    canada = Country.objects.get(name__icontains='Canada')

    # Open shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = driver.Open('/app/shapefiles/QUEBEC_mrc_s.shp', 0)
    layer = ds.GetLayer()

    print(f'Processing {layer.GetFeatureCount()} MRCs...')

    imported_count = 0
    skipped_count = 0

    for feature in layer:
        mrc_name = feature.GetField('MRS_NM_MRC')
        mrc_code = feature.GetField('MRS_CO_MRC')
        region_name = feature.GetField('MRS_NM_REG')
        geometry = feature.GetGeometryRef()

        if not mrc_name or not region_name:
            print(f'⚠️  Skipping feature with missing data')
            skipped_count += 1
            continue

        # Find parent region
        parent_region = AdministrativeDivision.objects.filter(
            country=canada,
            admin_level=2,
            name=region_name
        ).first()

        if not parent_region:
            print(f'⚠️  Parent region not found: {region_name} for MRC {mrc_name}')
            skipped_count += 1
            continue

        # Check if already exists
        existing = AdministrativeDivision.objects.filter(
            country=canada,
            admin_level=3,
            admin_code=mrc_code
        ).first()

        if existing:
            print(f'⚠️  Already exists: {mrc_name} ({mrc_code})')
            skipped_count += 1
            continue

        # Create new MRC
        from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
        geos_geom = GEOSGeometry(geometry.ExportToWkt())

        # Ensure it's a MultiPolygon
        if geos_geom.geom_type == 'Polygon':
            geos_geom = MultiPolygon([geos_geom])

        mrc = AdministrativeDivision.objects.create(
            country=canada,
            parent=parent_region,
            admin_level=3,
            name=mrc_name,
            admin_code=mrc_code,
            data_source='Quebec Administrative Data',
            area_geometry=geos_geom
        )

        print(f'✅ Imported: {mrc.name} ({mrc.admin_code}) → {parent_region.name}')
        imported_count += 1

    print(f'\n📊 Import Summary:')
    print(f'   Imported: {imported_count}')
    print(f'   Skipped: {skipped_count}')
    print(f'   Total: {imported_count + skipped_count}')

    return imported_count


if __name__ == '__main__':
    try:
        count = import_quebec_mrcs()
        if count > 0:
            print(f'\n🎉 Successfully imported {count} Quebec MRCs!')
        else:
            print('\n❌ No MRCs were imported')
    except Exception as e:
        print(f'\n❌ Error: {e}')