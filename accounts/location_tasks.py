"""
Async location processing tasks for user registration optimization.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

# Try to use libpostal's parse_address when available, otherwise provide a minimal fallback.
try:
    from postal.parser import parse_address as _postal_parse_address  # type: ignore
    _POSTAL_AVAILABLE = True
    def _parse_address(address):
        """Return a dict mapping libpostal label->value.

        libpostal returns a list of (value, label) tuples, e.g.
        [("5", "house_number"), ("rue sainte-anne", "road"), ...].
        This wrapper produces {'house_number': '5', 'road': 'rue sainte-anne', ...}.
        """
        parts = _postal_parse_address(address or '')
        result = {}
        for value, label in parts:
            if label in result:
                # join repeated labels (e.g., multiple road tokens)
                result[label] = f"{result[label]} {value}"
            else:
                result[label] = value
        return result
except Exception:
    _POSTAL_AVAILABLE = False
    def _parse_address(address):
        return {'address': address}


@shared_task(bind=True, max_retries=3)
def process_user_location_async(self, profile_id: str, country_name: str = None,
                               city_name: str = None, address: str = None,
                               ip_address: str = None):
    """
    Process user location data asynchronously after registration.
    This includes country/city creation and IP-based location detection.
    """
    try:
        from accounts.models import UserProfile
        from core.models import Country
        from core.utils import get_location_from_ip
        # Use postal parser fallback defined at module level
        parse_address = _parse_address

        profile = UserProfile.objects.get(id=profile_id)

        country_obj = None
        city_obj = None

        # Process location data based on what was provided
        if country_name or city_name:
            country_obj, city_obj = _get_or_create_country_city(country_name, city_name)
        elif address:
            # If parse_address is available use it, otherwise run a light-weight
            # fallback that extracts country/city by splitting the address.
            if _POSTAL_AVAILABLE:
                try:
                    # _parse_address returns a dict of token->value (see module-level wrapper)
                    parsed = _parse_address(address)
                    city_guess = parsed.get('city') # or parsed.get('city_district') or parsed.get('suburb')
                    # libpostal sometimes returns province/state but not country; handle that below
                    country_guess = parsed.get('country') # or parsed.get('state') or parsed.get('province')
                except Exception:
                    city_guess = None
                    country_guess = None
            else:
                # Fallback: attempt to extract country and city from the end
                # of the address string (common formats: '..., City, Country').
                try:
                    parts = [p.strip() for p in (address or '').split(',') if p.strip()]
                    country_guess = parts[-1] if len(parts) >= 1 else None
                    city_guess = parts[-2] if len(parts) >= 2 else None
                except Exception:
                    country_guess = None
                    city_guess = None

            # Normalize and map common province codes to country when needed
            if country_guess:
                # libpostal may return 'qc' or 'QC' for Quebec; normalize
                cg = (country_guess or '').strip()
                # common province codes that imply Canada
                if len(cg) <= 3 and cg.lower() in {'qc', 'on', 'bc', 'ab', 'mb', 'nb', 'nl', 'ns', 'pe', 'sk', 'yt', 'nt', 'nu'}:
                    country_guess = 'Canada'
                else:
                    country_guess = cg

            country_obj, city_obj = _get_or_create_country_city(country_guess, city_guess)
        elif ip_address:
            # Use full location lookup since this is async
            location = get_location_from_ip(ip_address)
            if location:
                country_name = location.get('country')
                city_name = location.get('city')
                country_obj, city_obj = _get_or_create_country_city(country_name, city_name)

        # Update profile with location data
        if country_obj or city_obj:
            update_fields = []
            if country_obj:
                profile.country = country_obj
                update_fields.append('country')
            if city_obj:
                profile.city = city_obj
                update_fields.append('city')

            profile.save(update_fields=update_fields)


        return {
            'success': True,
            'profile_id': profile_id,
            'country': country_obj.name if country_obj else None,
            'city': city_obj.name if city_obj else None
        }

    except Exception as exc:
        logger.error(f"Location processing failed for profile {profile_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


def _get_or_create_country_city(country_name, city_name):
    """
    Helper function to get or create Country and City objects.
    Returns (country_obj, city_obj)
    """
    from core.models import Country

    country_obj = None
    city_obj = None

    if country_name:
        # Normalize country name (title case)
        country_name = country_name.strip().title()
        country_obj, _ = Country.objects.get_or_create(
            name__iexact=country_name,
            defaults={'name': country_name}
        )

    if city_name:
        # Normalize city name (title case)
        city_name = city_name.strip().title()
        if country_obj:
            city_obj, _ = City.objects.get_or_create(
                name__iexact=city_name,
                country=country_obj,
                defaults={'name': city_name, 'country': country_obj}
            )
        else:
            city_obj = City.objects.filter(name__iexact=city_name).first()
            if not city_obj:
                city_obj = City.objects.create(name=city_name)

    return country_obj, city_obj
