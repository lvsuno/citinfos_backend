"""
Async location processing tasks for user registration optimization.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

# Location processing without address parsing


@shared_task(bind=True, max_retries=3)
def process_user_location_async(self, profile_id: str, division_name: str = None, ip_address: str = None):
    """
    Process user location data asynchronously after registration.
    This assigns administrative division based on division name or IP address.
    """
    try:
        from accounts.models import UserProfile
        from core.utils import get_location_from_ip

        profile = UserProfile.objects.get(id=profile_id)
        division_obj = None

        # Process location data based on what was provided
        if division_name:
            division_obj = _find_division_by_name(division_name)
        elif ip_address:
            # Use full location lookup since this is async
            location = get_location_from_ip(ip_address)
            if location:
                division_name = location.get('city')  # API returns 'city' key
                division_obj = _find_division_by_name(division_name)

        # Update profile with location data
        if division_obj:
            profile.administrative_division = division_obj
            profile.save(update_fields=['administrative_division'])

        return {
            'success': True,
            'profile_id': profile_id,
            'division': division_obj.name if division_obj else None
        }

    except Exception as exc:
        logger.error(f"Location processing failed for profile {profile_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


def _find_division_by_name(division_name):
    """
    Helper function to find existing AdministrativeDivision by name.

    Returns division_obj or None
    """
    from core.models import AdministrativeDivision

    if not division_name:
        return None

    division_name = division_name.strip()
    try:
        division_obj = AdministrativeDivision.objects.filter(
            name__iexact=division_name
        ).first()

        if division_obj:
            logger.info(f"Found administrative division: {division_name}")
        else:
            logger.warning(f"Administrative division '{division_name}' not found in database")

        return division_obj
    except Exception as e:
        logger.error(f"Error finding division '{division_name}': {e}")
        return None
