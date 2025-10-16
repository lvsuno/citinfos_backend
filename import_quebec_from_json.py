#!/usr/bin/env python3
"""
Import Quebec municipalities from municipalites_quebec.json file.
This script imports municipalities with their MRC and region relationships.
"""

import os
import sys
import django
import json
from pathlib import Path

# Setup Django
project_root = Path(__file__).parent
sys.path.append(str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from core.models import AdministrativeDivision, Country
from django.db import transaction

def create_or_get_region(canada, quebec, region_name):
    """Create or get a region (admin_level=2)"""
    region, created = AdministrativeDivision.objects.get_or_create(
        country=canada,
        admin_level=2,
        name=region_name,
        parent=quebec,
        defaults={
            'data_source': 'Quebec Municipalities JSON',
            'boundary_type': 'région'
        }
    )
    if created:
        print(f"   📍 Created region: {region_name}")
    return region

def create_or_get_mrc(canada, region, mrc_name):
    """Create or get an MRC (admin_level=3)"""
    mrc, created = AdministrativeDivision.objects.get_or_create(
        country=canada,
        admin_level=3,
        name=mrc_name,
        parent=region,
        defaults={
            'data_source': 'Quebec Municipalities JSON',
            'boundary_type': 'mrc'
        }
    )
    if created:
        print(f"     🏘️ Created MRC: {mrc_name}")
    return mrc

def import_quebec_from_json():
    """Import Quebec municipalities from JSON file"""
    
    print("🏛️ IMPORTING QUEBEC MUNICIPALITIES FROM JSON")
    print("=" * 48)
    
    # File path
    json_path = "/app/municipalites_quebec.json"
    
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return False
    
    try:
        # Get Canada
        canada, created = Country.objects.get_or_create(
            name='Canada',
            defaults={
                'code': 'CA',
                'data_source': 'Manual'
            }
        )
        if created:
            print(f"📍 Created country: {canada.name}")
        else:
            print(f"📍 Using existing country: {canada.name}")
        
        # Get or create Quebec province
        quebec, created = AdministrativeDivision.objects.get_or_create(
            country=canada,
            admin_level=1,
            name='Québec',
            defaults={
                'data_source': 'Manual',
                'boundary_type': 'province'
            }
        )
        if created:
            print(f"🍁 Created province: {quebec.name}")
        else:
            print(f"🍁 Using existing province: {quebec.name}")
        
        # Load JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        municipalities = data.get('villes', [])
        print(f"📊 Found {len(municipalities)} municipalities in JSON")
        
        # Import counters
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        # Keep track of created regions and MRCs
        created_regions = {}
        created_mrcs = {}
        
        with transaction.atomic():
            for muni_data in municipalities:
                try:
                    # Get municipality data
                    nom = muni_data.get('nom', '').strip()
                    code = muni_data.get('code', '').strip()
                    mrc_name = muni_data.get('mrc', '').strip()
                    region_name = muni_data.get('region', '').strip()
                    population = muni_data.get('population_estimee')
                    superficie = muni_data.get('superficie_km2')
                    
                    if not nom:
                        print(f"⚠️ Skipping municipality with no name")
                        skipped_count += 1
                        continue
                    
                    # Check if already exists
                    existing = AdministrativeDivision.objects.filter(
                        country=canada,
                        admin_level=4,
                        name=nom
                    ).first()
                    
                    if existing:
                        print(f"⏭️ Municipality '{nom}' already exists, skipping")
                        skipped_count += 1
                        continue
                    
                    # Create or get region
                    region = None
                    if region_name:
                        if region_name not in created_regions:
                            created_regions[region_name] = create_or_get_region(canada, quebec, region_name)
                        region = created_regions[region_name]
                    
                    # Create or get MRC
                    mrc = None
                    if mrc_name and region:
                        mrc_key = f"{region_name}::{mrc_name}"
                        if mrc_key not in created_mrcs:
                            created_mrcs[mrc_key] = create_or_get_mrc(canada, region, mrc_name)
                        mrc = created_mrcs[mrc_key]
                    
                    # Determine parent (MRC if exists, otherwise region, otherwise quebec)
                    parent = mrc or region or quebec
                    
                    # Create municipality
                    municipality = AdministrativeDivision.objects.create(
                        country=canada,
                        admin_level=4,
                        name=nom,
                        admin_code=code if code else None,
                        parent=parent,
                        data_source="Quebec Municipalities JSON",
                        boundary_type='municipalité'
                    )
                    
                    imported_count += 1
                    
                    # Progress indicator
                    if imported_count % 50 == 0:
                        print(f"✅ Imported {imported_count} municipalities...")
                
                except Exception as e:
                    error_count += 1
                    nom_safe = muni_data.get('nom', 'unknown') if isinstance(muni_data, dict) else 'unknown'
                    print(f"❌ Error processing municipality {nom_safe}: {str(e)}")
                    continue
        
        # Final summary
        print(f"\n🎉 QUEBEC MUNICIPALITIES IMPORT COMPLETE")
        print(f"   📍 Regions created: {len(created_regions)}")
        print(f"   🏘️ MRCs created: {len(created_mrcs)}")
        print(f"   ✅ Municipalities imported: {imported_count}")
        print(f"   ⏭️ Skipped: {skipped_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total processed: {imported_count + skipped_count + error_count}")
        
        # Show final counts
        total_regions = AdministrativeDivision.objects.filter(country=canada, admin_level=2).count()
        total_mrcs = AdministrativeDivision.objects.filter(country=canada, admin_level=3).count()
        total_munis = AdministrativeDivision.objects.filter(country=canada, admin_level=4).count()
        
        print(f"\n📊 FINAL DATABASE COUNTS:")
        print(f"   Provinces (Level 1): {AdministrativeDivision.objects.filter(country=canada, admin_level=1).count()}")
        print(f"   Regions (Level 2): {total_regions}")
        print(f"   MRCs (Level 3): {total_mrcs}")
        print(f"   Municipalities (Level 4): {total_munis}")
        
        return True
    
    except Exception as e:
        print(f"❌ Fatal error during import: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_quebec_from_json()
    sys.exit(0 if success else 1)