"""
Session Management utility for handling both Redis and Database storage.
"""

import json
import re
import redis
import logging
from django.conf import settings
# from django.core.cache import cache  # Unused, keeping for potential use
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Any, Optional
from .utils import get_client_ip, get_location_from_ip
from .location_db_cache import location_cache_service

logger = logging.getLogger(__name__)

# Session duration constants (aligned with user verification cycle)
SESSION_DURATION_HOURS = getattr(settings, 'SESSION_DURATION_HOURS', 4)
SESSION_DURATION_SECONDS = SESSION_DURATION_HOURS * 60 * 60


class SessionManager:
    """
    Hybrid session manager using Redis for fast access and Database for
    persistence.
    """

    def __init__(self):
        self.redis_client = None
        self.use_redis = getattr(settings, 'USE_REDIS_SESSIONS', False)

        if self.use_redis:
            try:
                redis_url = getattr(
                    settings, 'REDIS_URL', 'redis://localhost:6379/1'
                )
                self.redis_client = redis.from_url(
                    redis_url, decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}. "
                      "Falling back to database only.")
                self.use_redis = False

    def _get_models(self):
        """Lazy import of models to avoid circular imports."""
        from accounts.models import UserSession, UserProfile
        return UserSession, UserProfile

    def create_minimal_session_with_db(self, request, user_profile,
                                       persistent=False) -> dict:
        """
        Create minimal session for immediate login response with DB storage.
        Full session data will be populated asynchronously.

        Args:
            request: Django request object
            user_profile: UserProfile instance
            device_info: Device information dict (server + client info)
            persistent: Whether this is a "remember me" session

        Returns:
            Dict with session_id and other minimal data
        """
        from django.conf import settings
        import hashlib

        # Generate session ID and hash it
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key

        # Enhance session ID uniqueness to prevent duplicates
        # Add timestamp and entropy to make it more unique
        import time
        import random
        unique_suffix = f"{int(time.time() * 1000000)}{random.randint(1000, 9999)}"
        enhanced_session_id = f"{session_id}_{unique_suffix}"

        # Hash the enhanced session ID using the algorithm from settings
        hash_algo = getattr(settings, 'SESSION_TOKEN_HASH_ALGO', 'sha256')
        hashed_session_id = hashlib.new(
            hash_algo, enhanced_session_id.encode()
        ).hexdigest()

        # Get basic IP address
        ip_address = get_client_ip(request)

        # Fast device fingerprint for immediate response
        from core.device_fingerprint import get_fast_device_fingerprint
        fast_fingerprint = get_fast_device_fingerprint(request)

        # Calculate expiration based on persistent flag
        if persistent:
            # Remember me: 30 days
            default_hours = getattr(
                settings, 'PERSISTENT_SESSION_DURATION_DAYS', 30
            ) * 24
        else:
            # Normal session: 4 hours
            default_hours = getattr(settings, 'SESSION_DURATION_HOURS', 4)
        started_at = timezone.now()
        expires_at = started_at + timedelta(hours=default_hours)

        # Create UserSession in database for persistence with get_or_create to handle duplicates
        UserSession, _ = self._get_models()
        try:
            db_session, created = UserSession.objects.get_or_create(
                session_id=hashed_session_id,  # Use hashed version as unique key
                defaults={
                    'user': user_profile,
                    'ip_address': ip_address,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'device_fingerprint': fast_fingerprint,
                    'fast_fingerprint': fast_fingerprint,
                    'location_data': {},  # Will be filled asynchronously
                    'persistent': persistent,
                    'started_at': started_at,
                    'expires_at': expires_at,
                    'is_active': True,
                    'is_ended': False
                }
            )
            if not created:
                # If session already exists, update key fields and reactivate
                db_session.user = user_profile
                db_session.ip_address = ip_address
                db_session.user_agent = request.META.get('HTTP_USER_AGENT', '')
                db_session.device_fingerprint = fast_fingerprint
                db_session.fast_fingerprint = fast_fingerprint
                db_session.persistent = persistent
                db_session.expires_at = expires_at
                db_session.is_active = True
                db_session.is_ended = False
                db_session.save(update_fields=[
                    'user', 'ip_address', 'user_agent', 'device_fingerprint',
                    'fast_fingerprint', 'persistent', 'expires_at', 'is_active',
                    'is_ended', 'updated_at'
                ])
        except Exception as e:
            # Log but don't fail login if DB session creation fails
            import logging
            logger = logging.getLogger('core.session_manager')
            logger.warning(f"Failed to create/update DB session for {hashed_session_id[:8]}...: {e}")
            db_session = None

        # Minimal session data for Redis (fast response)
        minimal_data = {
            'user_id': str(user_profile.id),
            'user_username': user_profile.user.username,
            'session_id': hashed_session_id,  # Store hashed version
            'ip_address': ip_address,
            'device_fingerprint': fast_fingerprint,
            'fast_fingerprint': fast_fingerprint,  # Add this for fingerprint lookup
            'persistent': persistent,
            'is_active': True,
            'is_ended': False,
            'started_at': started_at.isoformat(),
            'expires_at': expires_at.isoformat(),
            'minimal': True,  # Flag for async enhancement
            'db_session_id': str(db_session.id) if db_session else None
        }

        # Store in Redis immediately (5-15ms)
        if self.use_redis:
            try:
                redis_key = f"session:{hashed_session_id}"
                self.redis_client.setex(
                    redis_key,
                    SESSION_DURATION_SECONDS,
                    json.dumps(minimal_data, default=str)
                )

                # Add to user's active sessions
                user_sessions_key = f"user_sessions:{user_profile.id}"
                self.redis_client.sadd(user_sessions_key, hashed_session_id)
                self.redis_client.expire(
                    user_sessions_key, SESSION_DURATION_SECONDS
                )
            except Exception as e:
                import logging
                logger = logging.getLogger('core.session_manager')
                logger.warning(f"Failed to store session in Redis: {e}")

        return {
            'session_id': hashed_session_id,
            'raw_session_id': session_id,  # For Django session management
            'user_id': str(user_profile.id),
            'expires_at': expires_at.isoformat(),
            'persistent': persistent,
            'db_session': db_session
        }

    # def create_session(self, request, user_profile,
    #                    merged_device_info: Dict[str, Any],
    #                    user_timezone: Optional[str] = None) -> Dict[str, Any]:
    #     """
    #     Create a new session in both Redis and Database using Django
    #     session ID. We extract the session ID from Django but store our
    #     own session data.

    #     Args:
    #         request: Django request object
    #         user_profile: UserProfile instance
    #         merged_device_info: Device information from client
    #         user_timezone: User's actual timezone from browser/device
    #     """
    #     # Extract session ID from Django session (but don't store Django session data)
    #     session_id = request.session.session_key
    #     if not session_id:
    #         request.session.create()
    #         session_id = request.session.session_key

    #     ip_address = get_client_ip(request)

    #     # OPTIMIZATION: Use fast cached location service
    #     location_data = {}
    #     try:
    #         from core.ip_location_service import FastLocationService
    #         # Try cached location first (5-20ms instead of 500ms-2s)
    #         cached_location = FastLocationService.get_location_fast(ip_address)

    #         if cached_location and cached_location.get('country_code'):
    #             # Use cached location data
    #             raw_location = cached_location
    #             location_data = self._resolve_and_store_location_data(
    #                 raw_location, user_timezone
    #             )
    #         else:
    #             raise ImportError("Fast cache miss, use fallback")

    #     except (ImportError, Exception):
    #         # Fallback to direct IP location lookup
    #         raw_location = get_location_from_ip(ip_address)
    #         if raw_location:
    #             location_data = self._resolve_and_store_location_data(
    #                 raw_location, user_timezone
    #             )
    #         else:
    #             # Store basic timezone info only
    #             location_data = {
    #                 'user_timezone': user_timezone,  # User's actual timezone
    #                 'detected_timezone': None,       # IP-based timezone (async)
    #             }

    #     # OPTIMIZATION: Use fast device fingerprint for immediate response
    #     from core.device_fingerprint import get_fast_device_fingerprint
    #     fast_fingerprint = get_fast_device_fingerprint(request)

    #     # Session data structure with fast fingerprint
    #     session_data = {
    #         'user_id': str(user_profile.id),  # Convert UUID to string
    #         'user_username': user_profile.user.username,
    #         'session_id': session_id,
    #         'ip_address': ip_address,
    #         'user_agent': request.META.get('HTTP_USER_AGENT', ''),
    #         'device_info': merged_device_info,
    #         'location_data': location_data,
    #         'device_fingerprint': fast_fingerprint,  # Fast fingerprint first
    #         'is_active': True,
    #         'started_at': None,  # Will be set by database
    #     }

    #     # Store in Database (persistent)
    #     UserSession, UserProfile = self._get_models()
    #     user_session, created = UserSession.objects.get_or_create(
    #         user=user_profile,
    #         session_id=session_id,
    #         defaults={
    #             'ip_address': ip_address,
    #             'user_agent': session_data['user_agent'],
    #             'device_info': merged_device_info,
    #             'location_data': location_data,
    #             'device_fingerprint': fast_fingerprint,  # Use fast fingerprint
    #             'is_active': True,
    #         }
    #     )

    #     if not created:
    #         # Update existing session
    #         user_session.device_info = merged_device_info
    #         user_session.location_data = location_data
    #         user_session.device_fingerprint = fast_fingerprint  # Use fast fingerprint
    #         user_session.is_active = True
    #         user_session.save()

    #     session_data['started_at'] = user_session.started_at.isoformat()

    #     # Store in Redis (fast access) with session duration expiration
    #     if self.use_redis:
    #         try:
    #             redis_key = f"session:{session_id}"
    #             self.redis_client.setex(
    #                 redis_key,
    #                 SESSION_DURATION_SECONDS,  # 4 hours (matches user verification)
    #                 json.dumps(session_data, default=str)
    #             )

    #             # Also store user's active sessions list
    #             user_sessions_key = f"user_sessions:{user_profile.id}"
    #             self.redis_client.sadd(user_sessions_key, session_id)
    #             self.redis_client.expire(user_sessions_key, SESSION_DURATION_SECONDS)
    #         except Exception as e:
    #             print(f"Redis storage failed: {e}")

    #     # Preload location cache for session duration
    #     if location_data:
    #         location_cache_service.preload_session_location_cache(
    #             session_id, location_data
    #         )

    #     return session_data

    def _resolve_and_store_location_data(
        self,
        raw_location: Dict[str, Any],
        user_timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve location data to include Country/Administrative Division IDs for efficient
        future lookups and both user-provided and detected timezones.

        Args:
            raw_location: Raw location data from IP lookup
            user_timezone: User's actual timezone from browser/device

        Returns:
            Enhanced location data with Country/Administrative Division IDs and timezone info
        """
        if not raw_location:
            return {}

        try:
            from core.location_db_cache import location_cache_service
            resolved_location = (
                location_cache_service.resolve_location_from_ip_data(
                    raw_location
                )
            )

            # Store both the resolved objects and IDs for efficient retrieval
            enhanced_location = {
                # Administrative division data
                'division_name': resolved_location.get('division_name'),
                'region': resolved_location.get('region'),
                'administrative_division_id': resolved_location.get(
                    'administrative_division_id'
                ),

                # Additional IP location data
                'latitude': raw_location.get('latitude'),
                'longitude': raw_location.get('longitude'),

                # TIMEZONE INFORMATION
                'user_timezone': user_timezone,  # User's actual timezone
                'detected_timezone': raw_location.get('timezone'),  # IP-based
                'timezone_source': 'user' if user_timezone else 'ip_detection',
            }

            return enhanced_location

        except Exception as e:
            print(f"Location cache service failed: {e}")
            # Fallback to manual location resolution
            return self._manual_location_resolution(raw_location, user_timezone)

    def _manual_location_resolution(self, raw_location, user_timezone):
        """
        Manual location resolution when cache service fails.
        Directly queries the database for Country/Administrative Division objects.
        """
        try:
            from core.models import AdministrativeDivision

            enhanced_location = {
                # Original data
                'division_name': raw_location.get('city'),  # City is now part of administrative division
                'region': raw_location.get('region'),
                'administrative_division_id': None,

                # Additional IP location data
                'latitude': raw_location.get('latitude'),
                'longitude': raw_location.get('longitude'),

                # TIMEZONE INFORMATION
                'user_timezone': user_timezone,
                'detected_timezone': raw_location.get('timezone'),
                'timezone_source': 'user' if user_timezone else 'ip_detection',
            }

            # Try to get administrative division ID (search by name only)
            division_name = raw_location.get('city')
            if division_name:
                try:
                    division = AdministrativeDivision.objects.filter(
                        name__iexact=division_name
                    ).first()
                    if division:
                        enhanced_location['administrative_division_id'] = str(division.id)  # Convert UUID to string
                except Exception:
                    pass

            return enhanced_location

        except ImportError:
            # Models not available, return basic data
            return {
                'division_name': raw_location.get('city'),  # City is now part of administrative division
                'region': raw_location.get('region'),
                'administrative_division_id': None,
                'user_timezone': user_timezone,
                'detected_timezone': raw_location.get('timezone'),
                'timezone_source': 'user' if user_timezone else 'ip_detection',
            }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data, trying Redis first, then Database.
        Database is only used when Redis is completely disabled in settings.
        """
        if self.use_redis:
            try:
                redis_key = f"session:{session_id}"
                redis_data = self.redis_client.get(redis_key)
                if redis_data:
                    return json.loads(redis_data)
                else:
                    # If Redis is enabled but key not found, session doesn't exist
                    return None
            except Exception as e:
                print(f"Redis get failed: {e}")
                return None

        # Only fallback to database when Redis is completely disabled
        UserSession, UserProfile = self._get_models()
        try:
            user_session = UserSession.objects.select_related('user__user').get(
                session_id=session_id,
                is_active=True
            )
            return {
                'user_id': str(user_session.user.id),  # Convert UUID to string
                'user_username': user_session.user.user.username,
                'session_id': user_session.session_id,
                'ip_address': user_session.ip_address,
                'user_agent': user_session.user_agent,
                'device_info': user_session.device_info,
                'location_data': user_session.location_data,
                'device_fingerprint': user_session.device_fingerprint,
                'is_active': user_session.is_active,
                'created_at': user_session.started_at.isoformat(),
            }
        except UserSession.DoesNotExist:
            return None

    def is_session_valid_for_jwt(self, session_id: str) -> bool:
        """
        CRITICAL: Strict session validation for JWT token generation/refresh.
        JWT tokens should ONLY be issued if a valid session exists in Redis/DB.

        Args:
            session_id: Session ID to validate

        Returns:
            bool: True only if session exists, is active, and not expired
        """
        if not session_id:
            return False

        # Primary check: Redis (fast)
        if self.use_redis:
            try:
                redis_key = f"session:{session_id}"
                session_data = self.redis_client.get(redis_key)
                if session_data:
                    parsed_data = json.loads(session_data)
                    is_active = parsed_data.get('is_active', False)
                    if is_active:
                        # Extend Redis expiration on successful validation
                        # self.redis_client.expire(redis_key, SESSION_DURATION_SECONDS)
                        return True
                    return False
                # Fall through to database check if not in Redis
            except Exception as e:
                print(f"Redis session validation failed: {e}")
                # Fall through to database check

        # Secondary check: Database (persistent)
        UserSession, UserProfile = self._get_models()
        try:
            session = UserSession.objects.get(
                session_id=session_id,
                is_active=True,
                is_deleted=False
            )

            # Check if session is expired (older than SESSION_DURATION_HOURS)

            if timezone.now() > session.expires_at:
                # Session expired - mark as inactive
                session.mark_ended(reason='expired (checked during JWT validation) in absence of Redis')
                return False

            return True

        except UserSession.DoesNotExist:
            return False
        except Exception as e:
            print(f"Database session validation failed: {e}")
            return False

    def validate_session_for_user(self, session_id: str, user_profile_id: str) -> bool:
        """
        Validate that a session belongs to a specific user and is active.

        Args:
            session_id: Session ID to validate
            user_profile_id: UserProfile ID that should own the session

        Returns:
            bool: True if session exists, is active, and belongs to user
        """
        if not session_id or not user_profile_id:
            return False

        # Check Redis first
        if self.use_redis:
            try:
                redis_key = f"session:{session_id}"
                session_data = self.redis_client.get(redis_key)
                if session_data:
                    parsed_data = json.loads(session_data)
                    session_user_id = parsed_data.get('user_id')
                    is_active = parsed_data.get('is_active', False)

                    # Validate ownership and activity
                    if str(session_user_id) == str(user_profile_id) and is_active:
                        return True
                    return False
            except Exception as e:
                print(f"Redis session-user validation failed: {e}")

        # Database fallback
        UserSession, UserProfile = self._get_models()
        try:
            return UserSession.objects.filter(
                session_id=session_id,
                user_id=user_profile_id,
                is_active=True,
                is_deleted=False
            ).exists()
        except Exception as e:
            print(f"Database session-user validation failed: {e}")
            return False

    def should_renew_session(self, session_id: str) -> bool:
        """
        Check if session should be renewed based on remaining validity.
        Only renew when session has 10% (10%) or less validity remaining.

        Args:
            session_id: Session ID to check

        Returns:
            bool: True if session should be renewed
        """
        if not session_id:
            return False

        # Check Redis TTL (Time To Live)
        if self.use_redis:
            try:
                redis_key = f"session:{session_id}"
                ttl = self.redis_client.ttl(redis_key)

                if ttl <= 0:
                    return False  # Session expired or doesn't exist

                # Renew if remaining time is 10% or less of total duration
                renewal_threshold = SESSION_DURATION_SECONDS * 0.1  # 10%
                return ttl <= renewal_threshold

            except Exception as e:
                print(f"Failed to check session TTL: {e}")
                return False

        # Fallback: Check database session age
        UserSession, _ = self._get_models()
        try:
            session = UserSession.objects.get(
                session_id=session_id,
                is_active=True,
                is_deleted=False
            )

            # Calculate session remaining time
            from datetime import timedelta
            session_remaining_time = session.expires_at - timezone.now()
            total_duration = timedelta(seconds=SESSION_DURATION_SECONDS)

            # Renew if session has used 75% or more of its time
            return session_remaining_time <= (total_duration * 0.25)

        except UserSession.DoesNotExist:
            return False
        except Exception as e:
            print(f"Failed to check session age: {e}")
            return False

    def smart_renew_session_if_needed(self, session_id: str, check_renew: bool=True) -> bool:
        """
        Intelligently renew session only when needed (10% validity remaining).

        Args:
            session_id: Session ID to potentially renew
            check_renew: If True, check if renewal is needed before renewing

        Returns:
            bool: True if session was renewed, False if no renewal needed
        """
        if check_renew:
            if not self.should_renew_session(session_id):
                return False  # No renewal needed

        UserSession, _ = self._get_models()

        # Get the session instance and extend it
        try:
            session = UserSession.objects.get(
                session_id=session_id,
                is_active=True,
                is_deleted=False
            )
            session.extend_session()  # Call on instance, not class
            logger.info(f"Session {session_id[:20]}... extended successfully")
            return True
        except UserSession.DoesNotExist:
            logger.warning(f"Session {session_id[:20]}... not found for extension")
            return False
        except Exception as e:
            logger.error(f"Failed to extend session {session_id[:20]}...: {e}")
            return False

    def invalidate_session(self, session_id: str):
        """
        Invalidate a session in both Redis and Database.
        """
        if self.use_redis:
            try:
                # Remove from Redis
                redis_key = f"session:{session_id}"
                self.redis_client.delete(redis_key)

                # Remove from user's active sessions
                session_data = self.get_session(session_id)
                if session_data:
                    user_sessions_key = f"user_sessions:{session_data['user_id']}"
                    self.redis_client.srem(user_sessions_key, session_id)

            except Exception as e:
                print(f"Redis invalidation failed: {e}")

        # Update database
        UserSession, UserProfile = self._get_models()
        try:
            session = UserSession.objects.filter(session_id=session_id).first()
            if session:
                session.mark_ended(reason="log out or manual invalidation")
        except Exception as e:
            print(f"Database invalidation failed: {e}")

    def get_user_active_sessions(self, user_profile_id) -> list:
        """
        Get all active sessions for a user profile.

        Args:
            user_profile_id: The UserProfile ID (UUID or string)
        """
        if self.use_redis:
            try:
                user_sessions_key = f"user_sessions:{user_profile_id}"
                session_ids = self.redis_client.smembers(user_sessions_key)
                sessions = []
                for session_id in session_ids:
                    session_data = self.get_session(session_id)
                    if session_data:
                        sessions.append(session_data)
                return sessions
            except Exception as e:
                print(f"Redis user sessions failed: {e}")

        # Fallback to database
        UserSession, UserProfile = self._get_models()
        try:
            user_sessions = UserSession.objects.filter(
                user_id=user_profile_id,
                is_active=True
            ).select_related('user__user')

            return [{
                'user_id': str(session.user.id),  # Convert UUID to string
                'user_username': session.user.user.username,
                'session_id': session.session_id,
                'ip_address': session.ip_address,
                'user_agent': session.user_agent,
                'device_info': session.device_info,
                'location_data': session.location_data,
                'device_fingerprint': session.device_fingerprint,
                'is_active': session.is_active,
                'created_at': session.started_at.isoformat(),
            } for session in user_sessions]
        except Exception as e:
            print(f"Database user sessions failed: {e}")
            return []

    def cleanup_expired_sessions(self):
        """
        Clean up expired sessions from database based on expires_at field.
        Redis handles its own expiration.
        """

        # Mark sessions as inactive if they've passed their expires_at time
        now = timezone.now()
        UserSession, UserProfile = self._get_models()
        expired_sessions = UserSession.objects.filter(
            expires_at__lt=now,
            is_active=True,
            is_ended=False,
            is_deleted=False,
        )

        for session in expired_sessions:
            session.mark_ended(
                reason="Session expired - automatic cleanup",
                from_cleanup=True
            )

    def enforce_session_limit(self, user_profile_id, max_sessions: int = 5):
        """
        Enforce maximum number of active sessions per user.
        Terminates oldest sessions if limit exceeded.

        Args:
            user_profile_id: The UserProfile ID (UUID or string)
        """


        active_sessions = self.get_user_active_sessions(user_profile_id)

        if len(active_sessions) >= max_sessions:
            # Sort by creation time, oldest first
            oldest_sessions = sorted(
                active_sessions,
                key=lambda x: x.get('created_at', '')
            )

            # Terminate oldest sessions to make room
            sessions_to_remove = len(active_sessions) - max_sessions + 1
            for session in oldest_sessions[:sessions_to_remove]:
                self.invalidate_session(session['session_id'])

        return True

    def find_any_active_session_by_fingerprint(self, fast_fingerprint: str) -> Optional[Dict[str, Any]]:
        """
        Find ANY active session by fast device fingerprint (across all users).
        Used for post-restart authentication fallback.

        Note: In edge cases where multiple users share same device, returns most recent session.

        Args:
            fast_fingerprint: Fast device fingerprint hash

        Returns:
            Dict with session data if found and valid, None otherwise
        """
        logger = logging.getLogger('core.session_manager')

        # STEP 1: Check Redis first (fast path)
        if self.use_redis:
            try:
                # Get all session keys from Redis
                session_keys = self.redis_client.keys('session:*')

                for key in session_keys:
                    try:
                        session_data_str = self.redis_client.get(key)
                        if session_data_str:
                            session_data = json.loads(session_data_str)

                            # Check if fingerprint matches (check both fields for compatibility)
                            stored_fp = session_data.get('device_fingerprint', '')
                            stored_fast_fp = session_data.get('fast_fingerprint', '')

                            if (stored_fp == fast_fingerprint or
                                stored_fast_fp == fast_fingerprint):

                                # Verify session is active
                                if session_data.get('is_active', False):
                                    logger.info(f"Found session in Redis for fingerprint: {fast_fingerprint[:16]}...")

                                    # Get user profile for the session
                                    user_id = session_data.get('user_id')
                                    if user_id:
                                        try:
                                            from accounts.models import UserProfile
                                            user_profile = UserProfile.objects.get(id=user_id)
                                            session_data['user_profile'] = user_profile
                                            return session_data
                                        except Exception as e:
                                            logger.warning(f"Could not get user profile {user_id}: {e}")
                                            continue

                    except Exception as e:
                        logger.debug(f"Error parsing Redis session {key}: {e}")
                        continue

            except Exception as e:
                logger.warning(f"Redis lookup failed for fingerprint: {e}")

        # STEP 2: Fallback to database (slower path)
        try:
            UserSession, _ = self._get_models()
            from django.utils import timezone

            # Fix: Use correct select_related - UserSession -> UserProfile -> User
            session = UserSession.objects.filter(
                fast_fingerprint=fast_fingerprint,
                is_active=True,
                is_ended=False,
                expires_at__gt=timezone.now()
            ).select_related('user').order_by('-started_at').first()

            if session:
                logger.info(f"Found session in DB for fingerprint: {fast_fingerprint[:16]}...")

                # Convert to session data format
                session_data = {
                    'session_id': session.session_id,
                    'user_id': str(session.user.id),
                    'user_username': session.user.user.username,
                    'ip_address': session.ip_address,
                    'device_fingerprint': session.device_fingerprint,
                    'fast_fingerprint': session.fast_fingerprint,
                    'persistent': session.persistent,
                    'is_active': session.is_active,
                    'is_ended': session.is_ended,
                    'started_at': session.started_at.isoformat(),
                    'expires_at': session.expires_at.isoformat(),
                    'location_data': session.location_data,
                    'db_session_id': str(session.id),
                    'user_profile': session.user  # Include for convenience
                }

                # Verify session is also valid for JWT
                if self.is_session_valid_for_jwt(session.session_id):
                    return session_data

        except Exception as e:
            logger.warning(f"Error finding session by fingerprint in DB: {e}")

        return None

        return None

    def find_existing_session_by_fast_fingerprint(self, user_profile,
                                                   fast_fingerprint: str) -> Optional[Dict[str, Any]]:
        """
        Find existing valid session for specific user by fast device fingerprint.
        Used for fast session reuse during login.

        Args:
            user_profile: UserProfile instance
            fast_fingerprint: Fast device fingerprint hash

        Returns:
            Dict with session data if found and valid, None otherwise
        """
        UserSession, _ = self._get_models()
        from django.utils import timezone

        try:
            # Find active sessions for this user with matching fast fingerprint
            session = UserSession.objects.filter(
                user=user_profile,
                fast_fingerprint=fast_fingerprint,
                is_active=True,
                is_ended=False,
                expires_at__gt=timezone.now()
            ).order_by('-started_at').first()

            if session:
                # Convert to session data format
                session_data = {
                    'session_id': session.session_id,
                    'user_id': str(user_profile.id),
                    'user_username': user_profile.user.username,
                    'ip_address': session.ip_address,
                    'device_fingerprint': session.device_fingerprint,
                    'persistent': session.persistent,
                    'is_active': session.is_active,
                    'is_ended': session.is_ended,
                    'started_at': session.started_at.isoformat(),
                    'expires_at': session.expires_at.isoformat(),
                    'location_data': session.location_data,
                    'db_session_id': str(session.id)
                }

                # Verify session is also valid for JWT
                if self.is_session_valid_for_jwt(session.session_id):
                    return session_data

        except Exception as e:
            logger = logging.getLogger('core.session_manager')
            logger.warning(f"Error finding session by fast fingerprint: {e}")

        return None

    def fast_login_with_session_reuse(self, request, user_profile, persistent=False) -> Dict[str, Any]:
        """
        Optimized login that tries to reuse existing sessions first.
        Creates new session only if no valid session exists for this device.

        Args:
            request: Django request object
            user_profile: UserProfile instance
            persistent: Whether this is a "remember me" session (30 days vs 4 hours)

        Returns:
            Dict with session data and 'reused' flag
        """
        from core.device_fingerprint import OptimizedDeviceFingerprint

        # Generate fast fingerprint for device identification
        fast_fingerprint = OptimizedDeviceFingerprint.get_fast_fingerprint(request)

        # Try to find existing valid session for this device
        existing_session = self.find_existing_session_by_fast_fingerprint(
            user_profile, fast_fingerprint
        )

        if existing_session:
            # Session found - renew immediately for extended validity
            session_id = existing_session['session_id']

            # Force immediate renewal without age check
            self.smart_renew_session_if_needed(
                session_id,
                check_renew=False  # Force immediate extension
            )

            # Update IP address if changed
            current_ip = get_client_ip(request)
            if existing_session.get('ip_address') != current_ip:
                try:
                    UserSession, _ = self._get_models()
                    UserSession.objects.filter(
                        session_id=session_id
                    ).update(ip_address=current_ip)
                    existing_session['ip_address'] = current_ip
                except Exception:
                    pass

            existing_session['reused'] = True
            return existing_session

        # No existing session - create new minimal session with persistent flag
        session_data = self.create_minimal_session_with_db(
            request, user_profile, persistent=persistent
        )
        session_data['reused'] = False
        return session_data


# Global session manager instance
session_manager = SessionManager()
