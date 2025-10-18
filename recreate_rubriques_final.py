"""
Recreate rubriques from scratch with correct hierarchical structure.
This script will:
1. Deactivate ALL existing rubriques
2. Create new rubriques matching the frontend structure exactly
3. Update all communities with the new rubriques
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from communities.models import RubriqueTemplate, Community
from django.db import transaction


# Complete rubrique structure matching frontend exactly
# NOTE: We use default_order instead of path because the save() method
# auto-generates paths based on default_order
NEW_RUBRIQUES = [
    # Accueil - Main page (001)
    {
        'template_type': 'accueil',
        'default_name': 'Accueil',
        'default_icon': 'Home',
        'default_order': 1,
        'parent': None,
    },

    # Nouvelles (002) with children
    {
        'template_type': 'nouvelles',
        'default_name': 'Nouvelles',
        'default_icon': 'Article',
        'default_order': 2,
        'parent': None,
    },
    {
        'template_type': 'actualites',
        'default_name': 'Actualités',
        'default_icon': 'FiberNew',
        'default_order': 1,
        'parent': 'nouvelles',
    },
    {
        'template_type': 'annonces',
        'default_name': 'Annonces',
        'default_icon': 'Campaign',
        'default_order': 2,
        'parent': 'nouvelles',
    },

    # Services (003) with children
    {
        'template_type': 'services_section',
        'default_name': 'Services',
        'default_icon': 'HomeRepairService',
        'default_order': 3,
        'parent': None,
    },
    {
        'template_type': 'services',
        'default_name': 'Services municipaux',
        'default_icon': 'AccountBalance',
        'default_order': 1,
        'parent': 'services_section',
    },
    {
        'template_type': 'transport',
        'default_name': 'Transport',
        'default_icon': 'DirectionsBus',
        'default_order': 2,
        'parent': 'services_section',
    },
    {
        'template_type': 'commerces',
        'default_name': 'Commerces',
        'default_icon': 'Storefront',
        'default_order': 3,
        'parent': 'services_section',
    },

    # Culture (004) with children
    {
        'template_type': 'culture_section',
        'default_name': 'Culture',
        'default_icon': 'TheaterComedy',
        'default_order': 4,
        'parent': None,
    },
    {
        'template_type': 'culture',
        'default_name': 'Événements culturels',
        'default_icon': 'Event',
        'default_order': 1,
        'parent': 'culture_section',
    },
    {
        'template_type': 'litterature',
        'default_name': 'Littérature',
        'default_icon': 'MenuBook',
        'default_order': 2,
        'parent': 'culture_section',
    },
    {
        'template_type': 'poesie',
        'default_name': 'Poésie',
        'default_icon': 'AutoStories',
        'default_order': 3,
        'parent': 'culture_section',
    },
    {
        'template_type': 'histoire',
        'default_name': 'Histoire',
        'default_icon': 'HistoryEdu',
        'default_order': 4,
        'parent': 'culture_section',
    },

    # Économie (005) with children
    {
        'template_type': 'economie_section',
        'default_name': 'Économie',
        'default_icon': 'TrendingUp',
        'default_order': 5,
        'parent': None,
    },
    {
        'template_type': 'economie',
        'default_name': 'Développement économique',
        'default_icon': 'Business',
        'default_order': 1,
        'parent': 'economie_section',
    },
    {
        'template_type': 'opportunites',
        'default_name': 'Opportunités',
        'default_icon': 'WorkOutline',
        'default_order': 2,
        'parent': 'economie_section',
    },

    # Art (006) with children
    {
        'template_type': 'art_section',
        'default_name': 'Art',
        'default_icon': 'Palette',
        'default_order': 6,
        'parent': None,
    },
    {
        'template_type': 'art',
        'default_name': 'Créations artistiques',
        'default_icon': 'Brush',
        'default_order': 1,
        'parent': 'art_section',
    },
    {
        'template_type': 'expositions',
        'default_name': 'Expositions',
        'default_icon': 'Museum',
        'default_order': 2,
        'parent': 'art_section',
    },

    # Sports (007) with children
    {
        'template_type': 'sports_section',
        'default_name': 'Sports',
        'default_icon': 'FitnessCenter',
        'default_order': 7,
        'parent': None,
    },
    {
        'template_type': 'sport',
        'default_name': 'Activités sportives',
        'default_icon': 'DirectionsRun',
        'default_order': 1,
        'parent': 'sports_section',
    },
    {
        'template_type': 'evenements_sportifs',
        'default_name': 'Événements sportifs',
        'default_icon': 'EmojiEvents',
        'default_order': 2,
        'parent': 'sports_section',
    },

    # Distinction (008) with children
    {
        'template_type': 'distinction_section',
        'default_name': 'Distinction',
        'default_icon': 'Stars',
        'default_order': 8,
        'parent': None,
    },
    {
        'template_type': 'reconnaissance',
        'default_name': 'Reconnaissances',
        'default_icon': 'CardGiftcard',
        'default_order': 1,
        'parent': 'distinction_section',
    },
    {
        'template_type': 'prix',
        'default_name': 'Prix et honneurs',
        'default_icon': 'MilitaryTech',
        'default_order': 2,
        'parent': 'distinction_section',
    },

    # Photos et Vidéos (009) with children
    {
        'template_type': 'photos_videos_section',
        'default_name': 'Photos et Vidéos',
        'default_icon': 'PermMedia',
        'default_order': 9,
        'parent': None,
    },
    {
        'template_type': 'photographie',
        'default_name': 'Galerie photos',
        'default_icon': 'PhotoLibrary',
        'default_order': 1,
        'parent': 'photos_videos_section',
    },
    {
        'template_type': 'videos',
        'default_name': 'Vidéos',
        'default_icon': 'VideoLibrary',
        'default_order': 2,
        'parent': 'photos_videos_section',
    },

    # Participation Citoyenne (010) with children
    {
        'template_type': 'participation_section',
        'default_name': 'Participation Citoyenne',
        'default_icon': 'HowToVote',
        'default_order': 10,
        'parent': None,
    },
    {
        'template_type': 'consultations',
        'default_name': 'Consultations',
        'default_icon': 'QuestionAnswer',
        'default_order': 1,
        'parent': 'participation_section',
    },
    {
        'template_type': 'suggestions',
        'default_name': 'Suggestions',
        'default_icon': 'Lightbulb',
        'default_order': 2,
        'parent': 'participation_section',
    },
    {
        'template_type': 'evenements',
        'default_name': 'Événements',
        'default_icon': 'CalendarToday',
        'default_order': 3,
        'parent': 'participation_section',
    },
]


@transaction.atomic
def recreate_rubriques():
    """Recreate all rubriques from scratch."""
    print("=" * 80)
    print("RECREATING RUBRIQUES FROM SCRATCH")
    print("=" * 80)

    # Step 1: Remove rubrique references from posts and threads
    print("\n1. Removing rubrique references from posts and threads...")
    from content.models import Post
    from communities.models import Thread

    posts_updated = Post.objects.filter(rubrique_template__isnull=False).update(rubrique_template=None)
    threads_updated = Thread.objects.filter(rubrique_template__isnull=False).update(rubrique_template=None)
    print(f"   ✓ Cleared {posts_updated} posts and {threads_updated} threads")

    # Step 2: Delete ALL existing rubriques
    print("\n2. Deleting all existing rubriques...")
    existing = RubriqueTemplate.objects.all()
    count = existing.count()
    existing.delete()
    print(f"   ✓ Deleted {count} existing rubriques")

    # Step 3: Create new rubriques (parents first, then children)
    print("\n3. Creating new rubriques...")
    created_rubriques = {}

    # First pass: Create all rubriques
    for rubrique_data in NEW_RUBRIQUES:
        template_type = rubrique_data['template_type']

        rubrique = RubriqueTemplate.objects.create(
            template_type=template_type,
            default_name=rubrique_data['default_name'],
            default_icon=rubrique_data['default_icon'],
            default_order=rubrique_data['default_order'],
            is_active=True,
        )

        created_rubriques[template_type] = rubrique

        depth_indicator = "  " * rubrique.depth + ("└─ " if rubrique.depth > 0 else "• ")
        print(f"   {depth_indicator}{rubrique.default_name:40} ({template_type})")

    # Second pass: Set parent relationships
    print("\n4. Setting parent relationships...")
    for rubrique_data in NEW_RUBRIQUES:
        if rubrique_data['parent']:
            child = created_rubriques[rubrique_data['template_type']]
            parent = created_rubriques[rubrique_data['parent']]
            child.parent = parent
            child.save()
            print(f"   ✓ {child.default_name} → parent: {parent.default_name}")

    # Step 5: Update all communities with new rubriques
    print("\n5. Updating communities with new rubriques...")
    new_rubrique_ids = [str(r.id) for r in created_rubriques.values()]

    communities = Community.objects.all()
    for community in communities:
        community.enabled_rubriques = new_rubrique_ids
        community.save()
        print(f"   ✓ {community.name}: {len(new_rubrique_ids)} rubriques enabled")

    # Step 6: Display final structure
    print("\n" + "=" * 80)
    print("FINAL RUBRIQUE STRUCTURE:")
    print("=" * 80)

    final_rubriques = RubriqueTemplate.objects.filter(
        is_active=True
    ).order_by('path')

    for r in final_rubriques:
        depth_indicator = "  " * r.depth + ("└─ " if r.depth > 0 else "• ")
        parent_info = f" (parent: {r.parent.default_name})" if r.parent else ""
        print(f"{depth_indicator}{r.default_name:40} | {r.path:10} | {r.default_icon}{parent_info}")

    print(f"\nTotal: {final_rubriques.count()} active rubriques")

    # Count parents and children
    parents = final_rubriques.filter(depth=0).count()
    children = final_rubriques.filter(depth=1).count()
    print(f"  - {parents} parent sections")
    print(f"  - {children} child rubriques")


if __name__ == '__main__':
    recreate_rubriques()
    print("\n✅ Rubriques recreated successfully!")
