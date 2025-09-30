#!/usr/bin/env python3
"""
Fix incorrect commune names in Benin shapefiles.

This script corrects the following commune names in all Benin shapefiles:
- Adjara → Adjarra
- Zangnanado → Zagnanado
- Boukoumbe → Boukoumbé
- Seme-kpodji → Sèmè-Podji
- Kobli → Cobly
- Kopargo → Copargo
"""

import os
import sys
from osgeo import ogr, osr
import shutil


def fix_commune_names_in_shapefile(input_path, output_path=None, dry_run=False):
    """Fix commune names in a shapefile"""

    # Name corrections mapping
    name_corrections = {
        'Adjara': 'Adjarra',
        'Zangnanado': 'Zagnanado',
        'Boukoumbe': 'Boukoumbé',
        'Seme-kpodji': 'Sèmè-Podji',
        'Kobli': 'Cobly',
        'Kopargo': 'Copargo'
    }

    # If no output path specified, create a backup and overwrite original
    if output_path is None:
        backup_path = input_path.replace('.shp', '_backup_names.shp')
        output_path = input_path
        create_backup = True
    else:
        create_backup = False

    print(f"Processing: {input_path}")

    # Open input shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    input_ds = driver.Open(input_path, 0)  # Read-only

    if not input_ds:
        print(f"Error: Could not open {input_path}")
        return False

    input_layer = input_ds.GetLayer()
    layer_defn = input_layer.GetLayerDefn()

    # Check if shapefile has name fields that might need correction
    name_fields = []
    for i in range(layer_defn.GetFieldCount()):
        field_name = layer_defn.GetFieldDefn(i).GetName()
        # Look for fields that typically contain commune names
        if any(name_part in field_name.lower() for name_part in ['name', 'nom', 'adm2']):
            name_fields.append(field_name)

    if not name_fields:
        print(f"  No name fields found in {input_path}")
        input_ds = None
        return False

    print(f"  Name fields found: {', '.join(name_fields)}")

    # Check if any corrections are needed
    corrections_needed = []
    input_layer.ResetReading()

    for feature in input_layer:
        for field in name_fields:
            value = feature.GetField(field)
            if value and value in name_corrections:
                corrections_needed.append((field, value, name_corrections[value]))

    if not corrections_needed:
        print(f"  No corrections needed in {input_path}")
        input_ds = None
        return False

    print(f"  Found {len(corrections_needed)} corrections needed")
    for field, old_name, new_name in set(corrections_needed):
        print(f"    {field}: {old_name} → {new_name}")

    if dry_run:
        print(f"  [DRY RUN] Would fix {len(corrections_needed)} name issues")
        input_ds = None
        return True

    # Create backup if overwriting original
    if create_backup:
        print(f"  Creating backup: {backup_path}")
        copy_shapefile(input_path, backup_path)

    # Create output shapefile
    if os.path.exists(output_path) and output_path != input_path:
        driver.DeleteDataSource(output_path)

    output_ds = driver.CreateDataSource(output_path)

    # Copy spatial reference
    srs = input_layer.GetSpatialRef()

    # Create output layer
    geom_type = input_layer.GetGeomType()
    output_layer = output_ds.CreateLayer(
        os.path.splitext(os.path.basename(output_path))[0],
        srs,
        geom_type
    )

    # Copy field definitions
    for i in range(layer_defn.GetFieldCount()):
        field_defn = layer_defn.GetFieldDefn(i)
        output_layer.CreateField(field_defn)

    # Copy and fix features
    corrections_made = 0
    input_layer.ResetReading()

    for feature in input_layer:
        # Create new feature
        new_feature = ogr.Feature(output_layer.GetLayerDefn())

        # Copy geometry
        geom = feature.GetGeometryRef()
        if geom:
            new_feature.SetGeometry(geom)

        # Copy and fix field values
        for i in range(layer_defn.GetFieldCount()):
            field_name = layer_defn.GetFieldDefn(i).GetName()
            value = feature.GetField(field_name)

            # Apply name correction if needed
            if value and value in name_corrections:
                corrected_value = name_corrections[value]
                new_feature.SetField(field_name, corrected_value)
                corrections_made += 1
                print(f"    Fixed: {value} → {corrected_value}")
            else:
                new_feature.SetField(field_name, value)

        # Add feature to output layer
        output_layer.CreateFeature(new_feature)
        new_feature = None

    # Clean up
    input_ds = None
    output_ds = None

    print(f"  ✅ Fixed {corrections_made} commune names")
    return True


def copy_shapefile(source_path, dest_path):
    """Copy all shapefile components (.shp, .shx, .dbf, .prj, etc.)"""
    base_source = os.path.splitext(source_path)[0]
    base_dest = os.path.splitext(dest_path)[0]

    # Common shapefile extensions
    extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.qmd']

    for ext in extensions:
        src_file = base_source + ext
        dest_file = base_dest + ext

        if os.path.exists(src_file):
            shutil.copy2(src_file, dest_file)


def find_benin_shapefiles(directory):
    """Find all Benin-related shapefiles in a directory"""
    shapefiles = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.shp') and 'benin' in file.lower():
                shapefiles.append(os.path.join(root, file))

    return shapefiles


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python fix_commune_names.py <shapefile_or_directory> [--dry-run]")
        print("\nExamples:")
        print("  python fix_commune_names.py /path/to/shapefile.shp")
        print("  python fix_commune_names.py /path/to/shapefiles/ --dry-run")
        sys.exit(1)

    path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("=" * 50)

    if os.path.isfile(path) and path.endswith('.shp'):
        # Single shapefile
        success = fix_commune_names_in_shapefile(path, dry_run=dry_run)
        if success:
            print("\n✅ Shapefile processing completed")
        else:
            print("\n❌ No changes were needed")

    elif os.path.isdir(path):
        # Directory - find all Benin shapefiles
        shapefiles = find_benin_shapefiles(path)

        if not shapefiles:
            print(f"No Benin shapefiles found in {path}")
            sys.exit(1)

        print(f"Found {len(shapefiles)} Benin shapefile(s):")
        for shp in shapefiles:
            print(f"  - {shp}")
        print()

        successful = 0
        for shapefile in shapefiles:
            if fix_commune_names_in_shapefile(shapefile, dry_run=dry_run):
                successful += 1
            print()

        print(f"✅ Successfully processed {successful}/{len(shapefiles)} shapefiles")

    else:
        print(f"Error: {path} is not a valid shapefile or directory")
        sys.exit(1)


if __name__ == '__main__':
    main()