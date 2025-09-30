import redis
import logging
import pickle
import zlib  # For compression
from django.conf import settings
from django.core.cache import cache
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Constants
SESSION_DURATION_HOURS = 4  # From session settings
LOCATION_CACHE_TIMEOUT = SESSION_DURATION_HOURS * 3600  # Use session duration


class LocationCacheService:
    """
    Location caching service with Redis primary and Django cache fallback.
    Optimized with connection pooling and reduced serialization overhead.
    """
    # Class-level Redis connection pool for better performance
    _redis_pool = None
    _redis_client = None

    def __init__(self):
        """Initialize service with optimized Redis connection."""
        self.use_redis = getattr(settings, 'USE_REDIS_CACHE', True)

        if self.use_redis:
            # Initialize Redis connection pool once at class level
            if LocationCacheService._redis_pool is None:
                try:
                    LocationCacheService._redis_pool = redis.ConnectionPool(
                        host=getattr(settings, 'REDIS_HOST', 'redis'),
                        port=getattr(settings, 'REDIS_PORT', 6379),
                        db=getattr(settings, 'REDIS_DB', 0),
                        password=getattr(settings, 'REDIS_PASSWORD', None),
                        decode_responses=False,  # Keep binary for pickle
                        max_connections=50,  # Increased pool size
                        retry_on_timeout=True,
                        socket_connect_timeout=0.5,  # Faster connection
                        socket_timeout=0.5,  # Faster individual operations
                        socket_keepalive=True,  # Keep connections alive
                        health_check_interval=30,  # Check connection health
                    )
                    LocationCacheService._redis_client = redis.Redis(
                        connection_pool=LocationCacheService._redis_pool
                    )
                    # Test connection
                    LocationCacheService._redis_client.ping()
                    logger.debug("Redis connection pool initialized successfully")
                except Exception as e:
                    logger.warning(f"Redis connection failed: {e}")
                    self.use_redis = False

            self.redis_client = LocationCacheService._redis_client

    def _get_from_cache(self, cache_key: str) -> Any:
        """Get data from cache (Django first for speed, Redis as backup)."""
        # Try Django cache first (fastest access)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        # If not in Django cache, try Redis (distributed/persistent cache)
        if self.use_redis:
            try:
                redis_data = self.redis_client.get(cache_key)
                if redis_data is not None:
                    if redis_data == b'false':
                        result = False  # Negative result
                    elif redis_data.startswith(b'ZLIB:'):
                        # Decompress and unpickle
                        compressed_data = redis_data[5:]  # Remove 'ZLIB:' prefix
                        decompressed = zlib.decompress(compressed_data)
                        result = pickle.loads(decompressed)
                    else:
                        # Standard pickle deserialization
                        result = pickle.loads(redis_data)

                    # Store in Django cache for faster next access
                    cache.set(cache_key, result, LOCATION_CACHE_TIMEOUT)
                    return result
            except Exception as e:
                logger.debug(f"Redis get failed for {cache_key}: {e}")

        # Not found in either cache
        return None

    def _set_in_cache(self, cache_key: str, value: Any,
                      timeout: int = LOCATION_CACHE_TIMEOUT):
        """Set data in both caches - Django for speed, Redis for distribution."""
        # Always store in Django cache first (fastest for immediate access)
        cache.set(cache_key, value, timeout)

        # Also store in Redis for distributed access and persistence
        if self.use_redis:
            try:
                if value is False:
                    # Store negative results as binary 'false'
                    self.redis_client.setex(cache_key, timeout, b'false')
                else:
                    # Optimized pickle with compression for network efficiency
                    pickled_data = pickle.dumps(
                        value, protocol=pickle.HIGHEST_PROTOCOL
                    )
                    # Compress if data is large enough to benefit
                    if len(pickled_data) > 100:
                        compressed_data = zlib.compress(pickled_data, level=1)
                        # Only use compression if it actually reduces size
                        if len(compressed_data) < len(pickled_data):
                            # Store with compression marker
                            self.redis_client.setex(
                                cache_key, timeout, b'ZLIB:' + compressed_data
                            )
                        else:
                            self.redis_client.setex(cache_key, timeout, pickled_data)
                    else:
                        self.redis_client.setex(cache_key, timeout, pickled_data)
            except Exception as e:
                logger.debug(f"Redis set failed for {cache_key}: {e}")
                # Django cache already set, continue without Redis
    def _get_multiple_from_cache(self, cache_keys: list) -> Dict[str, Any]:
        """Get multiple keys from cache in a single operation (Redis optimization)."""
        results = {}

        if self.use_redis and cache_keys:
            try:
                # Single Redis pipeline call for multiple keys
                pipe = self.redis_client.pipeline()
                for key in cache_keys:
                    pipe.get(key)
                redis_results = pipe.execute()

                for i, key in enumerate(cache_keys):
                    cached_data = redis_results[i]
                    if cached_data is not None:
                        if cached_data == b'false':
                            results[key] = False
                        else:
                            try:
                                results[key] = pickle.loads(cached_data)
                            except pickle.PickleError:
                                results[key] = None
                return results
            except Exception as e:
                logger.debug(f"Redis mget failed: {e}")

        # Fallback to Django cache
        for key in cache_keys:
            results[key] = cache.get(key)
        return results

    def _set_multiple_in_cache(self, items: Dict[str, Any],
                               timeout: int = LOCATION_CACHE_TIMEOUT):
        """Set multiple items in cache with single pipeline operation."""
        if self.use_redis and items:
            try:
                # Single Redis pipeline for multiple sets
                pipe = self.redis_client.pipeline()
                for key, value in items.items():
                    if value is False:
                        pipe.setex(key, timeout, b'false')
                    else:
                        # Optimized pickle serialization
                        pickled_data = pickle.dumps(
                            value, protocol=pickle.HIGHEST_PROTOCOL
                        )
                        pipe.setex(key, timeout, pickled_data)
                pipe.execute()
                return
            except Exception as e:
                logger.debug(f"Redis pipeline set failed: {e}")

        # Fallback to Django cache
        for key, value in items.items():
            cache.set(key, value, timeout)

    def get_country_by_code(self, country_code: str):
        """
        Get Country object by ISO2 code with hybrid caching.

        Args:
            country_code: ISO2 country code (e.g., 'US', 'FR')

        Returns:
            Country object or None
        """
        if not country_code:
            return None

        cache_key = f"location:country_code:{country_code.upper()}"
        cached_data = self._get_from_cache(cache_key)

        if cached_data is not None:
            if cached_data is False:
                return None  # Negative result cached
            # Both Redis (pickled) and Django cache return objects directly
            return cached_data

        # Not in cache, fetch from database
        try:
            from core.models import Country
            country = Country.objects.get(iso2=country_code.upper())
            self._set_in_cache(cache_key, country)
            return country
        except Country.DoesNotExist:
            # Cache negative result
            self._set_in_cache(cache_key, False)
            return None
        except Exception as e:
            logger.debug(f"Country lookup failed for {country_code}: {e}")
            return None

    def get_country_by_id(self, country_id: int):
        """
        Get Country object by ID with hybrid caching.

        Args:
            country_id: Country ID

        Returns:
            Country object or None
        """
        if not country_id:
            return None

        cache_key = f"location:country_id:{country_id}"
        cached_data = self._get_from_cache(cache_key)

        if cached_data is not None:
            if cached_data is False:
                return None  # Negative result cached
            # Both Redis (pickled) and Django cache return objects directly
            return cached_data

        # Not in cache, fetch from database
        try:
            from core.models import Country
            country = Country.objects.get(id=country_id)
            self._set_in_cache(cache_key, country)
            return country
        except Country.DoesNotExist:
            # Cache negative result
            self._set_in_cache(cache_key, False)
            return None
        except Exception as e:
            logger.debug(f"Country lookup failed for ID {country_id}: {e}")
            return None

    def get_city_by_name_and_country(self, city_name: str, country):
        """
        Get City object by name and country with hybrid caching.

        Args:
            city_name: City name
            country: Country object

        Returns:
            City object or None
        """
        if not city_name or not country:
            return None

        cache_key = f"location:city:{city_name}:{country.id}"
        cached_data = self._get_from_cache(cache_key)

        if cached_data is not None:
            if cached_data is False:
                return None  # Negative result cached
            # Both Redis (pickled) and Django cache return objects directly
            return cached_data

        # Not in cache, fetch from database
        try:
            from core.models import City
            city = City.objects.filter(
                name__iexact=city_name, country=country
            ).first()
            self._set_in_cache(cache_key, city or False)
            return city
        except Exception as e:
            logger.debug(
                f"City lookup failed for {city_name}, {country.name}: {e}"
            )
            return None

    def get_city_by_id(self, city_id: int):
        """
        Get City object by ID with hybrid caching.

        Args:
            city_id: City ID

        Returns:
            City object or None
        """
        if not city_id:
            return None

        cache_key = f"location:city_id:{city_id}"
        cached_data = self._get_from_cache(cache_key)

        if cached_data is not None:
            if cached_data is False:
                return None  # Negative result cached
            # Both Redis (pickled) and Django cache return objects directly
            return cached_data

        # Not in cache, fetch from database
        try:
            from core.models import City
            city = City.objects.select_related('country').get(id=city_id)
            self._set_in_cache(cache_key, city)
            return city
        except City.DoesNotExist:
            # Cache negative result
            self._set_in_cache(cache_key, False)
            return None
        except Exception as e:
            logger.debug(f"City lookup failed for ID {city_id}: {e}")
            return None

    def resolve_location_from_ip_data(
        self, ip_location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve Country/City objects from IP location data and return with IDs.

        Args:
            ip_location: Dictionary with country_code, city, region, etc.

        Returns:
            Dict with country/city objects and their IDs for storage
        """
        result = {
            'country': None,
            'country_id': None,
            'city': None,
            'city_id': None,
            'country_code': ip_location.get('country_code') or ip_location.get('country_iso_code'),
            'city_name': ip_location.get('city'),
            'region': ip_location.get('region')
        }

        # Get country (handle both country_code and country_iso_code)
        country_code = ip_location.get('country_code') or ip_location.get('country_iso_code')
        if country_code:
            country = self.get_country_by_code(country_code)
            if country:
                result['country'] = country
                result['country_id'] = str(country.id)  # Convert UUID to string

        # Get city
        if result['country'] and ip_location.get('city'):
            city = self.get_city_by_name_and_country(
                ip_location['city'], result['country']
            )
            if city:
                result['city'] = city
                result['city_id'] = str(city.id)  # Convert UUID to string
            elif ip_location.get('region'):
                # Fallback: try by region
                city = self.get_city_by_name_and_country(
                    ip_location['region'], result['country']
                )
                if city:
                    result['city'] = city
                    result['city_id'] = str(city.id)  # Convert UUID to string

        return result

    def resolve_location_from_stored_ids(
        self, location_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve Country/City objects from stored IDs with Redis caching.

        Args:
            location_data: Dictionary with country_id, city_id, etc.

        Returns:
            Dict with resolved country/city objects
        """
        result = {
            'country': None,
            'city': None,
            'country_code': location_data.get('country_code'),
            'city_name': location_data.get('city_name'),
            'region': location_data.get('region')
        }

        # Get country by ID (much faster than by code)
        country_id = location_data.get('country_id')
        if country_id:
            country = self.get_country_by_id(country_id)
            if country:
                result['country'] = country

        # Get city by ID (much faster than by name)
        city_id = location_data.get('city_id')
        if city_id:
            city = self.get_city_by_id(city_id)
            if city:
                result['city'] = city

        return result

    def extend_cache_timeout(self, session_id: str,
                             location_data: Dict[str, Any]):
        """
        Extend cache timeout for location objects when session is extended.

        Args:
            session_id: Session ID for cache key generation
            location_data: Location data with country_id, city_id
        """
        session_timeout = SESSION_DURATION_HOURS * 3600

        try:
            # Extend country cache
            country_id = location_data.get('country_id')
            if country_id:
                country_cache_key = f"location:country_id:{country_id}"
                if self.use_redis:
                    if self.redis_client.exists(country_cache_key):
                        self.redis_client.expire(
                            country_cache_key, session_timeout
                        )
                        logger.debug(
                            f"Extended country cache for session {session_id}"
                        )
                else:
                    # For Django cache, re-set with new timeout
                    country_data = cache.get(country_cache_key)
                    if country_data is not None:
                        cache.set(
                            country_cache_key, country_data, session_timeout
                        )

            # Extend city cache
            city_id = location_data.get('city_id')
            if city_id:
                city_cache_key = f"location:city_id:{city_id}"
                if self.use_redis:
                    if self.redis_client.exists(city_cache_key):
                        self.redis_client.expire(
                            city_cache_key, session_timeout
                        )
                        logger.debug(
                            f"Extended city cache for session {session_id}"
                        )
                else:
                    # For Django cache, re-set with new timeout
                    city_data = cache.get(city_cache_key)
                    if city_data is not None:
                        cache.set(city_cache_key, city_data, session_timeout)

            # Also extend by code cache keys if needed
            country_code = location_data.get('country_code')
            if country_code:
                code_cache_key = (
                    f"location:country_code:{country_code.upper()}"
                )
                if self.use_redis:
                    if self.redis_client.exists(code_cache_key):
                        self.redis_client.expire(
                            code_cache_key, session_timeout
                        )
                else:
                    # For Django cache, re-set with new timeout
                    code_data = cache.get(code_cache_key)
                    if code_data is not None:
                        cache.set(code_cache_key, code_data, session_timeout)

        except Exception as e:
            logger.debug(
                f"Failed to extend cache for session {session_id}: {e}"
            )

    def preload_session_location_cache(self, session_id: str,
                                       location_data: Dict[str, Any]):
        """
        Preload location cache when session is created/updated.

        Args:
            session_id: Session ID for logging
            location_data: Location data with country_id, city_id
        """
        try:
            # Preload country if not in cache
            country_id = location_data.get('country_id')
            if country_id:
                country_cache_key = f"location:country_id:{country_id}"
                cache_exists = False

                if self.use_redis:
                    cache_exists = self.redis_client.exists(country_cache_key)
                else:
                    cache_exists = cache.get(country_cache_key) is not None

                if not cache_exists:
                    country = self.get_country_by_id(country_id)
                    if country:
                        logger.debug(
                            f"Preloaded country cache for session {session_id}"
                        )

            # Preload city if not in cache
            city_id = location_data.get('city_id')
            if city_id:
                city_cache_key = f"location:city_id:{city_id}"
                cache_exists = False

                if self.use_redis:
                    cache_exists = self.redis_client.exists(city_cache_key)
                else:
                    cache_exists = cache.get(city_cache_key) is not None

                if not cache_exists:
                    city = self.get_city_by_id(city_id)
                    if city:
                        logger.debug(
                            f"Preloaded city cache for session {session_id}"
                        )

        except Exception as e:
            logger.debug(
                f"Failed to preload cache for session {session_id}: {e}"
            )

    def clear_location_cache(self):
        """Clear all location-related cache entries from both caches."""
        try:
            if self.use_redis:
                # Delete all location cache keys from Redis
                for pattern in [
                    'location:country_code:*',
                    'location:country_id:*',
                    'location:city_id:*',
                    'location:city:*'
                ]:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                        logger.debug(
                            f"Cleared {len(keys)} {pattern} cache entries"
                        )
            else:
                # For Django cache, we need to clear by pattern
                # This is a limitation - Django cache doesn't support patterns
                logger.debug("Django cache doesn't support pattern clearing")

        except Exception as e:
            logger.debug(f"Failed to clear location cache: {e}")


# Global service instance
location_cache_service = LocationCacheService()
