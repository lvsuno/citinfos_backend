"""
Utility functions for the communities app.
"""
import logging
from django.db import transaction
from django.utils.text import slugify

logger = logging.getLogger(__name__)


def get_or_create_default_community(division, creator_profile=None):
    """
    Get or create a default community for a division.

    This is called automatically when:
    1. A new division is uploaded/created
    2. A user tries to post to a division that has no community yet

    Args:
        division: AdministrativeDivision instance
        creator_profile: UserProfile instance (optional, system user if None)

    Returns:
        Community instance
    """
    from .models import Community
    from accounts.models import UserProfile
    from django.contrib.auth import get_user_model

    User = get_user_model()

    # Check if default community already exists
    existing_community = Community.objects.filter(
        division=division,
        community_type='public',
        is_deleted=False
    ).first()

    if existing_community:
        logger.info(
            f"Default community already exists for division "
            f"{division.name}: {existing_community.slug}"
        )
        return existing_community

    # Get or create system user for auto-generated communities
    if creator_profile is None:
        system_user, _ = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@citinfos.com',
                'is_active': True,
            }
        )
        creator_profile, _ = UserProfile.objects.get_or_create(
            user=system_user,
            defaults={
                'display_name': 'System',
            }
        )

    # Create default community
    with transaction.atomic():
        community_name = f"{division.name}"

        # Create description based on division type
        description = (
            f"Welcome to the {division.name} community! "
            f"Connect with neighbors, share local news, and discuss "
            f"topics relevant to our {division.boundary_type}."
        )

        community = Community.objects.create(
            name=community_name,
            description=description,
            community_type='public',
            division=division,
            creator=creator_profile,
            allow_posts=True,
            require_post_approval=False,
            allow_external_links=True,
            is_active=True,
            is_featured=False,
        )

        logger.info(
            f"Created default community '{community.slug}' "
            f"for division {division.name}"
        )

        return community


def ensure_community_for_division(division_id):
    """
    Ensure a default community exists for a given division ID.

    This is a convenience wrapper that fetches the division
    and calls get_or_create_default_community.

    Args:
        division_id: UUID of the division

    Returns:
        Community instance or None if division doesn't exist
    """
    from core.models import AdministrativeDivision

    try:
        division = AdministrativeDivision.objects.get(id=division_id)
        return get_or_create_default_community(division)
    except AdministrativeDivision.DoesNotExist:
        logger.warning(f"Division with ID {division_id} does not exist")
        return None


def get_community_for_post(division_id=None, community_id=None):
    """
    Get the appropriate community for a post.

    Priority:
    1. If community_id provided, use that community
    2. If division_id provided, get/create default community for division
    3. Return None if neither provided

    Args:
        division_id: Optional UUID of the division
        community_id: Optional UUID of the community

    Returns:
        Community instance or None
    """
    from .models import Community

    # If community_id is provided, use it directly
    if community_id:
        try:
            return Community.objects.get(
                id=community_id,
                is_deleted=False
            )
        except Community.DoesNotExist:
            logger.warning(f"Community with ID {community_id} does not exist")
            return None

    # If division_id is provided, get or create default community
    if division_id:
        return ensure_community_for_division(division_id)

    return None
