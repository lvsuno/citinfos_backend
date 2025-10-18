"""
Script to update rubrique structure to match new frontend design.

New structure:
- Main sections with subsections (2-level hierarchy)
- Updated names and paths
- New rubriques added
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from communities.models import RubriqueTemplate, Community


# New rubrique structure matching frontend
NEW_RUBRIQUES = [
    # Accueil (standalone, no parent)
    {
        'template_type': 'accueil',
        'default_name': 'Accueil',
        'default_name_en': 'Home',
        'default_description': 'Tableau de bord principal',
        'default_icon': 'Home',
        'default_color': '#6366f1',
        'depth': 0,
        'path': '000',
        'is_required': True,
        'allow_threads': False,
        'allow_direct_posts': False,
    },

    # Nouvelles (parent)
    {
        'template_type': 'nouvelles',
        'default_name': 'Nouvelles',
        'default_name_en': 'News',
        'default_description': 'Nouvelles et actualités',
        'default_icon': 'Article',
        'default_color': '#3b82f6',
        'depth': 0,
        'path': '001',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Actualités (child of Nouvelles)
    {
        'template_type': 'actualites',
        'default_name': 'Actualités',
        'default_name_en': 'News',
        'default_description': 'Actualités locales',
        'default_icon': 'Article',
        'default_color': '#3b82f6',
        'depth': 1,
        'path': '001.001',
        'parent_type': 'nouvelles',
        'is_required': True,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Annonces (child of Nouvelles)
    {
        'template_type': 'annonces',
        'default_name': 'Annonces',
        'default_name_en': 'Announcements',
        'default_description': 'Annonces officielles',
        'default_icon': 'Campaign',
        'default_color': '#3b82f6',
        'depth': 1,
        'path': '001.002',
        'parent_type': 'nouvelles',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Services (parent)
    {
        'template_type': 'services_parent',
        'default_name': 'Services',
        'default_name_en': 'Services',
        'default_description': 'Services et infrastructures',
        'default_icon': 'MiscellaneousServices',
        'default_color': '#10b981',
        'depth': 0,
        'path': '002',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': False,
    },

    # Services municipaux (child of Services)
    {
        'template_type': 'services',
        'default_name': 'Services municipaux',
        'default_name_en': 'Municipal Services',
        'default_description': 'Services publics',
        'default_icon': 'MiscellaneousServices',
        'default_color': '#10b981',
        'depth': 1,
        'path': '002.001',
        'parent_type': 'services_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Transport (child of Services)
    {
        'template_type': 'transport',
        'default_name': 'Transport',
        'default_name_en': 'Transportation',
        'default_description': 'Transport et circulation',
        'default_icon': 'DirectionsBus',
        'default_color': '#10b981',
        'depth': 1,
        'path': '002.002',
        'parent_type': 'services_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Commerces (child of Services)
    {
        'template_type': 'commerces',
        'default_name': 'Commerces',
        'default_name_en': 'Commerce',
        'default_description': 'Commerce local',
        'default_icon': 'Business',
        'default_color': '#10b981',
        'depth': 1,
        'path': '002.003',
        'parent_type': 'services_parent',
        'is_required': True,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Culture (parent)
    {
        'template_type': 'culture_parent',
        'default_name': 'Culture',
        'default_name_en': 'Culture',
        'default_description': 'Culture et patrimoine',
        'default_icon': 'TheaterComedy',
        'default_color': '#a855f7',
        'depth': 0,
        'path': '003',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': False,
    },

    # Événements culturels (child of Culture)
    {
        'template_type': 'culture',
        'default_name': 'Événements culturels',
        'default_name_en': 'Cultural Events',
        'default_description': 'Événements culturels',
        'default_icon': 'TheaterComedy',
        'default_color': '#a855f7',
        'depth': 1,
        'path': '003.001',
        'parent_type': 'culture_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Littérature (child of Culture)
    {
        'template_type': 'litterature',
        'default_name': 'Littérature',
        'default_name_en': 'Literature',
        'default_description': 'Œuvres littéraires',
        'default_icon': 'MenuBook',
        'default_color': '#a855f7',
        'depth': 1,
        'path': '003.002',
        'parent_type': 'culture_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Poésie (child of Culture)
    {
        'template_type': 'poesie',
        'default_name': 'Poésie',
        'default_name_en': 'Poetry',
        'default_description': 'Poèmes et vers',
        'default_icon': 'Create',
        'default_color': '#a855f7',
        'depth': 1,
        'path': '003.003',
        'parent_type': 'culture_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Histoire (child of Culture)
    {
        'template_type': 'histoire',
        'default_name': 'Histoire',
        'default_name_en': 'History',
        'default_description': 'Patrimoine local',
        'default_icon': 'History',
        'default_color': '#a855f7',
        'depth': 1,
        'path': '003.004',
        'parent_type': 'culture_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Économie (parent)
    {
        'template_type': 'economie_parent',
        'default_name': 'Économie',
        'default_name_en': 'Economy',
        'default_description': 'Économie et développement',
        'default_icon': 'TrendingUp',
        'default_color': '#f59e0b',
        'depth': 0,
        'path': '004',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': False,
    },

    # Développement économique (child of Économie)
    {
        'template_type': 'economie',
        'default_name': 'Développement économique',
        'default_name_en': 'Economic Development',
        'default_description': 'Économie locale',
        'default_icon': 'TrendingUp',
        'default_color': '#f59e0b',
        'depth': 1,
        'path': '004.001',
        'parent_type': 'economie_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Opportunités (child of Économie)
    {
        'template_type': 'opportunites',
        'default_name': 'Opportunités',
        'default_name_en': 'Opportunities',
        'default_description': "Opportunités d'affaires",
        'default_icon': 'Lightbulb',
        'default_color': '#f59e0b',
        'depth': 1,
        'path': '004.002',
        'parent_type': 'economie_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Art (parent)
    {
        'template_type': 'art_parent',
        'default_name': 'Art',
        'default_name_en': 'Art',
        'default_description': 'Art et créations',
        'default_icon': 'Palette',
        'default_color': '#ec4899',
        'depth': 0,
        'path': '005',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': False,
    },

    # Créations artistiques (child of Art)
    {
        'template_type': 'art',
        'default_name': 'Créations artistiques',
        'default_name_en': 'Artistic Creations',
        'default_description': 'Créations artistiques',
        'default_icon': 'Palette',
        'default_color': '#ec4899',
        'depth': 1,
        'path': '005.001',
        'parent_type': 'art_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Expositions (child of Art)
    {
        'template_type': 'expositions',
        'default_name': 'Expositions',
        'default_name_en': 'Exhibitions',
        'default_description': "Expositions d'art",
        'default_icon': 'Museum',
        'default_color': '#ec4899',
        'depth': 1,
        'path': '005.002',
        'parent_type': 'art_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Sports (parent)
    {
        'template_type': 'sports_parent',
        'default_name': 'Sports',
        'default_name_en': 'Sports',
        'default_description': 'Sports et activités',
        'default_icon': 'Sports',
        'default_color': '#ef4444',
        'depth': 0,
        'path': '006',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': False,
    },

    # Activités sportives (child of Sports)
    {
        'template_type': 'sport',
        'default_name': 'Activités sportives',
        'default_name_en': 'Sports Activities',
        'default_description': 'Activités sportives',
        'default_icon': 'Sports',
        'default_color': '#ef4444',
        'depth': 1,
        'path': '006.001',
        'parent_type': 'sports_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Événements sportifs (child of Sports)
    {
        'template_type': 'evenements_sportifs',
        'default_name': 'Événements sportifs',
        'default_name_en': 'Sports Events',
        'default_description': 'Compétitions et événements',
        'default_icon': 'EmojiEvents',
        'default_color': '#ef4444',
        'depth': 1,
        'path': '006.002',
        'parent_type': 'sports_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Distinction (parent)
    {
        'template_type': 'distinction_parent',
        'default_name': 'Distinction',
        'default_name_en': 'Recognition',
        'default_description': 'Reconnaissances et distinctions',
        'default_icon': 'EmojiEvents',
        'default_color': '#fbbf24',
        'depth': 0,
        'path': '007',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': False,
    },

    # Reconnaissances (child of Distinction)
    {
        'template_type': 'reconnaissance',
        'default_name': 'Reconnaissances',
        'default_name_en': 'Recognition',
        'default_description': 'Valorisation communautaire',
        'default_icon': 'EmojiEvents',
        'default_color': '#fbbf24',
        'depth': 1,
        'path': '007.001',
        'parent_type': 'distinction_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Prix et honneurs (child of Distinction)
    {
        'template_type': 'prix',
        'default_name': 'Prix et honneurs',
        'default_name_en': 'Awards and Honors',
        'default_description': 'Prix et distinctions',
        'default_icon': 'WorkspacePremium',
        'default_color': '#fbbf24',
        'depth': 1,
        'path': '007.002',
        'parent_type': 'distinction_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Photos et Vidéos (parent)
    {
        'template_type': 'photos_videos_parent',
        'default_name': 'Photos et Vidéos',
        'default_name_en': 'Photos and Videos',
        'default_description': 'Contenu multimédia',
        'default_icon': 'PhotoCamera',
        'default_color': '#06b6d4',
        'depth': 0,
        'path': '008',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': False,
    },

    # Galerie photos (child of Photos et Vidéos)
    {
        'template_type': 'photographie',
        'default_name': 'Galerie photos',
        'default_name_en': 'Photo Gallery',
        'default_description': 'Images et captures',
        'default_icon': 'PhotoCamera',
        'default_color': '#06b6d4',
        'depth': 1,
        'path': '008.001',
        'parent_type': 'photos_videos_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Vidéos (child of Photos et Vidéos)
    {
        'template_type': 'videos',
        'default_name': 'Vidéos',
        'default_name_en': 'Videos',
        'default_description': 'Contenu vidéo',
        'default_icon': 'Videocam',
        'default_color': '#06b6d4',
        'depth': 1,
        'path': '008.002',
        'parent_type': 'photos_videos_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Participation Citoyenne (parent)
    {
        'template_type': 'participation_parent',
        'default_name': 'Participation Citoyenne',
        'default_name_en': 'Citizen Participation',
        'default_description': 'Engagement citoyen',
        'default_icon': 'HowToVote',
        'default_color': '#8b5cf6',
        'depth': 0,
        'path': '009',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': False,
    },

    # Consultations (child of Participation)
    {
        'template_type': 'consultations',
        'default_name': 'Consultations',
        'default_name_en': 'Consultations',
        'default_description': 'Consultations publiques',
        'default_icon': 'Forum',
        'default_color': '#8b5cf6',
        'depth': 1,
        'path': '009.001',
        'parent_type': 'participation_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Suggestions (child of Participation)
    {
        'template_type': 'suggestions',
        'default_name': 'Suggestions',
        'default_name_en': 'Suggestions',
        'default_description': 'Boîte à suggestions',
        'default_icon': 'Lightbulb',
        'default_color': '#8b5cf6',
        'depth': 1,
        'path': '009.002',
        'parent_type': 'participation_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },

    # Événements (child of Participation)
    {
        'template_type': 'evenements',
        'default_name': 'Événements',
        'default_name_en': 'Events',
        'default_description': 'Événements participatifs',
        'default_icon': 'Event',
        'default_color': '#8b5cf6',
        'depth': 1,
        'path': '009.003',
        'parent_type': 'participation_parent',
        'is_required': False,
        'allow_threads': True,
        'allow_direct_posts': True,
    },
]


def update_rubriques():
    """Update rubrique structure."""
    print("=" * 80)
    print("UPDATING RUBRIQUE STRUCTURE")
    print("=" * 80)

    # First pass: Create/update all parent rubriques (depth=0)
    print("\n1. Creating/Updating Parent Rubriques (depth=0)...")
    print("-" * 80)
    parent_mapping = {}

    for rubrique_data in NEW_RUBRIQUES:
        if rubrique_data['depth'] == 0:
            template_type = rubrique_data['template_type']

            try:
                rubrique = RubriqueTemplate.objects.get(
                    template_type=template_type
                )
                # Update existing
                for key, value in rubrique_data.items():
                    if key not in ['template_type', 'parent_type']:
                        setattr(rubrique, key, value)
                rubrique.parent = None
                rubrique.is_active = True
                rubrique.save()
                print(f"✓ Updated: {rubrique.default_name} ({template_type})")
            except RubriqueTemplate.DoesNotExist:
                # Create new
                rubrique = RubriqueTemplate.objects.create(
                    **{k: v for k, v in rubrique_data.items()
                       if k != 'parent_type'}
                )
                print(f"✓ Created: {rubrique.default_name} ({template_type})")

            parent_mapping[template_type] = rubrique

    # Second pass: Create/update all child rubriques (depth=1)
    print("\n2. Creating/Updating Child Rubriques (depth=1)...")
    print("-" * 80)

    for rubrique_data in NEW_RUBRIQUES:
        if rubrique_data['depth'] == 1:
            template_type = rubrique_data['template_type']
            parent_type = rubrique_data.get('parent_type')

            if parent_type and parent_type in parent_mapping:
                parent = parent_mapping[parent_type]

                try:
                    rubrique = RubriqueTemplate.objects.get(
                        template_type=template_type
                    )
                    # Update existing
                    for key, value in rubrique_data.items():
                        if key not in ['template_type', 'parent_type']:
                            setattr(rubrique, key, value)
                    rubrique.parent = parent
                    rubrique.is_active = True
                    rubrique.save()
                    print(f"✓ Updated: {rubrique.default_name} ({template_type}) → parent: {parent.default_name}")
                except RubriqueTemplate.DoesNotExist:
                    # Create new
                    data = {k: v for k, v in rubrique_data.items()
                            if k != 'parent_type'}
                    data['parent'] = parent
                    rubrique = RubriqueTemplate.objects.create(**data)
                    print(f"✓ Created: {rubrique.default_name} ({template_type}) → parent: {parent.default_name}")
            else:
                print(f"✗ Skipped: {template_type} (parent {parent_type} not found)")

    # Deactivate old rubriques that are not in new structure
    print("\n3. Deactivating Old Rubriques...")
    print("-" * 80)

    new_template_types = [r['template_type'] for r in NEW_RUBRIQUES]
    old_rubriques = RubriqueTemplate.objects.exclude(
        template_type__in=new_template_types
    ).filter(is_active=True)

    for old in old_rubriques:
        old.is_active = False
        old.save()
        print(f"✓ Deactivated: {old.default_name} ({old.template_type})")

    if not old_rubriques.exists():
        print("  No old rubriques to deactivate")

    # Update all communities with new rubriques
    print("\n4. Updating Communities...")
    print("-" * 80)

    all_active_rubriques = RubriqueTemplate.objects.filter(is_active=True)
    total_active = all_active_rubriques.count()

    for community in Community.objects.filter(is_deleted=False):
        # Enable all active rubriques for all communities
        community.enabled_rubriques = [
            str(r.id) for r in all_active_rubriques
        ]
        community.save()
        print(f"✓ {community.name}: {len(community.enabled_rubriques)} rubriques enabled")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Active Rubriques: {total_active}")
    print(f"  - Parent rubriques (depth=0): {all_active_rubriques.filter(depth=0).count()}")
    print(f"  - Child rubriques (depth=1): {all_active_rubriques.filter(depth=1).count()}")
    print(f"Communities Updated: {Community.objects.filter(is_deleted=False).count()}")

    print("\n" + "=" * 80)
    print("✅ RUBRIQUE STRUCTURE UPDATE COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    update_rubriques()
