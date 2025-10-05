"""
Fix Quebec hierarchy by adding Province level (Level 1)

Current structure:
- Level 2: Régions (no parent)
- Level 3: MRC
- Level 4: Municipalities

Target structure:
- Level 1: Québec (province)
- Level 2: Régions (parent = Québec)
- Level 3: MRC
- Level 4: Municipalities
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from core.models import Country, AdministrativeDivision
from django.contrib.gis.geos import Point

def fix_quebec_hierarchy():
    """Add Québec province at level 1 and reparent all régions."""

    # Get Canada
    canada = Country.objects.filter(name__icontains='canada').first()
    if not canada:
        print("❌ Canada not found!")
        return

    print(f"✓ Found Canada: {canada.name}")

    # Check if Québec province already exists at level 1
    quebec_province = AdministrativeDivision.objects.filter(
        country=canada,
        admin_level=1,
        name__icontains='québec'
    ).first()

    if quebec_province:
        print(f"✓ Québec province already exists: {quebec_province.name}")
    else:
        # Create Québec province at level 1
        quebec_province = AdministrativeDivision.objects.create(
            country=canada,
            admin_level=1,
            name='Québec',
            local_name='Québec',
            boundary_type='province',
            admin_code='QC',
            local_code='24',  # Quebec's province code
            description='Province du Québec',
            parent=None,  # No parent (top level after country)
            # Add a centroid for Quebec City area
            centroid=Point(-71.2082, 46.8139, srid=4326),
        )
        print(f"✅ Created Québec province: {quebec_province.name}")

    # Get all level 2 régions without a parent (or with wrong parent)
    regions = AdministrativeDivision.objects.filter(
        country=canada,
        admin_level=2,
        boundary_type='régions'
    )

    print(f"\n📊 Found {regions.count()} régions at level 2")

    # Update each région to have Québec as parent
    updated_count = 0
    for region in regions:
        if region.parent != quebec_province:
            old_parent = region.parent.name if region.parent else "None"
            region.parent = quebec_province
            region.save()
            print(f"  ✓ Updated {region.name}: parent {old_parent} → Québec")
            updated_count += 1
        else:
            print(f"  - {region.name}: already has Québec as parent")

    print(f"\n✅ Updated {updated_count} régions")

    # Update Canada's admin_levels metadata
    print("\n📝 Updating Canada's admin_levels metadata...")
    admin_levels = canada.get_admin_levels()
    print(f"Current admin_levels: {admin_levels}")

    # Verify the hierarchy
    print("\n🔍 Verifying hierarchy:")
    print(f"Level 1 (provinces): {AdministrativeDivision.objects.filter(country=canada, admin_level=1).count()}")
    print(f"Level 2 (régions): {AdministrativeDivision.objects.filter(country=canada, admin_level=2).count()}")
    print(f"Level 3 (MRC): {AdministrativeDivision.objects.filter(country=canada, admin_level=3).count()}")
    print(f"Level 4 (municipalities): {AdministrativeDivision.objects.filter(country=canada, admin_level=4).count()}")

    # Show sample hierarchy
    print("\n📋 Sample hierarchy:")
    sample_muni = AdministrativeDivision.objects.filter(
        country=canada,
        admin_level=4,
        name__icontains='sherbrooke'
    ).first()

    if sample_muni:
        print(f"\nSherbrooke hierarchy:")
        current = sample_muni
        while current:
            print(f"  Level {current.admin_level}: {current.name} ({current.boundary_type})")
            current = current.parent
        print(f"  Level 0: {canada.name}")

        # Test get_ancestor_at_level
        level_1 = sample_muni.get_ancestor_at_level(1)
        if level_1:
            print(f"\n✓ get_ancestor_at_level(1) returns: {level_1.name}")
        else:
            print("\n❌ get_ancestor_at_level(1) returned None")

    print("\n✅ Done!")

if __name__ == '__main__':
    fix_quebec_hierarchy()
