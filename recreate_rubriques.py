"""
Create new rubrique structure based on frontend requirements.

This script will:
1. Deactivate all existing rubriques
2. Create new rubrique structure with proper parent-child relationships
3. Update all communities to use the new rubriques
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


# New rubrique structure based on frontend
NEW_RUBRIQUES = [
    {
        'template_type': 'accueil',
        'default_name': 'Accueil',
        'default_name_en': 'Home',
        'default_description': 'Tableau de bord principal',
        'default_icon': 'Home',
        'default_color': '#6366f1',
        'is_required': True,
        'allow_threads': False,
        'allow_direct_posts': True,
        'path': '001',
        'depth': 0,
        'parent': None,
    },
    # Nouvelles (parent)
    {
        'template_type': 'nouvelles',
        'default_name': 'Nouvelles',
        'default_name_en': 'News',
        'default_description': 'Actualités et annonces',
        'default_icon': 'Article',
        'default_color': '#3b82f6',
        'is_required': True,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '002',
        'depth': 0,
        'parent': None,
    },
    {
        'template_type': 'actualites',
        'default_name': 'Actualités',
        'default_name_en': 'News',
        'default_description': 'Actualités locales',
        'default_icon': 'Article',
        'default_color': '#3b82f6',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '002.001',
        'depth': 1,
        'parent': 'nouvelles',
    },
    {
        'template_type': 'annonces',
        'default_name': 'Annonces',
        'default_name_en': 'Announcements',
        'default_description': 'Annonces officielles',
        'default_icon': 'Campaign',
        'default_color': '#3b82f6',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '002.002',
        'depth': 1,
        'parent': 'nouvelles',
    },
    # Services (parent)
    {
        'template_type': 'services_section',
        'default_name': 'Services',
        'default_name_en': 'Services',
        'default_description': 'Services et infrastructures',
        'default_icon': 'HomeRepairService',
        'default_color': '#10b981',
        'is_required': True,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '003',
        'depth': 0,
        'parent': None,
    },
    {
        'template_type': 'services',
        'default_name': 'Services municipaux',
        'default_name_en': 'Municipal Services',
        'default_description': 'Services publics',
        'default_icon': 'HomeRepairService',
        'default_color': '#10b981',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '003.001',
        'depth': 1,
        'parent': 'services_section',
    },
    {
        'template_type': 'transport',
        'default_name': 'Transport',
        'default_name_en': 'Transportation',
        'default_description': 'Transport et circulation',
        'default_icon': 'DirectionsBus',
        'default_color': '#f59e0b',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '003.002',
        'depth': 1,
        'parent': 'services_section',
    },
    {
        'template_type': 'commerces',
        'default_name': 'Commerces',
        'default_name_en': 'Businesses',
        'default_description': 'Commerce local',
        'default_icon': 'Business',
        'default_color': '#10b981',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '003.003',
        'depth': 1,
        'parent': 'services_section',
    },
    # Culture (parent)
    {
        'template_type': 'culture_section',
        'default_name': 'Culture',
        'default_name_en': 'Culture',
        'default_description': 'Événements et patrimoine culturel',
        'default_icon': 'TheaterComedy',
        'default_color': '#a855f7',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '004',
        'depth': 0,
        'parent': None,
    },
    {
        'template_type': 'culture',
        'default_name': 'Événements culturels',
        'default_name_en': 'Cultural Events',
        'default_description': 'Événements culturels',
        'default_icon': 'TheaterComedy',
        'default_color': '#a855f7',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '004.001',
        'depth': 1,
        'parent': 'culture_section',
    },
    {
        'template_type': 'litterature',
        'default_name': 'Littérature',
        'default_name_en': 'Literature',
        'default_description': 'Œuvres littéraires',
        'default_icon': 'MenuBook',
        'default_color': '#6366f1',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '004.002',
        'depth': 1,
        'parent': 'culture_section',
    },
    {
        'template_type': 'poesie',
        'default_name': 'Poésie',
        'default_name_en': 'Poetry',
        'default_description': 'Poèmes et vers',
        'default_icon': 'Create',
        'default_color': '#8b5cf6',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '004.003',
        'depth': 1,
        'parent': 'culture_section',
    },
    {
        'template_type': 'histoire',
        'default_name': 'Histoire',
        'default_name_en': 'History',
        'default_description': 'Patrimoine local',
        'default_icon': 'History',
        'default_color': '#78716c',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '004.004',
        'depth': 1,
        'parent': 'culture_section',
    },
    # Économie (parent)
    {
        'template_type': 'economie_section',
        'default_name': 'Économie',
        'default_name_en': 'Economy',
        'default_description': 'Développement économique',
        'default_icon': 'TrendingUp',
        'default_color': '#059669',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '005',
        'depth': 0,
        'parent': None,
    },
    {
        'template_type': 'economie',
        'default_name': 'Développement économique',
        'default_name_en': 'Economic Development',
        'default_description': 'Économie locale',
        'default_icon': 'TrendingUp',
        'default_color': '#059669',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '005.001',
        'depth': 1,
        'parent': 'economie_section',
    },
    {
        'template_type': 'opportunites',
        'default_name': 'Opportunités',
        'default_name_en': 'Opportunities',
        'default_description': "Opportunités d'affaires",
        'default_icon': 'WorkOutline',
        'default_color': '#059669',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '005.002',
        'depth': 1,
        'parent': 'economie_section',
    },
    # Art (parent)
    {
        'template_type': 'art_section',
        'default_name': 'Art',
        'default_name_en': 'Art',
        'default_description': 'Créations et expositions artistiques',
        'default_icon': 'Palette',
        'default_color': '#ec4899',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '006',
        'depth': 0,
        'parent': None,
    },
    {
        'template_type': 'art',
        'default_name': 'Créations artistiques',
        'default_name_en': 'Artistic Creations',
        'default_description': 'Créations artistiques',
        'default_icon': 'Palette',
        'default_color': '#ec4899',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '006.001',
        'depth': 1,
        'parent': 'art_section',
    },
    {
        'template_type': 'expositions',
        'default_name': 'Expositions',
        'default_name_en': 'Exhibitions',
        'default_description': "Expositions d'art",
        'default_icon': 'Museum',
        'default_color': '#ec4899',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '006.002',
        'depth': 1,
        'parent': 'art_section',
    },
    # Sports (parent)
    {
        'template_type': 'sports_section',
        'default_name': 'Sports',
        'default_name_en': 'Sports',
        'default_description': 'Activités et événements sportifs',
        'default_icon': 'Sports',
        'default_color': '#ef4444',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '007',
        'depth': 0,
        'parent': None,
    },
    {
        'template_type': 'sport',
        'default_name': 'Activités sportives',
        'default_name_en': 'Sports Activities',
        'default_description': 'Activités sportives',
        'default_icon': 'Sports',
        'default_color': '#ef4444',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '007.001',
        'depth': 1,
        'parent': 'sports_section',
    },
    {
        'template_type': 'evenements_sportifs',
        'default_name': 'Événements sportifs',
        'default_name_en': 'Sports Events',
        'default_description': 'Compétitions et événements',
        'default_icon': 'EmojiEvents',
        'default_color': '#ef4444',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '007.002',
        'depth': 1,
        'parent': 'sports_section',
    },
    # Distinction (parent)
    {
        'template_type': 'distinction_section',
        'default_name': 'Distinction',
        'default_name_en': 'Distinction',
        'default_description': 'Reconnaissances et distinctions',
        'default_icon': 'EmojiEvents',
        'default_color': '#fbbf24',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '008',
        'depth': 0,
        'parent': None,
    },
    {
        'template_type': 'reconnaissance',
        'default_name': 'Reconnaissances',
        'default_name_en': 'Recognition',
        'default_description': 'Valorisation communautaire',
        'default_icon': 'EmojiEvents',
        'default_color': '#fbbf24',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '008.001',
        'depth': 1,
        'parent': 'distinction_section',
    },
    {
        'template_type': 'prix',
        'default_name': 'Prix et honneurs',
        'default_name_en': 'Awards and Honors',
        'default_description': 'Prix et distinctions',
        'default_icon': 'MilitaryTech',
        'default_color': '#fbbf24',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '008.002',
        'depth': 1,
        'parent': 'distinction_section',
    },
    # Photos et Vidéos (parent)
    {
        'template_type': 'photos_videos_section',
        'default_name': 'Photos et Vidéos',
        'default_name_en': 'Photos and Videos',
        'default_description': 'Galerie multimédia',
        'default_icon': 'PhotoCamera',
        'default_color': '#06b6d4',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '009',
        'depth': 0,
        'parent': None,
    },
    {
        'template_type': 'photographie',
        'default_name': 'Galerie photos',
        'default_name_en': 'Photo Gallery',
        'default_description': 'Images et captures',
        'default_icon': 'PhotoCamera',
        'default_color': '#06b6d4',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '009.001',
        'depth': 1,
        'parent': 'photos_videos_section',
    },
    {
        'template_type': 'videos',
        'default_name': 'Vidéos',
        'default_name_en': 'Videos',
        'default_description': 'Contenu vidéo',
        'default_icon': 'VideoLibrary',
        'default_color': '#06b6d4',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '009.002',
        'depth': 1,
        'parent': 'photos_videos_section',
    },
    # Participation Citoyenne (parent)
    {
        'template_type': 'participation_section',
        'default_name': 'Participation Citoyenne',
        'default_name_en': 'Citizen Participation',
        'default_description': 'Engagement citoyen',
        'default_icon': 'HowToVote',
        'default_color': '#8b5cf6',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '010',
        'depth': 0,
        'parent': None,
    },
    {
        'template_type': 'consultations',
        'default_name': 'Consultations',
        'default_name_en': 'Consultations',
        'default_description': 'Consultations publiques',
        'default_icon': 'QuestionAnswer',
        'default_color': '#8b5cf6',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '010.001',
        'depth': 1,
        'parent': 'participation_section',
    },
    {
        'template_type': 'suggestions',
        'default_name': 'Suggestions',
        'default_name_en': 'Suggestions',
        'default_description': 'Boîte à suggestions',
        'default_icon': 'Lightbulb',
        'default_color': '#8b5cf6',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '010.002',
        'depth': 1,
        'parent': 'participation_section',
    },
    {
        'template_type': 'evenements',
        'default_name': 'Événements',
        'default_name_en': 'Events',
        'default_description': 'Événements participatifs',
        'default_icon': 'Event',
        'default_color': '#8b5cf6',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
        'path': '010.003',
        'depth': 1,
        'parent': 'participation_section',
    },
]


@transaction.atomic
def recreate_rubriques():
    """Recreate rubrique structure."""
    print("=" * 80)
    print("RECREATING RUBRIQUE STRUCTURE")
    print("=" * 80)

    # Step 1: Deactivate all existing rubriques
    print("\n1. Deactivating existing rubriques...")
    old_rubriques = RubriqueTemplate.objects.filter(is_active=True)
    old_count = old_rubriques.count()
    old_rubriques.update(is_active=False)
    print(f"   ✓ Deactivated {old_count} rubriques")

    # Step 2: Create new rubriques
    print("\n2. Creating new rubriques...")
    created_rubriques = {}

    # First pass: Create all rubriques without parent relationships
    for rubrique_data in NEW_RUBRIQUES:
        data = rubrique_data.copy()
        parent_template_type = data.pop('parent', None)

        # Try to find existing rubrique by template_type
        rubrique, created = RubriqueTemplate.objects.get_or_create(
            template_type=data['template_type'],
            defaults=data
        )

        if not created:
            # Update existing rubrique
            for key, value in data.items():
                setattr(rubrique, key, value)
            rubrique.is_active = True
            rubrique.save()

        created_rubriques[data['template_type']] = {
            'rubrique': rubrique,
            'parent_template_type': parent_template_type
        }

        status = "Created" if created else "Updated"
        depth_indicator = "  " * rubrique.depth + ("└─ " if rubrique.depth > 0 else "• ")
        print(f"   {status}: {depth_indicator}{rubrique.default_name} ({rubrique.template_type})")

    # Second pass: Set parent relationships
    print("\n3. Setting parent relationships...")
    for template_type, data in created_rubriques.items():
        parent_template_type = data['parent_template_type']
        if parent_template_type:
            rubrique = data['rubrique']
            parent_rubrique = created_rubriques[parent_template_type]['rubrique']
            rubrique.parent = parent_rubrique
            rubrique.save()
            print(f"   ✓ {rubrique.default_name} → parent: {parent_rubrique.default_name}")

    # Step 3: Update all communities with new rubriques
    print("\n4. Updating communities...")
    all_active_rubriques = RubriqueTemplate.objects.filter(is_active=True)
    rubrique_ids = [str(r.id) for r in all_active_rubriques]

    for community in Community.objects.filter(is_deleted=False):
        community.enabled_rubriques = rubrique_ids
        community.save()
        print(f"   ✓ {community.name}: {len(rubrique_ids)} rubriques")

    print("\n" + "=" * 80)
    print("FINAL RUBRIQUE STRUCTURE:")
    print("=" * 80)

    rubriques = RubriqueTemplate.objects.filter(is_active=True).order_by('path')
    for r in rubriques:
        depth_indicator = "  " * r.depth + ("└─ " if r.depth > 0 else "• ")
        print(f"{depth_indicator}{r.default_name:40} ({r.template_type})")

    print(f"\nTotal: {rubriques.count()} active rubriques")
    print(f"Parents: {rubriques.filter(depth=0).count()}")
    print(f"Children: {rubriques.filter(depth=1).count()}")


if __name__ == '__main__':
    recreate_rubriques()
    print("\n✅ Rubrique structure recreated successfully!")
