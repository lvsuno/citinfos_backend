"""
WebSocket URL registry for ASGI.

Apps can expose a `websocket_urlpatterns` attribute in their `routing.py` and
this module will collect them so `asgi.py` can import a single source.
"""

import importlib
import logging
from typing import Any, List

from django.conf import settings

logger = logging.getLogger(__name__)


def get_websocket_urlpatterns() -> List[Any]:
    """Collect websocket_urlpatterns from apps that expose them.

    Returns a list suitable for `URLRouter`.
    """
    patterns = []

    # Always include notifications routing as base
    try:
        notifications = importlib.import_module('notifications.routing')
        patterns.extend(getattr(notifications, 'websocket_urlpatterns', []))
    except ModuleNotFoundError:
        # Notifications app not available - skip
        logger.debug('notifications.routing not found; skipping')
    except ImportError as e:
        logger.warning('Failed to import notifications.routing: %s', e)

    # Check for optional app-level routing modules listed in settings
    extra_apps = getattr(settings, 'WEBSOCKET_APPS', ['communities'])
    for app in extra_apps:
        mod_path = f"{app}.routing"
        try:
            mod = importlib.import_module(mod_path)
            app_patterns = getattr(mod, 'websocket_urlpatterns', [])
            if app_patterns:
                patterns.extend(app_patterns)
        except ModuleNotFoundError:
            # app does not provide routing — skip quietly
            logger.debug('%s.routing not found; skipping', app)
        except ImportError as e:
            logger.warning('Error importing %s: %s', app, e)

    return patterns
