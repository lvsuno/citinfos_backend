"""
Enable all active rubriques for all existing communities.
Run this after updating the signal to ensure all communities have all rubriques.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from communities.models import Community, RubriqueTemplate

def enable_all_rubriques_for_communities():
    print("=" * 80)
    print("ENABLING ALL RUBRIQUES FOR ALL COMMUNITIES")
    print("=" * 80)

    # Get all active rubriques
    all_rubriques = RubriqueTemplate.objects.filter(is_active=True)
    all_rubrique_ids = [str(r.id) for r in all_rubriques]

    print(f"\n📋 Total active rubriques: {len(all_rubrique_ids)}")
    for rubrique in all_rubriques:
        depth_indicator = "  " * rubrique.depth + ("└ " if rubrique.depth > 0 else "")
        print(f"   {depth_indicator}{rubrique.default_name} ({rubrique.template_type})")

    # Get all communities
    communities = Community.objects.filter(is_deleted=False)
    print(f"\n🏘️  Total communities to update: {communities.count()}")

    updated_count = 0
    already_complete = 0

    for community in communities:
        current_count = len(community.enabled_rubriques or [])

        if current_count == len(all_rubrique_ids):
            already_complete += 1
            print(f"   ✓ {community.name}: Already has all {current_count} rubriques")
        else:
            # Update to have all rubriques
            community.enabled_rubriques = all_rubrique_ids
            community.save(update_fields=['enabled_rubriques'])
            updated_count += 1
            print(f"   ✅ {community.name}: Updated from {current_count} to {len(all_rubrique_ids)} rubriques")

    print("\n" + "=" * 80)
    print("✅ UPDATE COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   • Communities already complete: {already_complete}")
    print(f"   • Communities updated: {updated_count}")
    print(f"   • Total rubriques per community: {len(all_rubrique_ids)}")
    print()

if __name__ == '__main__':
    enable_all_rubriques_for_communities()
