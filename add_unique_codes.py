#!/usr/bin/env python3
"""
Add unique admin codes to the Benin ADM3 shapefile to avoid constraint violations.
This script will add a unique identifier for each arrondissement based on its position and name.
"""

import os
from osgeo import ogr, osr
import hashlib

def add_unique_codes_to_shapefile():
    """Add unique admin_code values to each feature in the ADM3 shapefile"""

    # File paths (Docker container paths)
    input_file = "/app/shapefiles/geoBoundaries-BEN-ADM3-final.shp"
    output_file = "/app/shapefiles/geoBoundaries-BEN-ADM3-coded.shp"

    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return False

    print(f"📖 Opening shapefile: {input_file}")

    # Open input shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    input_ds = driver.Open(input_file, 0)  # 0 = read-only

    if input_ds is None:
        print(f"❌ Could not open input shapefile")
        return False

    input_layer = input_ds.GetLayer()

    # Get layer definition
    layer_defn = input_layer.GetLayerDefn()
    field_count = layer_defn.GetFieldCount()

    print(f"📊 Input shapefile has {input_layer.GetFeatureCount()} features")
    print(f"📋 Fields: {[layer_defn.GetFieldDefn(i).GetName() for i in range(field_count)]}")

    # Create output shapefile
    if os.path.exists(output_file):
        driver.DeleteDataSource(output_file)

    output_ds = driver.CreateDataSource(output_file)
    if output_ds is None:
        print(f"❌ Could not create output shapefile")
        return False

    # Create output layer with same spatial reference
    srs = input_layer.GetSpatialRef()
    output_layer = output_ds.CreateLayer("adm3_coded", srs, ogr.wkbPolygon)

    # Copy all existing fields
    for i in range(field_count):
        field_defn = layer_defn.GetFieldDefn(i)
        output_layer.CreateField(field_defn)

    # Add admin_code field
    admin_code_field = ogr.FieldDefn("admin_code", ogr.OFTString)
    admin_code_field.SetWidth(20)
    result = output_layer.CreateField(admin_code_field)
    if result != 0:
        print(f"❌ Failed to create admin_code field")
        return False
    print("✅ Added admin_code field")

    # Get output layer definition
    output_layer_defn = output_layer.GetLayerDefn()

    print("🔄 Processing features and adding unique codes...")

    # Process each feature
    feature_count = 0
    codes_used = set()

    for input_feature in input_layer:
        feature_count += 1

        # Create output feature
        output_feature = ogr.Feature(output_layer_defn)

        # Copy all existing attributes
        for i in range(field_count):
            field_name = layer_defn.GetFieldDefn(i).GetName()
            value = input_feature.GetField(field_name)
            output_feature.SetField(field_name, value)

        # Generate unique admin code
        shape_name = input_feature.GetField('shapeName') or f"Feature_{feature_count}"
        parent_name = input_feature.GetField('parentName') or "Unknown"

        # Create base code from parent and shape name
        base_code = f"BEN-ADM3-{feature_count:03d}"

        # Ensure uniqueness
        admin_code = base_code
        counter = 1
        while admin_code in codes_used:
            admin_code = f"{base_code}-{counter}"
            counter += 1

        codes_used.add(admin_code)
        output_feature.SetField("admin_code", admin_code)

        # Copy geometry
        geometry = input_feature.GetGeometryRef()
        output_feature.SetGeometry(geometry)

        # Add feature to output layer
        output_layer.CreateFeature(output_feature)

        if feature_count <= 5:
            print(f"  ✅ {shape_name} ({parent_name}) → {admin_code}")
        elif feature_count == 6:
            print("  ...")

        output_feature = None
        input_feature = None

    # Clean up
    input_ds = None
    output_ds = None

    print(f"✅ Successfully processed {feature_count} features")
    print(f"📁 Output file: {output_file}")

    # Copy associated files (.dbf, .shx, .prj)
    base_input = input_file.replace('.shp', '')
    base_output = output_file.replace('.shp', '')

    for ext in ['.dbf', '.shx', '.prj']:
        src = base_input + ext
        dst = base_output + ext
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, dst)
            print(f"📋 Copied {ext} file")

    return True

if __name__ == "__main__":
    success = add_unique_codes_to_shapefile()
    if success:
        print("\n🎉 Unique codes added successfully!")
        print("🔄 You can now import with:")
        print("   docker compose exec backend python manage.py import_shapefile \\")
        print("     /app/shapefiles/geoBoundaries-BEN-ADM3-coded.shp \\")
        print("     --country BEN --admin-level 3 --geometry-type area \\")
        print("     --data-source 'GeoBoundaries ADM3 Coded' --parent-field parentName")
    else:
        print("\n❌ Failed to add unique codes")