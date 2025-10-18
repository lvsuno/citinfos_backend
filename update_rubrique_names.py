"""
Update rubrique names to match new frontend structure.

This script updates the default_name for existing rubriques to align with
the new frontend naming conventions.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from communities.models import RubriqueTemplate

# Mapping from template_type to new names
NAME_UPDATES = {
    # Accueil remains the same
    'accueil': {
        'default_name': 'Accueil',
        'default_name_en': 'Home',
    },

    # Nouvelles section
    'actualites': {
        'default_name': 'Actualités',
        'default_name_en': 'News',
    },

    # Services section
    'transport': {
        'default_name': 'Transport',
        'default_name_en': 'Transportation',
    },
    'commerces': {
        'default_name': 'Commerces',
        'default_name_en': 'Businesses',
    },

    # Culture section
    'culture': {
        'default_name': 'Événements culturels',
        'default_name_en': 'Cultural Events',
    },
    'litterature': {
        'default_name': 'Littérature',
        'default_name_en': 'Literature',
    },
    'poesie': {
        'default_name': 'Poésie',
        'default_name_en': 'Poetry',
    },
    'histoire': {
        'default_name': 'Histoire',
        'default_name_en': 'History',
    },

    # Art section
    'art': {
        'default_name': 'Créations artistiques',
        'default_name_en': 'Artistic Creations',
    },

    # Sports section
    'sport': {
        'default_name': 'Activités sportives',
        'default_name_en': 'Sports Activities',
    },
    'sport_hockey': {
        'default_name': 'Hockey',
        'default_name_en': 'Hockey',
    },
    'sport_soccer': {
        'default_name': 'Soccer',
        'default_name_en': 'Soccer',
    },

    # Distinction section
    'reconnaissance': {
        'default_name': 'Reconnaissances',
        'default_name_en': 'Recognition',
    },

    # Photos et Vidéos section
    'photographie': {
        'default_name': 'Galerie photos',
        'default_name_en': 'Photo Gallery',
    },

    # Participation Citoyenne section
    'evenements': {
        'default_name': 'Événements',
        'default_name_en': 'Events',
    },
    'evenements_concerts': {
        'default_name': 'Concerts',
        'default_name_en': 'Concerts',
    },
    'evenements_festivals': {
        'default_name': 'Festivals',
        'default_name_en': 'Festivals',
    },

    # Chronologie
    'chronologie': {
        'default_name': 'Chronologie',
        'default_name_en': 'Timeline',
    },
}

def update_rubrique_names():
    """Update rubrique names in database."""
    print("=" * 80)
    print("UPDATING RUBRIQUE NAMES TO MATCH FRONTEND STRUCTURE")
    print("=" * 80)

    updated_count = 0
    not_found_count = 0

    for template_type, names in NAME_UPDATES.items():
        try:
            rubrique = RubriqueTemplate.objects.get(
                template_type=template_type,
                is_active=True
            )

            old_name = rubrique.default_name
            new_name = names['default_name']

            # Update the names
            rubrique.default_name = new_name
            rubrique.default_name_en = names['default_name_en']
            rubrique.save()

            if old_name != new_name:
                print(f"✓ {template_type:25} | {old_name:30} → {new_name}")
                updated_count += 1
            else:
                print(f"- {template_type:25} | {new_name:30} (unchanged)")

        except RubriqueTemplate.DoesNotExist:
            print(f"✗ {template_type:25} | NOT FOUND")
            not_found_count += 1

    print("\n" + "=" * 80)
    print(f"Updated: {updated_count} rubriques")
    print(f"Unchanged: {len(NAME_UPDATES) - updated_count - not_found_count}")
    print(f"Not found: {not_found_count}")
    print("=" * 80)

    # Display updated structure
    print("\n" + "=" * 80)
    print("CURRENT RUBRIQUE STRUCTURE:")
    print("=" * 80)

    rubriques = RubriqueTemplate.objects.filter(
        is_active=True
    ).order_by('path')

    for r in rubriques:
        depth_indicator = "  " * r.depth + ("└─ " if r.depth > 0 else "• ")
        print(f"{depth_indicator}{r.default_name:35} ({r.template_type})")

    print(f"\nTotal: {rubriques.count()} active rubriques")

if __name__ == '__main__':
    update_rubrique_names()
    print("\n✅ Rubrique names updated successfully!")
