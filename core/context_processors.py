"""Context processors for making settings available in templates."""
from django.conf import settings


def domain_settings(request):
    """Make domain settings available in all templates."""
    return {
        'DOMAIN_URL': settings.DOMAIN_URL,
        'LOGO_URL': f"{settings.DOMAIN_URL}/static/images/homey-logo.png",
    }
