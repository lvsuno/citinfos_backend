#!/usr/bin/env python3
"""
Fix Quebec data structure to have proper province level.

Current: Regions at level 2 with no parent
Target: Province at level 1 → Regions at level 2 → MRC at level 3 → Municipalities at level 4
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from core.models import Country, AdministrativeDivision
from django.contrib.gis.geos import Point

def fix_quebec_structure():
    """Fix Quebec hierarchy by adding province level."""

    # Get Canada
    canada = Country.objects.filter(name__icontains='canada').first()
    if not canada:
        print("❌ Canada not found!")
        return False

    print(f"✓ Found Canada: {canada.name}")
    print(f"  Default admin level: {canada.default_admin_level}")
    print()

    # Step 1: Create Quebec province at level 1
    quebec_province, created = AdministrativeDivision.objects.get_or_create(
        country=canada,
        admin_level=1,
        admin_code='QC',
        defaults={
            'name': 'Québec',
            'local_name': 'Québec',
            'boundary_type': 'province',
            'local_code': '24',
            'description': 'Province du Québec',
            'parent': None,
            'centroid': Point(-71.2082, 46.8139, srid=4326),
            'data_source': 'Manual entry',
        }
    )

    if created:
        print(f"✅ Created Quebec province: {quebec_province.name}")
    else:
        print(f"✓ Quebec province already exists: {quebec_province.name}")
        # Update it to ensure correct data
        quebec_province.name = 'Québec'
        quebec_province.boundary_type = 'province'
        quebec_province.parent = None
        quebec_province.save()
        print(f"  Updated province data")

    print()

    # Step 2: Update all level 2 regions to have Quebec as parent
    regions = AdministrativeDivision.objects.filter(
        country=canada,
        admin_level=2
    )

    print(f"📊 Found {regions.count()} regions at level 2")

    updated = 0
    for region in regions:
        if region.parent != quebec_province:
            region.parent = quebec_province
            region.save()
            print(f"  ✓ Updated {region.name}: parent → Québec")
            updated += 1
        else:
            print(f"  - {region.name}: already has correct parent")

    print(f"\n✅ Updated {updated} regions")
    print()

    # Step 3: Verify the hierarchy
    print("🔍 Verifying hierarchy:")
    print(f"  Level 1 (provinces): {AdministrativeDivision.objects.filter(country=canada, admin_level=1).count()}")
    print(f"  Level 2 (régions): {AdministrativeDivision.objects.filter(country=canada, admin_level=2).count()}")
    print(f"  Level 3 (MRC): {AdministrativeDivision.objects.filter(country=canada, admin_level=3).count()}")
    print(f"  Level 4 (municipalities): {AdministrativeDivision.objects.filter(country=canada, admin_level=4).count()}")
    print(f"  Level 5 (arrondissements): {AdministrativeDivision.objects.filter(country=canada, admin_level=5).count()}")
    print()

    # Step 4: Test with a sample municipality
    sample = AdministrativeDivision.objects.filter(
        country=canada,
        admin_level=4,
        name__icontains='sherbrooke'
    ).first()

    if sample:
        print(f"📋 Sample hierarchy for {sample.name}:")
        current = sample
        while current:
            print(f"  Level {current.admin_level}: {current.name} ({current.boundary_type})")
            current = current.parent
        print(f"  Level 0: {canada.name}")
        print()

        # Test ancestor method
        level_1 = sample.get_ancestor_at_level(1)
        if level_1:
            print(f"✅ get_ancestor_at_level(1) correctly returns: {level_1.name}")
        else:
            print(f"❌ get_ancestor_at_level(1) returned None!")
            return False

    print()
    print("✅ Quebec data structure fix completed successfully!")
    return True

if __name__ == '__main__':
    fix_quebec_structure()
