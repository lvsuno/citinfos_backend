#!/usr/bin/env python3
"""
Create Quebec province shapefile by merging all regions.
This creates a level 1 division from the union of all level 2 regions.
"""

import os
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from osgeo import ogr, osr
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon

def create_quebec_province_shapefile():
    """Create Quebec province shapefile from regions."""

    print("🍁 Creating Quebec Province Shapefile")
    print("=" * 50)

    # Paths
    regions_shp = Path('/app/shapefiles/quebec_adm/QUEBEC_regio_s.shp')
    output_dir = Path('/app/shapefiles/quebec_adm')
    output_shp = output_dir / 'QUEBEC_province_s.shp'

    if not regions_shp.exists():
        print(f"❌ Regions shapefile not found: {regions_shp}")
        return False

    print(f"✓ Reading regions from: {regions_shp}")

    # Read all regions and merge their geometries
    ds = DataSource(str(regions_shp))
    layer = ds[0]

    print(f"  Found {len(layer)} regions")

    # Collect all geometries
    geometries = []
    for feature in layer:
        geom = feature.geom
        geos_geom = GEOSGeometry(geom.wkt)
        geometries.append(geos_geom)

    # Union all geometries to create province boundary
    print("  Merging all regions into province boundary...")
    quebec_geom = geometries[0]
    for geom in geometries[1:]:
        quebec_geom = quebec_geom.union(geom)

    # Ensure it's a MultiPolygon
    if quebec_geom.geom_type == 'Polygon':
        quebec_geom = MultiPolygon(quebec_geom)

    print(f"  ✓ Created province geometry: {quebec_geom.geom_type}")

    # Create output shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')

    # Remove existing shapefile if it exists
    if output_shp.exists():
        driver.DeleteDataSource(str(output_shp))
        print(f"  Removed existing shapefile")

    # Create new shapefile
    out_ds = driver.CreateDataSource(str(output_shp))

    # Create spatial reference (WGS84)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    # Create layer
    out_layer = out_ds.CreateLayer(
        'QUEBEC_province_s',
        srs,
        ogr.wkbMultiPolygon
    )

    # Add fields matching the expected structure
    fields = [
        ('PROV_NAME', ogr.OFTString, 100),
        ('PROV_CODE', ogr.OFTString, 10),
        ('PROV_ID', ogr.OFTString, 10),
    ]

    for field_name, field_type, width in fields:
        field_def = ogr.FieldDefn(field_name, field_type)
        if field_type == ogr.OFTString:
            field_def.SetWidth(width)
        out_layer.CreateField(field_def)

    # Create feature
    feature_def = out_layer.GetLayerDefn()
    feature = ogr.Feature(feature_def)

    # Set attributes
    feature.SetField('PROV_NAME', 'Québec')
    feature.SetField('PROV_CODE', 'QC')
    feature.SetField('PROV_ID', '24')

    # Set geometry
    ogr_geom = ogr.CreateGeometryFromWkt(quebec_geom.wkt)
    feature.SetGeometry(ogr_geom)

    # Add feature to layer
    out_layer.CreateFeature(feature)

    # Clean up
    feature = None
    out_ds = None

    print(f"✅ Created shapefile: {output_shp}")
    print(f"   - PROV_NAME: Québec")
    print(f"   - PROV_CODE: QC")
    print(f"   - PROV_ID: 24")
    print()

    # Verify the created file
    verify_ds = DataSource(str(output_shp))
    verify_layer = verify_ds[0]
    print(f"✓ Verification: {len(verify_layer)} feature(s) in output shapefile")

    for feat in verify_layer:
        print(f"  - Name: {feat['PROV_NAME'].value}")
        print(f"  - Code: {feat['PROV_CODE'].value}")
        print(f"  - Geometry type: {feat.geom.geom_type}")

    print()
    print("✅ Quebec province shapefile created successfully!")
    return True

if __name__ == '__main__':
    create_quebec_province_shapefile()
