#!/usr/bin/env python3
"""
Add parent commune information to ADM3 arrondissements using spatial containment analysis.
This script will determine which commune each arrondissement polygon falls within and
update the original shapefile with this parent relationship information.
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

from core.models import AdministrativeDivision, Country


def find_parent_commune_by_containment(arrond_geom, commune_divisions):
    """Find parent commune using spatial containment"""
    max_overlap = 0
    parent_commune = None

    for commune in commune_divisions:
        if commune.area_geometry:
            # Convert Django geometry to OGR for spatial operations
            commune_wkt = commune.area_geometry.wkt
            commune_geom = ogr.CreateGeometryFromWkt(commune_wkt)

            # Check if arrondissement is contained within commune
            if arrond_geom.Within(commune_geom):
                return commune

            # If not fully contained, find commune with maximum overlap
            intersection = arrond_geom.Intersection(commune_geom)
            if intersection and intersection.GetArea() > max_overlap:
                max_overlap = intersection.GetArea()
                parent_commune = commune

    return parent_commune


def add_parent_info_to_shapefile(input_path, output_path):
    """Add parent commune information to ADM3 shapefile using spatial analysis"""

    print(f"Processing: {input_path}")
    print(f"Output: {output_path}")

    # Get existing communes from database
    benin = Country.objects.filter(name='Benin').first()
    if not benin:
        raise Exception("Benin country not found in database")

    communes = AdministrativeDivision.objects.filter(
        country=benin,
        admin_level=2,
        area_geometry__isnull=False
    )
    print(f"Found {communes.count()} communes with area geometry")

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

    # Create output layer with new fields
    output_layer = output_ds.CreateLayer('arrondissements_with_parents', srs, ogr.wkbPolygon)

    # Copy original field definitions
    input_defn = input_layer.GetLayerDefn()
    for i in range(input_defn.GetFieldCount()):
        field_defn = input_defn.GetFieldDefn(i)
        output_layer.CreateField(field_defn)

    # Add new parent fields
    parent_name_field = ogr.FieldDefn('parentName', ogr.OFTString)
    parent_name_field.SetWidth(100)
    output_layer.CreateField(parent_name_field)

    parent_id_field = ogr.FieldDefn('parentID', ogr.OFTString)
    parent_id_field.SetWidth(50)
    output_layer.CreateField(parent_id_field)

    parent_level_field = ogr.FieldDefn('parentLevel', ogr.OFTInteger)
    output_layer.CreateField(parent_level_field)

    # Process features and find parents
    matched_count = 0
    unmatched_count = 0

    print("\\nAnalyzing spatial containment...")

    for i, input_feature in enumerate(input_layer):
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{input_layer.GetFeatureCount()} features...")

        # Create new feature
        output_feature = ogr.Feature(output_layer.GetLayerDefn())

        # Copy geometry
        geom = input_feature.GetGeometryRef()
        output_feature.SetGeometry(geom)

        # Copy original fields
        for j in range(input_defn.GetFieldCount()):
            field_name = input_defn.GetFieldDefn(j).GetName()
            value = input_feature.GetField(j)
            output_feature.SetField(field_name, value)

        # Find parent commune using spatial containment
        arrond_name = input_feature.GetField('shapeName')
        parent_commune = find_parent_commune_by_containment(geom, communes)

        if parent_commune:
            output_feature.SetField('parentName', parent_commune.name)
            output_feature.SetField('parentID', str(parent_commune.id))
            output_feature.SetField('parentLevel', parent_commune.admin_level)
            matched_count += 1

            if matched_count <= 10:  # Show first 10 matches
                print(f"    ✓ {arrond_name} → {parent_commune.name}")
        else:
            output_feature.SetField('parentName', None)
            output_feature.SetField('parentID', None)
            output_feature.SetField('parentLevel', None)
            unmatched_count += 1

            if unmatched_count <= 5:  # Show first 5 unmatched
                print(f"    ❌ {arrond_name} → No parent found")

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

    print(f"\\nCompleted spatial analysis!")
    print(f"  Matched with parent: {matched_count}")
    print(f"  No parent found: {unmatched_count}")
    print(f"  Success rate: {matched_count / (matched_count + unmatched_count) * 100:.1f}%")
    print(f"  Output shapefile: {output_path}")

    return matched_count, unmatched_count


def main():
    input_shapefile = '/app/shapefiles/geoBoundaries-BEN-ADM3-fixed.shp'
    output_shapefile = '/app/shapefiles/geoBoundaries-BEN-ADM3-with-parents.shp'

    # Create backup
    backup_path = '/app/shapefiles/geoBoundaries-BEN-ADM3-fixed-backup.shp'
    if not os.path.exists(backup_path):
        print("Creating backup...")
        for ext in ['.shp', '.shx', '.dbf', '.prj']:
            src = input_shapefile.replace('.shp', ext)
            dst = backup_path.replace('.shp', ext)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"  Backed up: {os.path.basename(src)}")

    # Add parent information using spatial analysis
    try:
        matched, unmatched = add_parent_info_to_shapefile(input_shapefile, output_shapefile)

        print(f"\\n✅ Successfully added parent information!")
        print(f"   {matched} arrondissements matched with communes")
        print(f"   {unmatched} arrondissements without parent")

        # Verify the output
        print("\\nVerifying output...")
        driver = ogr.GetDriverByName('ESRI Shapefile')
        ds = driver.Open(output_shapefile, 0)
        layer = ds.GetLayer()

        # Show sample results
        print("\\nSample results:")
        for i, feat in enumerate(layer):
            if i >= 5:
                break
            arrond_name = feat.GetField('shapeName')
            parent_name = feat.GetField('parentName')
            print(f"  {arrond_name} → {parent_name or 'No parent'}")

        ds = None

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())