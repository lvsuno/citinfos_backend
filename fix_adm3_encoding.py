#!/usr/bin/env python3
"""
Fix encoding issues in the geoBoundaries-BEN-ADM3.shp shapefile.
Converts '?' characters back to proper accented characters for Benin arrondissement names.
"""

import os
import shutil
from osgeo import ogr, osr
import django
import sys

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()


def fix_encoding_issues(input_path, output_path):
    """Fix encoding issues in shapefile names"""

    # Common replacements for Benin names with encoding issues
    encoding_fixes = {
        # Common patterns for accented characters
        'D?': 'Dé', 'S?': 'Sé', 'H?': 'Hé', 'Agu?': 'Agué',
        'Dj?vi?': 'Djéviè', 'Dj?': 'Djé', 'S?dj?': 'Sédjé',
        'kanm?': 'kanmè', 'gbo': 'gbo', 'H?kanm?': 'Hékanmè',
        'Agbam?': 'Agbamè', 'Hou?gbo': 'Houègbo', 'Dam?': 'Damè',
        'S?hou?': 'Séhouè', 'D?kanm?': 'Dékanmè', 'Agu?kon': 'Aguékon',
        'Koudokpo?': 'Koudokpoè', 'Djanglanm?': 'Djanglanmè',
        'Colli-Agbam?': 'Colli-Agbamè', 'Hou?do-Agu?kon': 'Houèdo-Aguékon',
        'Tangbo-Dj?vi?': 'Tangbo-Djéviè', 'S?dj?-D?nou': 'Sédjé-Dénou',

        # Other common patterns
        '?': 'è',  # Default replacement for remaining question marks
    }

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
    output_layer = output_ds.CreateLayer('corrected', srs, ogr.wkbPolygon)

    # Copy field definitions
    input_defn = input_layer.GetLayerDefn()
    for i in range(input_defn.GetFieldCount()):
        field_defn = input_defn.GetFieldDefn(i)
        output_layer.CreateField(field_defn)

    # Copy features with corrected names
    corrections_made = 0

    for input_feature in input_layer:
        # Create new feature
        output_feature = ogr.Feature(output_layer.GetLayerDefn())

        # Copy geometry
        geom = input_feature.GetGeometryRef()
        output_feature.SetGeometry(geom)

        # Copy and fix fields
        for i in range(input_defn.GetFieldCount()):
            field_name = input_defn.GetFieldDefn(i).GetName()
            value = input_feature.GetField(i)

            # Fix encoding for shapeName field
            if field_name == 'shapeName' and value and '?' in value:
                original_value = value

                # Apply encoding fixes
                for pattern, replacement in encoding_fixes.items():
                    if pattern in value:
                        value = value.replace(pattern, replacement)

                if value != original_value:
                    corrections_made += 1
                    print(f"  Fixed: '{original_value}' → '{value}'")

            output_feature.SetField(field_name, value)

        # Add feature to output layer
        output_layer.CreateFeature(output_feature)
        output_feature = None

    # Close datasets
    input_ds = None
    output_ds = None

    # Copy other shapefile components (.prj, .dbf, etc.)
    base_input = os.path.splitext(input_path)[0]
    base_output = os.path.splitext(output_path)[0]

    for ext in ['.prj', '.cpg']:
        src_file = f"{base_input}{ext}"
        dst_file = f"{base_output}{ext}"
        if os.path.exists(src_file):
            shutil.copy2(src_file, dst_file)
            print(f"  Copied: {os.path.basename(src_file)}")

    print(f"\nCompleted!")
    print(f"  Corrections made: {corrections_made}")
    print(f"  Output shapefile: {output_path}")

    return corrections_made


def main():
    input_shapefile = '/app/shapefiles/geoBoundaries-BEN-ADM3.shp'
    output_shapefile = '/app/shapefiles/geoBoundaries-BEN-ADM3-fixed.shp'

    # Create backup
    backup_path = '/app/shapefiles/geoBoundaries-BEN-ADM3-backup.shp'
    if not os.path.exists(backup_path):
        print("Creating backup...")
        for ext in ['.shp', '.shx', '.dbf', '.prj']:
            src = input_shapefile.replace('.shp', ext)
            dst = backup_path.replace('.shp', ext)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"  Backed up: {os.path.basename(src)}")

    # Fix encoding
    try:
        corrections = fix_encoding_issues(input_shapefile, output_shapefile)
        print(f"\n✅ Successfully fixed {corrections} encoding issues!")

        # Show some corrected names
        print("\nVerifying corrections...")
        driver = ogr.GetDriverByName('ESRI Shapefile')
        ds = driver.Open(output_shapefile, 0)
        layer = ds.GetLayer()

        corrected_names = []
        for i, feat in enumerate(layer):
            name = feat.GetField('shapeName')
            if '?' not in name and any(char in name for char in 'éèêçàâùûôî'):
                corrected_names.append(name)
            if len(corrected_names) >= 10:
                break

        print("Sample corrected names:")
        for name in corrected_names:
            print(f"  ✓ {name}")

        ds = None

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())