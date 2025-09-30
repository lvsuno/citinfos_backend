#!/usr/bin/env python3
"""
Fix Ganviè encoding issues and set correct parent commune for Ganvié I.
"""

import os
import shutil
from osgeo import ogr
import django
import sys

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()


def fix_ganvie_issues(input_path, output_path):
    """Fix Ganviè encoding and parent commune assignment"""

    print(f"Processing: {input_path}")
    print(f"Output: {output_path}")

    # Open input shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    input_ds = driver.Open(input_path, 0)  # Read-only

    if not input_ds:
        raise Exception(f"Could not open input shapefile: {input_path}")

    input_layer = input_ds.GetLayer()

    # Create output shapefile
    if os.path.exists(output_path):
        driver.DeleteDataSource(output_path)

    output_ds = driver.CreateDataSource(output_path)

    # Get spatial reference
    srs = input_layer.GetSpatialRef()

    # Create output layer
    output_layer = output_ds.CreateLayer('fixed_arrondissements', srs, ogr.wkbPolygon)

    # Copy field definitions
    input_defn = input_layer.GetLayerDefn()
    for i in range(input_defn.GetFieldCount()):
        field_defn = input_defn.GetFieldDefn(i)
        output_layer.CreateField(field_defn)

    # Process features and fix Ganviè issues
    ganvie_fixes = 0
    parent_fixes = 0

    print("\\nProcessing features...")

    for input_feature in input_layer:
        # Create new feature
        output_feature = ogr.Feature(output_layer.GetLayerDefn())

        # Copy geometry
        geom = input_feature.GetGeometryRef()
        output_feature.SetGeometry(geom)

        # Copy and fix fields
        for j in range(input_defn.GetFieldCount()):
            field_name = input_defn.GetFieldDefn(j).GetName()
            value = input_feature.GetField(j)

            # Fix shapeName field for Ganviè encoding
            if field_name == 'shapeName' and value:
                original_value = value

                # Fix Ganviè encoding issues
                if 'Ganviè' in value:
                    value = value.replace('Ganviè', 'Ganvié')
                    ganvie_fixes += 1
                    print(f"  Fixed name: '{original_value}' → '{value}'")

            # Fix parent assignment for Ganvié I
            if field_name == 'parentName':
                shape_name = input_feature.GetField('shapeName')
                # Check both original and corrected versions
                if shape_name and ('Ganviè I' in shape_name or 'Ganvié I' in shape_name):
                    if not value:  # If no parent assigned
                        value = 'So-ava'
                        parent_fixes += 1
                        print(f"  Fixed parent: {shape_name} → {value}")

            output_feature.SetField(field_name, value)

        # Add feature to output layer
        output_layer.CreateFeature(output_feature)
        output_feature = None

    # Close datasets
    input_ds = None
    output_ds = None

    # Copy other shapefile components
    base_input = os.path.splitext(input_path)[0]
    base_output = os.path.splitext(output_path)[0]

    for ext in ['.prj', '.cpg']:
        src_file = f"{base_input}{ext}"
        dst_file = f"{base_output}{ext}"
        if os.path.exists(src_file):
            shutil.copy2(src_file, dst_file)

    print(f"\\nCompleted fixes!")
    print(f"  Ganviè name fixes: {ganvie_fixes}")
    print(f"  Parent commune fixes: {parent_fixes}")
    print(f"  Output shapefile: {output_path}")

    return ganvie_fixes, parent_fixes


def main():
    input_shapefile = '/app/shapefiles/geoBoundaries-BEN-ADM3-with-parents.shp'
    output_shapefile = '/app/shapefiles/geoBoundaries-BEN-ADM3-final.shp'

    # Create backup
    backup_path = '/app/shapefiles/geoBoundaries-BEN-ADM3-with-parents-backup.shp'
    if not os.path.exists(backup_path):
        print("Creating backup...")
        for ext in ['.shp', '.shx', '.dbf', '.prj']:
            src = input_shapefile.replace('.shp', ext)
            dst = backup_path.replace('.shp', ext)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"  Backed up: {os.path.basename(src)}")

    # Fix Ganviè issues
    try:
        name_fixes, parent_fixes = fix_ganvie_issues(input_shapefile, output_shapefile)

        print(f"\\n✅ Successfully fixed Ganvié issues!")
        print(f"   Name encoding fixes: {name_fixes}")
        print(f"   Parent commune fixes: {parent_fixes}")

        # Verify the fixes
        print("\\nVerifying fixes...")
        driver = ogr.GetDriverByName('ESRI Shapefile')
        ds = driver.Open(output_shapefile, 0)
        layer = ds[0]

        print("Looking for Ganvié features:")
        ganvie_count = 0
        for feat in layer:
            name = feat.GetField('shapeName')
            parent = feat.GetField('parentName')
            if 'Ganvié' in name:
                ganvie_count += 1
                print(f"  ✓ {name} → {parent or 'NO PARENT'}")

        print(f"Found {ganvie_count} Ganvié features")

        # Count unmatched arrondissements now
        unmatched = 0
        for feat in layer:
            parent = feat.GetField('parentName')
            if not parent:
                unmatched += 1

        print(f"Remaining unmatched arrondissements: {unmatched}")

        ds = None

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())