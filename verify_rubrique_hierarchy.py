#!/usr/bin/env python
"""Verify the hierarchical rubrique structure."""

from communities.models import RubriqueTemplate, Community

print("=" * 60)
print("RUBRIQUE HIERARCHY VERIFICATION")
print("=" * 60)

# Count rubriques
total = RubriqueTemplate.objects.count()
main = RubriqueTemplate.objects.filter(depth=0).count()
subsections = RubriqueTemplate.objects.filter(depth=1).count()

print(f"\nTotal rubriques: {total}")
print(f"Main rubriques (depth=0): {main}")
print(f"Subsections (depth=1): {subsections}")

# Show hierarchy
print("\n" + "=" * 60)
print("HIERARCHY STRUCTURE:")
print("=" * 60)

for rubrique in RubriqueTemplate.objects.filter(parent__isnull=True).order_by('path'):
    req = "✓ REQUIRED" if rubrique.is_required else "  optional"
    print(f"\n{req} | {rubrique.template_type}")
    print(f"         Name: {rubrique.default_name}")
    print(f"         Path: {rubrique.path}, Depth: {rubrique.depth}")

    # Show children
    children = RubriqueTemplate.objects.filter(parent=rubrique).order_by('path')
    if children:
        print(f"         Subsections:")
        for child in children:
            print(f"           → {child.template_type} (path={child.path}, depth={child.depth})")

# Check Community model
print("\n" + "=" * 60)
print("COMMUNITY MODEL CHECK:")
print("=" * 60)

communities = Community.objects.all()
print(f"\nTotal communities: {communities.count()}")

if communities.exists():
    sample = communities.first()
    print(f"\nSample community: {sample.name}")
    print(f"Enabled rubriques (JSONField): {sample.enabled_rubriques}")
    print(f"Type: {type(sample.enabled_rubriques)}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE!")
print("=" * 60)
