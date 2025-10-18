"""
Test script to verify the community rubriques API endpoint
Run this to test the /communities/{slug}/rubriques/ endpoint
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from communities.models import Community, RubriqueTemplate
from django.contrib.auth import get_user_model

User = get_user_model()

def test_rubriques_api():
    print("=" * 80)
    print("TESTING COMMUNITY RUBRIQUES API ENDPOINT")
    print("=" * 80)

    # Get a test community
    community = Community.objects.first()

    if not community:
        print("❌ No communities found in database")
        return

    print(f"\n✅ Testing with community: {community.name} (slug: {community.slug})")
    print(f"   Community ID: {community.id}")

    # Check enabled rubriques
    print(f"\n📋 Enabled Rubriques Count: {len(community.enabled_rubriques)}")
    print(f"   Enabled Rubrique UUIDs: {community.enabled_rubriques[:3]}...")

    # Get rubrique tree
    tree = community.get_rubrique_tree()
    print(f"\n🌲 Rubrique Tree Structure:")
    for rubrique in tree:
        print(f"   • {rubrique['name']} (depth={rubrique['depth']}, required={rubrique.get('required', False)})")
        if rubrique.get('children'):
            for child in rubrique['children']:
                print(f"      └ {child['name']} (depth={child['depth']})")

    # Test API endpoint simulation
    print(f"\n🔗 API Endpoint Test:")
    print(f"   GET /api/communities/{community.slug}/rubriques/")

    # Simulate what the API would return
    enabled_rubriques = community.get_enabled_rubriques()
    print(f"\n   ✅ Would return {enabled_rubriques.count()} enabled rubriques")

    for rubrique in enabled_rubriques[:5]:
        print(f"      • {rubrique.default_name} ({rubrique.template_type})")
        if rubrique.get_children().exists():
            for child in rubrique.get_children():
                print(f"         └ {child.default_name} ({child.template_type})")

    # Test performance
    import time
    start_time = time.time()
    for _ in range(10):
        community.get_rubrique_tree()
    end_time = time.time()

    avg_time = (end_time - start_time) / 10 * 1000
    print(f"\n⚡ Performance:")
    print(f"   Average time for get_rubrique_tree(): {avg_time:.2f}ms")

    if avg_time < 50:
        print(f"   ✅ EXCELLENT - Fast enough for real-time usage!")
    elif avg_time < 100:
        print(f"   ✅ GOOD - Acceptable performance")
    else:
        print(f"   ⚠️  SLOW - Consider caching")

    # Test with multiple communities
    print(f"\n📊 Testing Multiple Communities:")
    communities = Community.objects.all()[:5]

    for comm in communities:
        start = time.time()
        tree = comm.get_rubrique_tree()
        elapsed = (time.time() - start) * 1000
        print(f"   • {comm.name}: {len(tree)} rubriques ({elapsed:.2f}ms)")

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE!")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. Start Django server: docker-compose up")
    print("2. Test endpoint: curl http://localhost:8000/api/communities/{slug}/rubriques/")
    print("3. Check frontend integration in browser")
    print()

if __name__ == '__main__':
    test_rubriques_api()
