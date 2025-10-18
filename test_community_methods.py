from communities.models import Community, RubriqueTemplate
from accounts.models import UserProfile

print("=" * 60)
print("TESTING COMMUNITY HELPER METHODS")
print("=" * 60)

# Get first user
creator = UserProfile.objects.first()

# Create a test community
community = Community.objects.create(
    name="Test Methods Community",
    slug="test-methods-community",
    creator=creator,
    description="Testing helper methods"
)

print(f"\n1. Created community: {community.name}")
print(f"   enabled_rubriques: {community.enabled_rubriques}")
print(f"   Count: {len(community.enabled_rubriques)}")

# Test get_enabled_rubriques()
print("\n2. Testing get_enabled_rubriques():")
enabled = community.get_enabled_rubriques()
print(f"   Queryset count: {enabled.count()}")
for r in enabled:
    print(f"   - {r.template_type}: {r.default_name}")

# Test is_rubrique_enabled()
print("\n3. Testing is_rubrique_enabled():")
actualites = RubriqueTemplate.objects.filter(template_type='actualites').first()
sport = RubriqueTemplate.objects.filter(template_type='sport').first()

if actualites:
    print(f"   actualites enabled: {community.is_rubrique_enabled(actualites.id)}")
if sport:
    print(f"   sport enabled: {community.is_rubrique_enabled(sport.id)}")

# Test add_rubrique()
print("\n4. Testing add_rubrique():")
if sport:
    result = community.add_rubrique(sport.id)
    print(f"   Added sport: {result}")
    print(f"   sport now enabled: {community.is_rubrique_enabled(sport.id)}")
    print(f"   Count: {len(community.enabled_rubriques)}")

# Test get_rubrique_tree()
print("\n5. Testing get_rubrique_tree():")
tree = community.get_rubrique_tree()
print(f"   Tree has {len(tree)} top-level rubriques")
for node in tree:
    print(f"   - {node['template_type']}: {node['name']}")
    if node['children']:
        for child in node['children']:
            print(f"       → {child['template_type']}: {child['name']}")

# Test remove_rubrique()
print("\n6. Testing remove_rubrique():")
if sport:
    # Try to remove sport (optional, should succeed)
    result = community.remove_rubrique(sport.id)
    print(f"   Removed sport: {result}")
    print(f"   sport now enabled: {community.is_rubrique_enabled(sport.id)}")

if actualites:
    # Try to remove actualites (required, should fail)
    result = community.remove_rubrique(actualites.id)
    print(f"   Removed actualites (required): {result}")
    print(f"   actualites still enabled: {community.is_rubrique_enabled(actualites.id)}")

print("\n7. Final state:")
print(f"   enabled_rubriques: {community.enabled_rubriques}")
print(f"   Count: {len(community.enabled_rubriques)}")

# Clean up
community.delete()
print("\n✅ Test community deleted")
print("=" * 60)
