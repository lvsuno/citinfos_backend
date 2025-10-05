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

    def get_administrative_division_by_id(self, division_id):
        """
        Get AdministrativeDivision object by ID with hybrid caching.

        Args:
            division_id: Administrative Division ID

        Returns:
            AdministrativeDivision object or None
        """
        if not division_id:
            return None

        cache_key = f"location:admin_division_id:{division_id}"
        cached_data = self._get_from_cache(cache_key)

        if cached_data is not None:
            if cached_data is False:
                return None  # Negative result cached
            return cached_data

        # Not in cache, fetch from database
        try:
            from core.models import AdministrativeDivision
            division = AdministrativeDivision.objects.select_related(
                'country', 'parent'
            ).get(id=division_id)
            self._set_in_cache(cache_key, division)
            return division
        except AdministrativeDivision.DoesNotExist:
            # Cache negative result
            self._set_in_cache(cache_key, False)
            return None
        except Exception as e:
            logger.debug(f"Division lookup failed for ID {division_id}: {e}")
            return None

    def get_administrative_division_by_coordinates(self, lat, lng, country=None):
        """
        Get closest AdministrativeDivision by coordinates with caching.

        Args:
            lat: Latitude
            lng: Longitude
            country: Optional country to restrict search

        Returns:
            AdministrativeDivision object or None
        """
        if not lat or not lng:
            return None

        # Create cache key based on coordinates (rounded to reasonable precision)
        lat_rounded = round(float(lat), 4)
        lng_rounded = round(float(lng), 4)
        country_filter = country.id if country else 'global'
        cache_key = f"location:coords:{lat_rounded}:{lng_rounded}:{country_filter}"

        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            if cached_data is False:
                return None
            return cached_data

        # Not in cache, find closest division
        try:
            from django.contrib.gis.geos import Point
            from django.contrib.gis.db.models.functions import Distance
            from core.models import AdministrativeDivision

            user_point = Point(lng, lat, srid=4326)

            # Build query
            queryset = AdministrativeDivision.objects.filter(
                geometry__dwithin=(user_point, 0.1)  # ~10km
            )

            if country:
                queryset = queryset.filter(country=country)

            division = queryset.annotate(
                distance=Distance('geometry', user_point)
            ).order_by('distance').first()

            # Cache result (even if None)
            self._set_in_cache(cache_key, division or False)
            return division

        except Exception as e:
            logger.debug(f"Coordinate division lookup failed: {e}")
            return None

    def resolve_location_from_ip_data(
        self, ip_location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve AdministrativeDivision from IP location data using coordinates.

        Args:
            ip_location: Dictionary with latitude, longitude, city, region, etc.

        Returns:
            Dict with administrative division data for storage
        """
        result = {
            'administrative_division_id': None,
            'division_name': None,
            'latitude': ip_location.get('latitude'),
            'longitude': ip_location.get('longitude'),
            'region': ip_location.get('region'),
            'user_timezone': None,
            'detected_timezone': ip_location.get('timezone'),
            'timezone_source': 'ip_detection',
            # Reference data (not part of core location_data but useful)
            'original_city': ip_location.get('city'),
            'country_iso_code': ip_location.get('country_code') or ip_location.get('country_iso_code'),
            'country_name': None
        }

        # Get administrative division using coordinates
        lat = ip_location.get('latitude')
        lng = ip_location.get('longitude')

        if lat and lng:
            division = self.get_administrative_division_by_coordinates(lat, lng)
            if division:
                result['administrative_division_id'] = str(division.id)
                result['division_name'] = division.name
                result['country_name'] = division.country.name
                result['country_iso_code'] = division.country.iso2

        return result

    def resolve_location_from_stored_ids(
        self, location_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve AdministrativeDivision objects from stored IDs.

        Args:
            location_data: Dictionary with administrative_division_id, etc.

        Returns:
            Dict with resolved administrative division objects
        """
        result = {
            'administrative_division_id': location_data.get('administrative_division_id'),
            'division_name': location_data.get('division_name'),
            'region': location_data.get('region'),
            'latitude': location_data.get('latitude'),
            'longitude': location_data.get('longitude'),
            'user_timezone': location_data.get('user_timezone'),
            'detected_timezone': location_data.get('detected_timezone'),
            'timezone_source': location_data.get('timezone_source', 'unknown'),
            # Reference data
            'original_city': location_data.get('original_city'),
            'country_iso_code': location_data.get('country_iso_code'),
            'country_name': location_data.get('country_name')
        }

        # Get administrative division by ID to ensure current data (optional refresh)
        division_id = location_data.get('administrative_division_id')
        if division_id:
            division = self.get_administrative_division_by_id(division_id)
            if division:
                result['division_name'] = division.name
                result['country_name'] = division.country.name
                result['country_iso_code'] = division.country.iso2

        return result

    def extend_cache_timeout(self, session_id: str,
                             location_data: Dict[str, Any]):
        """
        Extend cache timeout for location objects when session is extended.

        Args:
            session_id: Session ID for cache key generation
            location_data: Location data with administrative_division_id
        """
        session_timeout = SESSION_DURATION_HOURS * 3600

        try:
            # Extend administrative division cache
            division_id = location_data.get('administrative_division_id')
            if division_id:
                division_cache_key = f"location:admin_division_id:{division_id}"
                if self.use_redis:
                    if self.redis_client.exists(division_cache_key):
                        self.redis_client.expire(
                            division_cache_key, session_timeout
                        )
                        logger.debug(
                            f"Extended division cache for session {session_id}"
                        )
                else:
                    # For Django cache, re-set with new timeout
                    division_data = cache.get(division_cache_key)
                    if division_data is not None:
                        cache.set(
                            division_cache_key, division_data, session_timeout
                        )

            # Extend coordinate-based cache if available
            lat = location_data.get('latitude')
            lng = location_data.get('longitude')
            if lat and lng:
                lat_rounded = round(float(lat), 4)
                lng_rounded = round(float(lng), 4)
                coord_cache_key = f"location:coords:{lat_rounded}:{lng_rounded}:global"
                if self.use_redis:
                    if self.redis_client.exists(coord_cache_key):
                        self.redis_client.expire(coord_cache_key, session_timeout)
                else:
                    coord_data = cache.get(coord_cache_key)
                    if coord_data is not None:
                        cache.set(coord_cache_key, coord_data, session_timeout)

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
            location_data: Location data with administrative_division_id
        """
        try:
            # Preload administrative division if not in cache
            division_id = location_data.get('administrative_division_id')
            if division_id:
                division_cache_key = f"location:admin_division_id:{division_id}"
                cache_exists = False

                if self.use_redis:
                    cache_exists = self.redis_client.exists(division_cache_key)
                else:
                    cache_exists = cache.get(division_cache_key) is not None

                if not cache_exists:
                    division = self.get_administrative_division_by_id(division_id)
                    if division:
                        logger.debug(
                            f"Preloaded division cache for session {session_id}"
                        )

            # Preload coordinate cache if available
            lat = location_data.get('latitude')
            lng = location_data.get('longitude')
            if lat and lng:
                lat_rounded = round(float(lat), 4)
                lng_rounded = round(float(lng), 4)
                coord_cache_key = f"location:coords:{lat_rounded}:{lng_rounded}:global"

                cache_exists = False
                if self.use_redis:
                    cache_exists = self.redis_client.exists(coord_cache_key)
                else:
                    cache_exists = cache.get(coord_cache_key) is not None

                if not cache_exists:
                    # This will populate the coordinate cache
                    self.get_administrative_division_by_coordinates(lat, lng)

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
                    'location:admin_division_id:*',
                    'location:coords:*'
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
