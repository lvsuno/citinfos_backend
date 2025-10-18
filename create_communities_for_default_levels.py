"""
Create communities for all existing divisions at their country's default level.

This script:
1. Finds all divisions at the default admin level for their country
2. Creates a public community for each division (if not already exists)
3. Auto-populates all active rubriques for each community
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from core.models import AdministrativeDivision, Country
from communities.models import Community
from communities.utils import get_or_create_default_community
from django.db import transaction
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_communities_for_default_levels():
    """Create communities for all divisions at default levels."""

    print("=" * 80)
    print("CREATING COMMUNITIES FOR DEFAULT ADMIN LEVELS")
    print("=" * 80)

    countries = Country.objects.all()

    total_created = 0
    total_existing = 0
    total_errors = 0

    for country in countries:
        default_level = country.default_admin_level

        print(f"\n🌍 {country.name} (Default level: {default_level})")
        print("-" * 80)

        # Get all divisions at the default level for this country
        divisions_at_default_level = AdministrativeDivision.objects.filter(
            country=country,
            admin_level=default_level
        ).order_by('name')

        total_divisions = divisions_at_default_level.count()
        print(f"Found {total_divisions} divisions at level {default_level}\n")

        if total_divisions == 0:
            print("⚠️  No divisions found at this level")
            continue

        created_count = 0
        existing_count = 0
        error_count = 0

        for i, division in enumerate(divisions_at_default_level, 1):
            try:
                # Check if community already exists
                existing_community = Community.objects.filter(
                    division=division,
                    is_deleted=False
                ).first()

                if existing_community:
                    print(f"  [{i}/{total_divisions}] ✅ {division.name} (already has community: {existing_community.slug})")
                    existing_count += 1
                else:
                    # Create community
                    with transaction.atomic():
                        community = get_or_create_default_community(division)
                        print(f"  [{i}/{total_divisions}] ✨ {division.name} → Created: {community.slug}")
                        created_count += 1

            except Exception as e:
                print(f"  [{i}/{total_divisions}] ❌ {division.name} → Error: {str(e)}")
                error_count += 1
                logger.error(f"Failed to create community for {division.name}: {str(e)}", exc_info=True)

        print(f"\n📊 {country.name} Summary:")
        print(f"   Created: {created_count}")
        print(f"   Already existed: {existing_count}")
        print(f"   Errors: {error_count}")

        total_created += created_count
        total_existing += existing_count
        total_errors += error_count

    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"✨ Total communities created: {total_created}")
    print(f"✅ Total communities already existed: {total_existing}")
    print(f"❌ Total errors: {total_errors}")
    print(f"📌 Total communities now: {Community.objects.filter(is_deleted=False).count()}")
    print("=" * 80)


if __name__ == '__main__':
    create_communities_for_default_levels()
