"""
High-performance location detection service with Redis caching.
This module provides fast location lookups with async fallback for cache misses.
"""

from django.core.cache import cache
from django.conf import settings
from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger('core.location_cache')


class FastLocationService:
    """
    High-performance location detection with caching and async fallback.
    Prioritizes speed over completeness for user experience optimization.
    """

    # Cache settings
    LOCATION_CACHE_TIMEOUT = 3600 * 24 * 7  # 1 week
    SESSION_CACHE_TIMEOUT = 3600 * 4  # 4 hours (session duration)

    @classmethod
    def get_location_fast(cls, ip_address: str) -> Dict[str, Any]:
        """
        Get location data with Redis caching and async fallback.
        Returns cached data immediately or empty dict with background population.

        Args:
            ip_address: IP address to lookup

        Returns:
            Location data dictionary (may be empty if cache miss)
        """
        if not ip_address:
            return {}

        # Try Redis cache first (1-5ms response time)
        cache_key = f"location:{ip_address}"
        cached_location = cache.get(cache_key)

        if cached_location:
            logger.debug(f"Location cache hit for {ip_address}")
            try:
                if isinstance(cached_location, str):
                    return json.loads(cached_location)
                return cached_location
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid cached location data for {ip_address}")
                cache.delete(cache_key)

        # Cache miss - populate asynchronously and return empty for now
        logger.debug(f"Location cache miss for {ip_address}")
        cls._populate_location_cache_async(ip_address)

        return {}  # Empty location, will be populated on next request

    @classmethod
    def get_location_blocking(cls, ip_address: str) -> Dict[str, Any]:
        """
        Get location data with blocking lookup if not cached.
        Use only when location data is critical and waiting is acceptable.

        Args:
            ip_address: IP address to lookup

        Returns:
            Location data dictionary
        """
        if not ip_address:
            return {}

        # Try cache first
        cached_location = cls.get_location_fast(ip_address)
        if cached_location:
            return cached_location

        # Perform blocking lookup
        from core.utils import get_location_from_ip
        location_data = get_location_from_ip(ip_address)

        # Cache the result
        if location_data:
            cls._cache_location_data(ip_address, location_data)

        return location_data

    @classmethod
    def _populate_location_cache_async(cls, ip_address: str):
        """
        Synchronous fallback for location cache population.
        """
        try:
            from core.utils import get_location_from_ip
            location_data = get_location_from_ip(ip_address)
            if location_data:
                cls._cache_location_data(ip_address, location_data)
        except Exception as exc:
            logger.error(f"Failed to populate location cache for {ip_address}: {exc}")

    @classmethod
    def _cache_location_data(cls, ip_address: str, location_data: Dict[str, Any]):
        """
        Cache location data with proper serialization.
        """
        try:
            cache_key = f"location:{ip_address}"

            # Ensure data is JSON serializable
            serializable_data = {}
            for key, value in location_data.items():
                if value is not None:
                    serializable_data[key] = str(value) if not isinstance(value, (str, int, float, bool)) else value

            # Cache with long timeout (1 week)
            cache.set(cache_key, serializable_data, cls.LOCATION_CACHE_TIMEOUT)

            logger.info(f"Cached location data for {ip_address}: {list(serializable_data.keys())}")

        except Exception as exc:
            logger.error(f"Failed to cache location data for {ip_address}: {exc}")

    @classmethod
    def preload_session_location_cache(cls, session_id: str, location_data: Dict[str, Any]):
        """
        Preload location data for a session to enable fast subsequent lookups.

        Args:
            session_id: Session identifier
            location_data: Location data to cache
        """
        try:
            session_cache_key = f"session_location:{session_id}"

            # Ensure data is serializable
            serializable_data = {}
            for key, value in location_data.items():
                if value is not None:
                    serializable_data[key] = str(value) if not isinstance(value, (str, int, float, bool)) else value

            # Cache with session timeout (4 hours)
            cache.set(session_cache_key, serializable_data, cls.SESSION_CACHE_TIMEOUT)

            logger.debug(f"Preloaded session location cache for {session_id}")

        except Exception as exc:
            logger.error(f"Failed to preload session location cache: {exc}")

    @classmethod
    def get_session_location(cls, session_id: str) -> Dict[str, Any]:
        """
        Get cached location data for a specific session.

        Args:
            session_id: Session identifier

        Returns:
            Cached location data or empty dict
        """
        try:
            session_cache_key = f"session_location:{session_id}"
            cached_data = cache.get(session_cache_key)

            if cached_data:
                logger.debug(f"Session location cache hit for {session_id}")
                return cached_data if isinstance(cached_data, dict) else {}

        except Exception as exc:
            logger.error(f"Failed to get session location cache: {exc}")

        return {}

    @classmethod
    def extend_cache_timeout(cls, session_id: str, location_data: Dict[str, Any]):
        """
        Extend cache timeout for active session location data.

        Args:
            session_id: Session identifier
            location_data: Current location data
        """
        try:
            session_cache_key = f"session_location:{session_id}"

            # Re-cache with fresh timeout
            cache.set(session_cache_key, location_data, cls.SESSION_CACHE_TIMEOUT)

            logger.debug(f"Extended session location cache timeout for {session_id}")

        except Exception as exc:
            logger.error(f"Failed to extend session location cache: {exc}")

    @classmethod
    def warm_up_common_locations(cls, ip_addresses: list):
        """
        Pre-populate cache with common IP addresses to improve hit rate.
        Useful for warming up cache with frequently seen IPs.

        Args:
            ip_addresses: List of IP addresses to warm up
        """
        logger.info(f"Warming up location cache for {len(ip_addresses)} IPs")

        for ip_address in ip_addresses:
            # Check if already cached
            cache_key = f"location:{ip_address}"
            if not cache.get(cache_key):
                # Trigger async population
                cls._populate_location_cache_async(ip_address)

    @classmethod
    def clear_location_cache(cls, ip_address: Optional[str] = None):
        """
        Clear location cache for specific IP or all location data.

        Args:
            ip_address: Specific IP to clear, or None to clear all
        """
        try:
            if ip_address:
                cache_key = f"location:{ip_address}"
                cache.delete(cache_key)
                logger.info(f"Cleared location cache for {ip_address}")
            else:
                # Clear all location cache entries
                # Note: Pattern deletion is Redis-specific and may not work with all backends
                try:
                    # Try pattern deletion if supported (django-redis backend)
                    if hasattr(cache, 'delete_pattern'):
                        cache.delete_pattern("location:*")
                        cache.delete_pattern("session_location:*")
                        logger.info("Cleared all location cache entries with patterns")
                    else:
                        # Fallback: Log warning about manual tracking needed
                        logger.warning(
                            "Pattern deletion not supported. Consider tracking "
                            "cache keys for manual deletion."
                        )
                except AttributeError:
                    logger.warning(
                        "Cache backend doesn't support pattern deletion. "
                        "Individual keys must be tracked and deleted manually."
                    )

        except Exception as exc:
            logger.error(f"Failed to clear location cache: {exc}")


# Create global instance for easy importing
fast_location_service = FastLocationService()
