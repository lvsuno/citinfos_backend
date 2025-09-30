"""
Timezone-based access control utilities for community restrictions.

This module provides server-side functions to:
1. Get user's actual timezone from session data (captured at login)
2. Validate timezone-based community access with priority handling
3. Check if user can access during specific timezone hours
4. Handle timezone conflicts with proper precedence rules
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from django.utils import timezone as django_timezone

import pytz
from core.session_manager import session_manager
from core.timezone_utils import are_timezones_equivalent

logger = logging.getLogger(__name__)


def get_user_timezone_from_session(request) -> Optional[str]:
    """
    Get user's actual timezone from session data.

    Priority:
    1. User-provided timezone from browser/device (session data)
    2. User profile timezone setting
    3. IP-detected timezone (fallback)

    Args:
        request: Django request object

    Returns:
        User's timezone string or None if not available
    """
    if not hasattr(request, 'session') or not request.session.session_key:
        return None

    try:
        # Get session data with timezone information
        session_data = session_manager.get_session(request.session.session_key)
        if not session_data:
            return None

        location_data = session_data.get('location_data', {})
        if not location_data:
            return None

        # Priority 1: User's actual timezone from browser/device
        user_timezone = location_data.get('user_timezone')
        if user_timezone:
            return user_timezone

        # Priority 2: User profile timezone (if available)
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_profile = getattr(request.user, 'profile', None)
            if user_profile and hasattr(user_profile, 'timezone'):
                profile_timezone = user_profile.timezone
                if profile_timezone and profile_timezone != 'UTC':
                    return profile_timezone

        # Priority 3: IP-detected timezone (fallback)
        detected_timezone = location_data.get('detected_timezone')
        if detected_timezone:
            return detected_timezone

        return None

    except Exception as e:
        logger.debug(f"Failed to get user timezone from session: {e}")
        return None


def check_timezone_based_access(
    user_timezone: str,
    allowed_timezones: List[str],
    blocked_timezones: List[str]
) -> Tuple[bool, Optional[str]]:
    """
    Check if user can access based on timezone restrictions.

    Rules:
    1. If both allowed and blocked timezones are specified, allowed takes
       priority
    2. If user timezone is in blocked list and NOT in allowed list, deny
       access
    3. If user timezone is in allowed list, grant access regardless of
       blocked list
    4. Uses timezone equivalency detection to prevent circumvention

    Args:
        user_timezone: User's actual timezone
        allowed_timezones: List of allowed timezone names
        blocked_timezones: List of blocked timezone names

    Returns:
        Tuple of (is_allowed, error_message)
    """
    if not user_timezone:
        return False, "Unable to determine user timezone for access control"

    try:
        # Check allowed timezones first (higher priority)
        if allowed_timezones:
            for allowed_tz in allowed_timezones:
                if are_timezones_equivalent(user_timezone, allowed_tz):
                    return True, None  # Access granted by allowed list

            # User timezone not in allowed list - access denied
            return False, (
                f"Access restricted to specific timezones. "
                f"Your timezone ({user_timezone}) is not in the allowed list."
            )

        # Check blocked timezones (only if no allowed list)
        if blocked_timezones:
            for blocked_tz in blocked_timezones:
                if are_timezones_equivalent(user_timezone, blocked_tz):
                    return False, (
                        f"Access denied. Your timezone ({user_timezone}) "
                        f"is blocked for this community."
                    )

        # No restrictions apply - access granted
        return True, None

    except Exception as e:
        logger.error(f"Timezone access check failed: {e}")
        return False, f"Timezone validation error: {e}"


def check_timezone_hours_access(
    user_timezone: str,
    allowed_hours: Optional[Dict[str, Any]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Check if user can access during their local timezone hours.

    This enables communities to restrict access to certain hours in the
    user's local timezone (e.g., business hours only).

    Args:
        user_timezone: User's actual timezone
        allowed_hours: Dict with 'start_hour', 'end_hour', 'days' restrictions
                      Example: {'start_hour': 9, 'end_hour': 17,
                               'days': [0,1,2,3,4]}    Returns:
        Tuple of (is_allowed, error_message)
    """
    if not allowed_hours:
        return True, None  # No hour restrictions

    if not user_timezone:
        return False, "Unable to determine user timezone for hour-based access"

    try:
        # Get current time in user's timezone
        user_tz = pytz.timezone(user_timezone)
        current_time = django_timezone.now().astimezone(user_tz)

        # Check day restrictions
        # Default: all days
        allowed_days = allowed_hours.get('days', list(range(7)))
        if current_time.weekday() not in allowed_days:
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                         'Friday', 'Saturday', 'Sunday']
            allowed_day_names = [day_names[day] for day in allowed_days]
            return False, (
                f"Access restricted to specific days. "
                f"Currently {day_names[current_time.weekday()]}, "
                f"but access is only allowed on: "
                f"{', '.join(allowed_day_names)}"
            )        # Check hour restrictions
        start_hour = allowed_hours.get('start_hour', 0)
        end_hour = allowed_hours.get('end_hour', 24)

        current_hour = current_time.hour

        if start_hour <= end_hour:
            # Normal hours (e.g., 9 AM to 5 PM)
            is_allowed = start_hour <= current_hour < end_hour
        else:
            # Overnight hours (e.g., 10 PM to 6 AM)
            is_allowed = current_hour >= start_hour or current_hour < end_hour

        if not is_allowed:
            return False, (
                f"Access restricted to specific hours in your timezone. "
                f"Currently {current_time.strftime('%I:%M %p')} "
                f"({user_timezone}), but access is only allowed "
                f"between {start_hour:02d}:00 and {end_hour:02d}:00."
            )

        return True, None

    except pytz.UnknownTimeZoneError:
        return False, f"Invalid user timezone: {user_timezone}"
    except Exception as e:
        logger.error(f"Timezone hours access check failed: {e}")
        return False, f"Timezone hours validation error: {e}"


def validate_community_timezone_access(
    request,
    community,
    check_hours: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive timezone-based access validation for communities.

    This is the main function used by middleware and views to check
    if a user can access a community based on timezone restrictions.

    Args:
        request: Django request object
        community: Community instance
        check_hours: Whether to check hour-based restrictions

    Returns:
        Tuple of (is_allowed, error_message)
    """
    # Skip if no timezone-based restrictions
    if not getattr(community, 'is_geo_restricted', False):
        return True, None

    if getattr(community, 'geo_restriction_type', None) != 'timezone_based':
        return True, None

    # Get user's timezone from session
    user_timezone = get_user_timezone_from_session(request)
    if not user_timezone:
        return False, (
            "Timezone-based access control requires timezone detection. "
            "Please ensure your browser allows timezone detection."
        )

    # Get timezone restrictions from community
    timezone_restrictions = community.geo_restrictions.filter(
        restriction_type__in=['allow_timezone', 'block_timezone'],
        is_active=True
    )

    if not timezone_restrictions.exists():
        return True, None  # No restrictions configured

    # Collect allowed and blocked timezones
    allowed_timezones = []
    blocked_timezones = []
    hour_restrictions = None

    for restriction in timezone_restrictions:
        timezone_list = restriction.timezone_list or []

        if restriction.restriction_type == 'allow_timezone':
            allowed_timezones.extend(timezone_list)
            # Check for hour restrictions in the restriction notes or config
            if hasattr(restriction, 'hour_restrictions'):
                hour_restrictions = restriction.hour_restrictions

        elif restriction.restriction_type == 'block_timezone':
            blocked_timezones.extend(timezone_list)

    # Check timezone-based access
    timezone_allowed, timezone_error = check_timezone_based_access(
        user_timezone, allowed_timezones, blocked_timezones
    )

    if not timezone_allowed:
        return False, timezone_error

    # Check hour-based access if enabled and configured
    if check_hours and hour_restrictions:
        hours_allowed, hours_error = check_timezone_hours_access(
            user_timezone, hour_restrictions
        )

        if not hours_allowed:
            return False, hours_error

    return True, None


def get_user_current_time_info(request) -> Optional[Dict[str, Any]]:
    """
    Get user's current time information for debugging/display purposes.

    Args:
        request: Django request object

    Returns:
        Dict with user's timezone and current time information
    """
    user_timezone = get_user_timezone_from_session(request)
    if not user_timezone:
        return None

    try:
        user_tz = pytz.timezone(user_timezone)
        current_time = django_timezone.now().astimezone(user_tz)

        return {
            'timezone': user_timezone,
            'current_time': current_time.isoformat(),
            'formatted_time': current_time.strftime('%Y-%m-%d %I:%M:%S %p'),
            'weekday': current_time.weekday(),
            'weekday_name': current_time.strftime('%A'),
            'hour': current_time.hour,
        }

    except Exception as e:
        logger.debug(f"Failed to get user time info: {e}")
        return None
