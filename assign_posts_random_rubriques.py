"""
Randomly assign rubriques to existing posts.

This script updates all existing Post objects that don't have a rubrique_template
assigned, randomly selecting from their community's enabled rubriques.
"""

import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from content.models import Post
from communities.models import RubriqueTemplate


def assign_random_rubriques_to_posts():
    print("=" * 80)
    print("ASSIGNING RANDOM RUBRIQUES TO EXISTING POSTS")
    print("=" * 80)

    # Get all posts without rubrique_template
    posts_without_rubrique = Post.objects.filter(
        rubrique_template__isnull=True
    ).select_related('community')

    total_posts = posts_without_rubrique.count()
    print(f"\n📊 Found {total_posts} posts without rubrique assignment")

    if total_posts == 0:
        print("\n✅ All posts already have rubriques assigned!")
        return

    updated_count = 0
    error_count = 0
    community_stats = {}

    for post in posts_without_rubrique:
        try:
            community = post.community

            if not community:
                print(f"   ⚠️  Post {post.id} has no community, skipping")
                error_count += 1
                continue

            # Get enabled rubriques for this community
            if not community.enabled_rubriques:
                print(f"   ⚠️  Community {community.name} has no enabled rubriques")
                error_count += 1
                continue

            # Get actual RubriqueTemplate objects
            enabled_templates = RubriqueTemplate.objects.filter(
                id__in=community.enabled_rubriques,
                is_active=True
            )

            if not enabled_templates.exists():
                print(f"   ⚠️  No active templates for community {community.name}")
                error_count += 1
                continue

            # Randomly select a rubrique (prefer main rubriques)
            main_rubriques = enabled_templates.filter(depth=0)
            subsection_rubriques = enabled_templates.filter(depth__gt=0)

            # 70% chance for main rubrique, 30% for subsection
            if main_rubriques.exists():
                if not subsection_rubriques.exists() or random.random() < 0.7:
                    selected_rubrique = random.choice(list(main_rubriques))
                else:
                    selected_rubrique = random.choice(list(subsection_rubriques))
            else:
                selected_rubrique = random.choice(list(enabled_templates))

            # Assign the rubrique
            post.rubrique_template = selected_rubrique
            post.save(update_fields=['rubrique_template'])

            updated_count += 1

            # Track stats per community
            comm_key = f"{community.name} ({community.slug})"
            if comm_key not in community_stats:
                community_stats[comm_key] = {}

            rubrique_name = selected_rubrique.default_name
            if rubrique_name not in community_stats[comm_key]:
                community_stats[comm_key][rubrique_name] = 0
            community_stats[comm_key][rubrique_name] += 1

            if updated_count % 10 == 0:
                print(f"   ✅ Updated {updated_count}/{total_posts} posts...")

        except Exception as e:
            print(f"   ❌ Error updating post {post.id}: {e}")
            error_count += 1

    print("\n" + "=" * 80)
    print("✅ UPDATE COMPLETE!")
    print("=" * 80)

    print(f"\n📊 Summary:")
    print(f"   • Total posts processed: {total_posts}")
    print(f"   • Successfully updated: {updated_count}")
    print(f"   • Errors: {error_count}")

    if community_stats:
        print(f"\n📈 Distribution by Community:")
        for comm_name, rubriques in sorted(community_stats.items()):
            print(f"\n   {comm_name}:")
            total_for_comm = sum(rubriques.values())
            for rubrique, count in sorted(rubriques.items(),
                                          key=lambda x: x[1], reverse=True):
                percentage = (count / total_for_comm) * 100
                print(f"      • {rubrique}: {count} posts ({percentage:.1f}%)")

    print()


if __name__ == '__main__':
    assign_random_rubriques_to_posts()
