from communities.models import Community, RubriqueTemplate
from accounts.models import UserProfile

print("Testing populate_enabled_rubriques signal...")
print("=" * 60)

# Get first user to be the creator
creator = UserProfile.objects.first()
if not creator:
    print("ERROR: No user profiles found!")
else:
    print(f"Creator: {creator.user.username}")

    # Create a new community
    community = Community.objects.create(
        name="Test Signal Community",
        slug="test-signal-community",
        creator=creator,
        description="Testing signal population"
    )

    print(f"\nCreated community: {community.name}")
    print(f"enabled_rubriques type: {type(community.enabled_rubriques)}")
    print(f"enabled_rubriques value: {community.enabled_rubriques}")
    print(f"Number of enabled rubriques: {len(community.enabled_rubriques)}")

    # Check which rubriques were added
    if community.enabled_rubriques:
        print("\nEnabled rubriques:")
        for rubrique_id in community.enabled_rubriques:
            try:
                rubrique = RubriqueTemplate.objects.get(id=rubrique_id)
                print(f"  - {rubrique.template_type}: {rubrique.default_name}")
            except RubriqueTemplate.DoesNotExist:
                print(f"  - UUID {rubrique_id}: NOT FOUND")

    # Verify the required rubriques
    required_rubriques = RubriqueTemplate.objects.filter(
        is_required=True,
        is_active=True,
        parent__isnull=True
    )
    print(f"\nExpected required rubriques: {required_rubriques.count()}")
    for r in required_rubriques:
        print(f"  - {r.template_type}: {r.default_name}")

    # Clean up
    community.delete()
    print("\n✅ Test community deleted")
