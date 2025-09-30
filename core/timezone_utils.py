"""
Timezone utilities for handling timezone equivalency and validation.

This module provides functions to:
1. Detect equivalent timezones (e.g., America/Toronto vs Canada/Toronto)
2. Normalize timezone names for consistent comparison
3. Validate timezone restrictions to prevent conflicts
4. Generate timezone equivalency mappings

Used by community geo-restrictions to ensure users cannot allow and block
the same timezone using different timezone names.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Tuple

import pytz
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache key for timezone equivalency map
TIMEZONE_EQUIVALENCY_CACHE_KEY = 'timezone_equivalency_map'
CACHE_TIMEOUT = 3600 * 24  # 24 hours


def get_timezone_equivalency_map(
    use_cache: bool = True
) -> Dict[str, List[str]]:
    """
    Generate a mapping of equivalent timezones based on their UTC offsets
    and DST rules.

    Returns a dictionary where keys are representative timezone names
    and values are lists of equivalent timezone names.

    Args:
        use_cache: Whether to use cached results (default: True)

    Returns:
        Dict mapping representative timezone to list of equivalent timezones

    Example:
        {
            'America/New_York': [
                'America/New_York', 'US/Eastern', 'Canada/Eastern'
            ],
            'America/Chicago': [
                'America/Chicago', 'US/Central', 'Canada/Central'
            ],
            ...
        }
    """
    if use_cache:
        cached_map = cache.get(TIMEZONE_EQUIVALENCY_CACHE_KEY)
        if cached_map:
            return cached_map

    logger.info("Generating timezone equivalency map...")

    # Get all available timezones
    all_timezones = list(pytz.all_timezones)

    # Group timezones by their UTC offset patterns
    timezone_groups = defaultdict(list)

    # Test dates to check DST behavior (winter and summer)
    test_dates = [
        datetime(2024, 1, 15, 12, 0, 0),  # Winter
        datetime(2024, 7, 15, 12, 0, 0),  # Summer
    ]

    for tz_name in all_timezones:
        try:
            tz = pytz.timezone(tz_name)

            # Get UTC offsets for test dates
            offsets = []
            for test_date in test_dates:
                localized_dt = tz.localize(test_date)
                offset = localized_dt.utcoffset().total_seconds()
                offsets.append(offset)

            # Create a signature based on offset pattern
            signature = tuple(offsets)
            timezone_groups[signature].append(tz_name)

        except Exception as e:
            logger.warning(f"Error processing timezone {tz_name}: {e}")
            continue

    # Convert grouped timezones to equivalency map
    equivalency_map = {}

    for signature, tz_list in timezone_groups.items():
        if len(tz_list) > 1:  # Only include groups with multiple timezones
            # Sort to get consistent representative timezone
            tz_list.sort()

            # Use the first timezone as the representative
            representative = tz_list[0]
            equivalency_map[representative] = tz_list

    # Cache the result
    if use_cache:
        cache.set(
            TIMEZONE_EQUIVALENCY_CACHE_KEY, equivalency_map, CACHE_TIMEOUT
        )

    logger.info(
        f"Generated {len(equivalency_map)} timezone equivalency groups"
    )
    return equivalency_map


def normalize_timezone(timezone_name: str) -> str:
    """
    Normalize a timezone name to its representative form.

    This function maps equivalent timezone names to a single representative
    timezone to enable consistent comparison.

    Args:
        timezone_name: The timezone name to normalize

    Returns:
        The representative timezone name

    Raises:
        ValueError: If the timezone name is invalid

    Example:
        normalize_timezone('US/Eastern') -> 'America/New_York'
        normalize_timezone('Canada/Eastern') -> 'America/New_York'
    """
    if not timezone_name:
        raise ValueError("Timezone name cannot be empty")

    # Validate that the timezone exists
    try:
        pytz.timezone(timezone_name)
    except pytz.UnknownTimeZoneError:
        raise ValueError(f"Unknown timezone: {timezone_name}")

    # Get equivalency map
    equivalency_map = get_timezone_equivalency_map()

    # Find the group containing this timezone
    for representative, tz_list in equivalency_map.items():
        if timezone_name in tz_list:
            return representative

    # If not found in any group, return the original (it's unique)
    return timezone_name


def are_timezones_equivalent(tz1: str, tz2: str) -> bool:
    """
    Check if two timezone names represent the same timezone.

    Args:
        tz1: First timezone name
        tz2: Second timezone name

    Returns:
        True if the timezones are equivalent, False otherwise

    Raises:
        ValueError: If either timezone name is invalid

    Example:
        are_timezones_equivalent('US/Eastern', 'America/New_York') -> True
        are_timezones_equivalent('US/Eastern', 'US/Pacific') -> False
    """
    try:
        normalized_tz1 = normalize_timezone(tz1)
        normalized_tz2 = normalize_timezone(tz2)
        return normalized_tz1 == normalized_tz2
    except ValueError:
        # Re-raise with more context
        raise ValueError(f"Error comparing timezones '{tz1}' and '{tz2}'")


def validate_timezone_restrictions(
    allowed_timezones: List[str],
    blocked_timezones: List[str]
) -> List[Tuple[str, str]]:
    """
    Validate timezone restrictions to prevent conflicts.

    Checks if any allowed timezone is equivalent to any blocked timezone.
    This prevents users from allowing and blocking the same timezone
    using different timezone names.

    Args:
        allowed_timezones: List of allowed timezone names
        blocked_timezones: List of blocked timezone names

    Returns:
        List of conflicting timezone pairs (allowed, blocked)

    Raises:
        ValueError: If conflicts are found

    Example:
        allowed = ['US/Eastern']
        blocked = ['America/New_York']
        validate_timezone_restrictions(allowed, blocked)
        # Raises ValueError: Timezone conflicts detected
    """
    conflicts = []

    # Normalize all timezones for comparison
    try:
        normalized_allowed = {
            tz: normalize_timezone(tz) for tz in allowed_timezones
        }
        normalized_blocked = {
            tz: normalize_timezone(tz) for tz in blocked_timezones
        }
    except ValueError as e:
        raise ValueError(f"Invalid timezone in restrictions: {e}")

    # Check for conflicts
    for allowed_tz, normalized_allowed in normalized_allowed.items():
        for blocked_tz, normalized_blocked_tz in normalized_blocked.items():
            if normalized_allowed == normalized_blocked_tz:
                conflicts.append((allowed_tz, blocked_tz))

    if conflicts:
        conflict_descriptions = [
            f"'{allowed}' (allowed) conflicts with '{blocked}' (blocked)"
            for allowed, blocked in conflicts
        ]
        error_message = (
            f"Timezone conflicts detected: "
            f"{'; '.join(conflict_descriptions)}. "
            "The same timezone cannot be both allowed and blocked."
        )
        raise ValueError(error_message)

    return conflicts


def get_timezone_conflicts_for_restrictions(
    restrictions: List[Dict[str, Any]]
) -> List[str]:
    """
    Validate timezone restrictions from community geo-restriction data.

    This is the main validation function used by Django serializers
    to check for timezone conflicts in community geo-restrictions.

    Args:
        restrictions: List of restriction dictionaries from community data

    Returns:
        List of conflict error messages

    Example:
        restrictions = [
            {
                'restriction_type': 'timezone',
                'action': 'allow',
                'allowed_timezones': ['US/Eastern']
            },
            {
                'restriction_type': 'timezone',
                'action': 'block',
                'blocked_timezones': ['America/New_York']
            }
        ]
        get_timezone_conflicts_for_restrictions(restrictions)
        # Returns: ['Timezone conflicts detected: ...']
    """
    conflicts = []

    # Extract all timezone restrictions
    allowed_timezones = []
    blocked_timezones = []

    for restriction in restrictions:
        if restriction.get('restriction_type') != 'timezone':
            continue

        action = restriction.get('action')
        if action == 'allow':
            allowed_timezones.extend(
                restriction.get('allowed_timezones', [])
            )
        elif action == 'block':
            blocked_timezones.extend(
                restriction.get('blocked_timezones', [])
            )

    # Validate for conflicts
    if allowed_timezones and blocked_timezones:
        try:
            validate_timezone_restrictions(
                allowed_timezones, blocked_timezones
            )
        except ValueError as e:
            conflicts.append(str(e))

    return conflicts


# Commonly used timezone mappings for quick reference
COMMON_TIMEZONE_EQUIVALENTS = {
    'US/Eastern': 'America/New_York',
    'US/Central': 'America/Chicago',
    'US/Mountain': 'America/Denver',
    'US/Pacific': 'America/Los_Angeles',
    'Canada/Eastern': 'America/New_York',
    'Canada/Central': 'America/Chicago',
    'Canada/Mountain': 'America/Denver',
    'Canada/Pacific': 'America/Vancouver',
    'GMT': 'UTC',
}


def get_common_timezone_equivalent(timezone_name: str) -> str:
    """
    Get the common equivalent for well-known timezone names.

    This provides a faster lookup for commonly used timezone equivalents
    without needing to generate the full equivalency map.

    Args:
        timezone_name: The timezone name to look up

    Returns:
        The equivalent timezone name, or the original if no mapping exists
    """
    return COMMON_TIMEZONE_EQUIVALENTS.get(timezone_name, timezone_name)
