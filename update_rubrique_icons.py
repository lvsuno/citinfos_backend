"""
Update rubrique icons to match Material-UI icon names.
Maps current icon names to the exact MUI component names used in the frontend.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from communities.models import RubriqueTemplate
from django.db import transaction


# Icon mapping from current names to MUI component names
# Based on the frontend imports:
# Home, Newspaper, RoomService, TheaterComedy, Business, Palette, Sports,
# EmojiEvents, PhotoCamera, HowToVote
ICON_MAPPING = {
    # Parent sections - match frontend imports exactly
    'Home': 'Home',  # Already correct
    'Article': 'Newspaper',  # Nouvelles
    'HomeRepairService': 'RoomService',  # Services
    'TheaterComedy': 'TheaterComedy',  # Already correct
    'TrendingUp': 'Business',  # Économie (use Business icon)
    'Palette': 'Palette',  # Already correct
    'FitnessCenter': 'Sports',  # Sports
    'Stars': 'EmojiEvents',  # Distinction (use EmojiEvents)
    'PermMedia': 'PhotoCamera',  # Photos et Vidéos
    'HowToVote': 'HowToVote',  # Already correct

    # Child icons - keep as is or map to simpler MUI icons
    'FiberNew': 'FiberNew',
    'Campaign': 'Campaign',
    'AccountBalance': 'AccountBalance',
    'DirectionsBus': 'DirectionsBus',
    'Storefront': 'Storefront',
    'Event': 'Event',
    'MenuBook': 'MenuBook',
    'AutoStories': 'AutoStories',
    'HistoryEdu': 'HistoryEdu',
    'Business': 'Business',
    'WorkOutline': 'WorkOutline',
    'Brush': 'Brush',
    'Museum': 'Museum',
    'DirectionsRun': 'DirectionsRun',
    'EmojiEvents': 'EmojiEvents',
    'CardGiftcard': 'CardGiftcard',
    'MilitaryTech': 'MilitaryTech',
    'PhotoLibrary': 'PhotoLibrary',
    'VideoLibrary': 'VideoLibrary',
    'QuestionAnswer': 'QuestionAnswer',
    'Lightbulb': 'Lightbulb',
    'CalendarToday': 'CalendarToday',
}


@transaction.atomic
def update_icons():
    """Update rubrique icons to match MUI component names."""
    print("=" * 80)
    print("UPDATING RUBRIQUE ICONS TO MATCH MUI IMPORTS")
    print("=" * 80)

    rubriques = RubriqueTemplate.objects.filter(is_active=True).order_by('path')
    updated_count = 0

    for rubrique in rubriques:
        old_icon = rubrique.default_icon

        if old_icon in ICON_MAPPING:
            new_icon = ICON_MAPPING[old_icon]

            if old_icon != new_icon:
                rubrique.default_icon = new_icon
                rubrique.save()

                depth_indicator = "  " * rubrique.depth + ("└─ " if rubrique.depth > 0 else "• ")
                print(f"{depth_indicator}{rubrique.default_name:40} | {old_icon:20} → {new_icon}")
                updated_count += 1
            else:
                depth_indicator = "  " * rubrique.depth + ("└─ " if rubrique.depth > 0 else "• ")
                print(f"{depth_indicator}{rubrique.default_name:40} | {old_icon:20} (no change)")
        else:
            depth_indicator = "  " * rubrique.depth + ("└─ " if rubrique.depth > 0 else "• ")
            print(f"⚠️  {depth_indicator}{rubrique.default_name:40} | {old_icon:20} (NOT MAPPED)")

    print(f"\n✅ Updated {updated_count} rubrique icons")

    # Display final state
    print("\n" + "=" * 80)
    print("FINAL ICON STATE:")
    print("=" * 80)

    rubriques = RubriqueTemplate.objects.filter(is_active=True).order_by('path')
    for r in rubriques:
        depth_indicator = "  " * r.depth + ("└─ " if r.depth > 0 else "• ")
        print(f"{depth_indicator}{r.default_name:40} | {r.default_icon}")


if __name__ == '__main__':
    update_icons()
    print("\n✅ Icon update complete!")
