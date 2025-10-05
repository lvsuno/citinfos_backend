#!/bin/bash

# Complete Quebec data cleanup and re-import with proper province hierarchy

set -e

echo "🍁 QUEBEC DATA RE-IMPORT WITH PROVINCE LEVEL"
echo "============================================="
echo ""

echo "Step 1: Delete all existing Canada divisions..."
docker compose exec backend python manage.py shell -c "
from core.models import Country, AdministrativeDivision

canada = Country.objects.get(name__icontains='canada')
deleted = AdministrativeDivision.objects.filter(country=canada).delete()
print(f'Deleted {deleted[0]} Canadian divisions')
"

echo ""
echo "Step 2: Create Québec province at level 1..."
docker compose exec backend python fix_quebec_data_structure.py

echo ""
echo "Step 3: Re-import Quebec geographic data using setup.sh..."
./setup.sh --start-from geodata

echo ""
echo "Step 4: Update regions to have Québec province as parent..."
docker compose exec backend python manage.py shell -c "
from core.models import Country, AdministrativeDivision

canada = Country.objects.get(name__icontains='canada')
quebec_province = AdministrativeDivision.objects.get(
    country=canada,
    admin_level=1,
    admin_code='QC'
)

# Update all level 2 regions
regions = AdministrativeDivision.objects.filter(country=canada, admin_level=2)
updated = 0
for region in regions:
    region.parent = quebec_province
    region.save()
    updated += 1

print(f'Updated {updated} regions to have Québec as parent')
"

echo ""
echo "Step 5: Verify the hierarchy..."
docker compose exec backend python manage.py shell -c "
from core.models import Country, AdministrativeDivision

canada = Country.objects.get(name__icontains='canada')

print('\\nCanada administrative divisions:')
for level in [1, 2, 3, 4, 5]:
    count = AdministrativeDivision.objects.filter(country=canada, admin_level=level).count()
    print(f'  Level {level}: {count}')

# Test with Sherbrooke
sherbrooke = AdministrativeDivision.objects.filter(
    country=canada,
    admin_level=4,
    name__icontains='sherbrooke'
).first()

if sherbrooke:
    print(f'\\nSherbrooke hierarchy:')
    current = sherbrooke
    while current:
        print(f'  Level {current.admin_level}: {current.name} ({current.boundary_type})')
        current = current.parent
    print(f'  Level 0: {canada.name}')

    # Test get_ancestor_at_level
    level_1 = sherbrooke.get_ancestor_at_level(1)
    if level_1:
        print(f'\\n✅ get_ancestor_at_level(1) = {level_1.name}')
    else:
        print(f'\\n❌ get_ancestor_at_level(1) returned None')
"

echo ""
echo "✅ Quebec re-import completed!"
