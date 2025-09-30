#!/usr/bin/env python3
"""
Create a new shapefile with admin codes for Benin ADM3 data
"""
import os
from osgeo import ogr

def create_coded_shapefile():
    """Create a new shapefile with unique admin codes"""

    # File paths
    input_file = "/app/shapefiles/geoBoundaries-BEN-ADM3-final.shp"
    output_file = "/app/shapefiles/geoBoundaries-BEN-ADM3-with-codes.shp"

    # Remove existing output files
    for ext in ['.shp', '.dbf', '.shx', '.prj', '.cpg']:
        output_path = output_file.replace('.shp', ext)
        if os.path.exists(output_path):
            os.remove(output_path)

    print(f"📖 Reading: {input_file}")
    print(f"📁 Creating: {output_file}")

    # Open input
    driver = ogr.GetDriverByName('ESRI Shapefile')
    input_ds = driver.Open(input_file, 0)
    if not input_ds:
        print("❌ Failed to open input")
        return False

    input_layer = input_ds.GetLayer()
    input_defn = input_layer.GetLayerDefn()

    # Create output datasource
    output_ds = driver.CreateDataSource(output_file)
    if not output_ds:
        print("❌ Failed to create output")
        return False

    # Create output layer
    srs = input_layer.GetSpatialRef()
    output_layer = output_ds.CreateLayer("adm3", srs, ogr.wkbPolygon)

    # Copy existing fields first
    field_names = []
    for i in range(input_defn.GetFieldCount()):
        field_defn = input_defn.GetFieldDefn(i)
        output_layer.CreateField(field_defn)
        field_names.append(field_defn.GetName())

    # Add admin_code field as the last field
    admin_code_field = ogr.FieldDefn("admin_code", ogr.OFTString)
    admin_code_field.SetWidth(20)
    if output_layer.CreateField(admin_code_field) != 0:
        print("❌ Failed to add admin_code field")
        return False

    field_names.append("admin_code")
    print(f"✅ Created fields: {field_names}")

    # Get output layer definition
    output_defn = output_layer.GetLayerDefn()

    # Process features
    count = 0
    input_layer.ResetReading()

    for input_feature in input_layer:
        count += 1

        # Create new feature
        output_feature = ogr.Feature(output_defn)

        # Copy existing fields
        for i in range(input_defn.GetFieldCount()):
            field_name = input_defn.GetFieldDefn(i).GetName()
            value = input_feature.GetField(field_name)
            output_feature.SetField(field_name, value)

        # Add unique admin code
        admin_code = f"BEN-ADM3-{count:03d}"
        output_feature.SetField("admin_code", admin_code)

        # Copy geometry
        geometry = input_feature.GetGeometryRef()
        output_feature.SetGeometry(geometry)

        # Add to layer
        output_layer.CreateFeature(output_feature)

        if count <= 3:
            shape_name = input_feature.GetField('shapeName')
            print(f"  ✅ {shape_name} → {admin_code}")
        elif count == 4:
            print("  ...")

    # Clean up
    input_ds = None
    output_ds = None

    print(f"✅ Created {count} features with admin codes")
    return True

if __name__ == "__main__":
    if create_coded_shapefile():
        print("\n🎉 Success! Now you can import with:")
        print("docker compose exec backend python manage.py import_shapefile \\")
        print("  /app/shapefiles/geoBoundaries-BEN-ADM3-with-codes.shp \\")
        print("  --country BEN --admin-level 3 --geometry-type area \\")
        print("  --data-source 'GeoBoundaries ADM3 With Codes' \\")
        print("  --parent-field parentName")
    else:
        print("\n❌ Failed to create coded shapefile")