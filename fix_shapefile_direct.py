#!/usr/bin/env python3
"""
Simple script to fix the duplicate admin code issue in the Benin communes shapefile.
This corrects Adjarra commune's admin codes from BJ01/BJ0101 to BJ10/BJ1001.
"""

import os
import shutil
from osgeo import ogr, osr

def fix_benin_communes_shapefile():
    """Fix the admin code duplicate issue in the Benin communes shapefile."""

    # File paths
    input_shp = '/app/shapefiles/ben_adm_1m_salb_2019_shapes/ben_admbnda_adm2_1m_salb_20190816.shp'
    output_shp = '/app/shapefiles/ben_adm_1m_salb_2019_shapes/ben_admbnda_adm2_1m_salb_20190816_fixed.shp'
    backup_shp = '/app/shapefiles/ben_adm_1m_salb_2019_shapes/ben_admbnda_adm2_1m_salb_20190816_original.shp'

    print(f"Input shapefile: {input_shp}")
    print(f"Output shapefile: {output_shp}")

    # Create backup first
    print("Creating backup...")
    backup_shapefile(input_shp, backup_shp)

    # Open input shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    input_ds = driver.Open(input_shp, 0)  # 0 = read-only
    if not input_ds:
        raise Exception(f"Could not open {input_shp}")

    input_layer = input_ds.GetLayer()

    # Create output shapefile
    if os.path.exists(output_shp):
        driver.DeleteDataSource(output_shp)

    output_ds = driver.CreateDataSource(output_shp)
    output_layer = output_ds.CreateLayer(
        'communes_fixed',
        input_layer.GetSpatialRef(),
        input_layer.GetGeomType()
    )

    # Copy field definitions
    input_layer_defn = input_layer.GetLayerDefn()
    for i in range(input_layer_defn.GetFieldCount()):
        field_defn = input_layer_defn.GetFieldDefn(i)
        output_layer.CreateField(field_defn)

    output_layer_defn = output_layer.GetLayerDefn()

    # Copy features with fixes
    fixes_applied = 0
    total_features = input_layer.GetFeatureCount()
    print(f"Processing {total_features} features...")

    for feature in input_layer:
        # Get feature data
        adm2_name = feature.GetField('adm2_name')
        adm1_name = feature.GetField('adm1_name')
        admin1Pcod = feature.GetField('admin1Pcod')
        admin2Pcod = feature.GetField('admin2Pcod')

        # Create output feature
        output_feature = ogr.Feature(output_layer_defn)

        # Copy geometry
        geom = feature.GetGeometryRef()
        output_feature.SetGeometry(geom)

        # Copy all fields
        for i in range(input_layer_defn.GetFieldCount()):
            field_name = input_layer_defn.GetFieldDefn(i).GetName()
            value = feature.GetField(field_name)

            # Apply fix for Adjarra in Oueme with wrong admin codes
            if (adm2_name == 'Adjarra' and adm1_name == 'Oueme' and
                admin1Pcod == 'BJ01' and admin2Pcod == 'BJ0101'):

                if field_name == 'admin1Pcod':
                    value = 'BJ10'  # Correct Oueme department code
                elif field_name == 'admin2Pcod':
                    value = 'BJ1001'  # Correct Adjarra commune code

                if field_name in ['admin1Pcod', 'admin2Pcod']:
                    print(f"Fixed {adm2_name}: {field_name} {feature.GetField(field_name)} -> {value}")
                    fixes_applied += 1

            output_feature.SetField(field_name, value)

        # Add feature to output
        output_layer.CreateFeature(output_feature)
        output_feature = None

    # Clean up
    input_ds = None
    output_ds = None

    print(f"Created fixed shapefile: {output_shp}")
    print(f"Fixes applied: {fixes_applied}")

    # Verify the fix worked
    verify_fix(output_shp)

    return output_shp

def backup_shapefile(source_shp, backup_shp):
    """Backup all shapefile components."""
    base_source = source_shp.replace('.shp', '')
    base_backup = backup_shp.replace('.shp', '')

    extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.sbn', '.sbx']

    for ext in extensions:
        source_file = f'{base_source}{ext}'
        backup_file = f'{base_backup}{ext}'

        if os.path.exists(source_file):
            shutil.copy2(source_file, backup_file)
            print(f"Backed up: {os.path.basename(source_file)}")

def verify_fix(shapefile_path):
    """Verify that the fix was applied correctly."""
    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = driver.Open(shapefile_path, 0)
    layer = ds.GetLayer()

    print("\\nVerifying fix...")

    # Check for duplicate admin codes
    admin_codes = {}
    oueme_communes = []

    for feature in layer:
        admin2Pcod = feature.GetField('admin2Pcod')
        adm2_name = feature.GetField('adm2_name')
        adm1_name = feature.GetField('adm1_name')
        admin1Pcod = feature.GetField('admin1Pcod')

        # Track admin codes
        if admin2Pcod in admin_codes:
            print(f"WARNING: Duplicate admin code {admin2Pcod} found!")
        else:
            admin_codes[admin2Pcod] = adm2_name

        # Track Oueme communes
        if adm1_name == 'Oueme':
            oueme_communes.append({
                'name': adm2_name,
                'admin1Pcod': admin1Pcod,
                'admin2Pcod': admin2Pcod
            })

    print(f"Total unique admin codes: {len(admin_codes)}")
    print(f"Total features: {layer.GetFeatureCount()}")

    print(f"\\nOueme communes ({len(oueme_communes)}):")
    for commune in oueme_communes:
        print(f"  {commune['name']}: {commune['admin1Pcod']}/{commune['admin2Pcod']}")

    # Check specifically for Adjarra
    adjarra_communes = [c for c in oueme_communes if c['name'] == 'Adjarra']
    if adjarra_communes:
        adjarra = adjarra_communes[0]
        if adjarra['admin1Pcod'] == 'BJ10' and adjarra['admin2Pcod'] == 'BJ1001':
            print("✅ Adjarra admin codes correctly fixed!")
        else:
            print(f"❌ Adjarra still has wrong codes: {adjarra['admin1Pcod']}/{adjarra['admin2Pcod']}")
    else:
        print("❌ Adjarra commune not found!")

    ds = None

if __name__ == '__main__':
    try:
        fixed_shapefile = fix_benin_communes_shapefile()
        print(f"\\n🎉 Successfully created fixed shapefile: {fixed_shapefile}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()