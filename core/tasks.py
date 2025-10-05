"""
Core async tasks for performance optimization.
Handles location caching, session enhancement, and other background operations.
"""

from celery import shared_task
from django.core.cache import cache
import logging
import json

logger = logging.getLogger('core.tasks')


@shared_task
def enhance_session_async(session_id: str, request_data: dict, client_device_info: dict):
    """
    Enhance session with full device info and location data asynchronously.
    This allows fast login while building comprehensive session data in background.

    Args:
        session_id: Session ID to enhance
        request_data: Dict containing extracted request data (IP, headers, etc.)
        client_device_info: Dict containing client-side device fingerprint data

    Returns:
        Enhanced session data or error message
    """
    # Add comprehensive debugging
    logger.info(f"🚀 TASK START: enhance_session_async called for session {session_id[:10]}...")
    logger.info(f"📥 Request data keys: {list(request_data.keys()) if request_data else 'None'}")
    logger.info(f"📱 Client device info keys: {list(client_device_info.keys()) if client_device_info else 'None'}")

    try:
        logger.info("📦 Importing required modules...")
        from core.session_manager import (
            session_manager,
            SESSION_DURATION_SECONDS
        )
        from core.ip_location_service import FastLocationService
        from core.device_fingerprint import OptimizedDeviceFingerprint
        logger.info("✅ Module imports successful")

        # Get current session data
        logger.info(f"🔍 Looking up session data for {session_id[:10]}...")
        session_data = session_manager.get_session(session_id)

        if not session_data:
            logger.error(f"❌ Session {session_id[:10]}... not found for enhancement")
            return {"error": f"Session {session_id} not found"}

        logger.info(f"✅ Found session data with keys: {list(session_data.keys())}")

        # Extract data components from the serialized request_data
        server_device_info = request_data.get('device_info', {})
        ip_address = request_data.get('ip_address', '')
        logger.info(f"🌐 Processing IP: {ip_address}")
        logger.info(f"🖥️ Server device info keys: {list(server_device_info.keys())}")

        # Add request headers to server device info
        server_device_info.update({
        #    'ip_address': ip_address,
            'accept': request_data.get('accept', ''),
            'accept_lang': request_data.get('accept_lang', ''),
            'accept_encoding': request_data.get('accept_encoding', ''),
            'accept_charset': request_data.get('accept_charset', ''),
            'dnt': request_data.get('dnt', ''),
            'connection': request_data.get('connection', ''),
            'cache_control': request_data.get('cache_control', ''),
            'pragma': request_data.get('pragma', ''),
            'sec_fetch_dest': request_data.get('sec_fetch_dest', ''),
            'sec_fetch_mode': request_data.get('sec_fetch_mode', ''),
            'sec_fetch_site': request_data.get('sec_fetch_site', ''),
            'sec_fetch_user': request_data.get('sec_fetch_user', ''),
            'upgrade_insecure': request_data.get('upgrade_insecure', ''),
        })

        enhanced_session_data = {}

        # 1. Enhanced Device Fingerprint Generation
        if client_device_info or server_device_info:
            try:

                # Generate enhanced fingerprint with all available data
                final_fingerprint = OptimizedDeviceFingerprint.get_enhanced_fingerprint(
                    client_device_info, server_device_info
                )

                enhanced_session_data['device_fingerprint'] = final_fingerprint
                enhanced_session_data['client_fingerprint_data'] = client_device_info
                enhanced_session_data['server_device_info'] = server_device_info
                enhanced_session_data['fingerprint_enhanced'] = True

                logger.info(f"Enhanced fingerprint generated for session {session_id}")

            except Exception as e:
                logger.warning(f"Fingerprint enhancement failed for {session_id}: {e}")

        # 2. Location Data Enhancement
        if ip_address:
            try:
                # Use blocking location lookup since this is async anyway
                location_data = FastLocationService.get_location_blocking(
                    ip_address
                )
                if location_data:
                    enhanced_session_data['location_data'] = location_data
                    enhanced_session_data['enhanced_ip_address'] = ip_address

                    # Resolve to database objects for geo-restrictions
                    from core.location_db_cache import location_cache_service
                    resolved_location = location_cache_service.resolve_location_from_ip_data(
                        location_data
                    )
                    # Use the complete resolved location data structure
                    location_data = resolved_location
                    enhanced_session_data['resolved_location'] = location_data

                    logger.info(f"Location data enhanced for session {session_id}")
                else:
                    logger.debug(f"No cached location data for IP {ip_address}")

            except Exception as e:
                logger.warning(f"Location enhancement failed for {session_id}: {e}")

        # 3. Update Session Data
        if enhanced_session_data:
            try:
                # Update session in both Redis and Database
                session_data.update(enhanced_session_data)

                # Update Redis
                if session_manager.use_redis:
                    redis_key = f"session:{session_id}"
                    session_manager.redis_client.setex(
                        redis_key,
                        SESSION_DURATION_SECONDS,
                        json.dumps(session_data, default=str)
                    )

                # Update Database
                UserSession, _ = session_manager._get_models()
                db_updates = {}

                if 'device_fingerprint' in enhanced_session_data:
                    db_updates['device_fingerprint'] = enhanced_session_data['device_fingerprint']

                if 'location_data' in enhanced_session_data:
                    db_updates['location_data'] = enhanced_session_data['location_data']

                if 'enhanced_ip_address' in enhanced_session_data:
                    db_updates['ip_address'] = enhanced_session_data['enhanced_ip_address']

                db_updates['device_info'] = request_data.get('device_info', {})

                if db_updates:
                    UserSession.objects.filter(session_id=session_id).update(**db_updates)
                    logger.info(f"Database updated for session {session_id}")

                # Track session creation analytics with all the enhanced data
                logger.info("📊 Starting analytics tracking...")
                try:
                    from analytics.tasks import track_session_comprehensive
                    from django.utils import timezone

                    # Get user information from session
                    userprofile_id = session_data.get('user_id')
                    django_user_id = None
                    logger.info(f"👤 UserProfile ID from session: {userprofile_id}")

                    if userprofile_id:
                        # Get Django User ID from UserProfile ID for analytics
                        try:
                            from accounts.models import UserProfile
                            user_profile = UserProfile.objects.get(id=userprofile_id)
                            django_user_id = user_profile.user.id
                            logger.info(f"🔄 Converted to Django User ID: {django_user_id}")
                        except UserProfile.DoesNotExist:
                            logger.warning(f"⚠️ UserProfile {userprofile_id} not found")
                            django_user_id = None

                    if django_user_id:
                        analytics_data = {
                            'session_id': session_id,
                            'user_id': django_user_id,
                            'event_type': 'created',
                            'creation_time_ms': session_data.get(
                                'creation_time_ms', 0.0
                            ),
                            'ip_address': enhanced_session_data.get(
                                'enhanced_ip_address'
                            ),
                            'user_agent': server_device_info.get(
                                'user_agent', ''
                            ),
                            'location_data': enhanced_session_data.get(
                                'location_data', {}
                            ),
                            'additional_metadata': {
                                'device_fingerprint': (
                                    enhanced_session_data.get(
                                        'device_fingerprint'
                                    )
                                ),
                                'server_device_info': server_device_info,
                                'client_device_info': client_device_info,
                                'resolved_location': enhanced_session_data.get(
                                    'resolved_location', {}
                                ),
                                'enhancement_timestamp': (
                                    timezone.now().isoformat()
                                )
                            }
                        }

                        logger.info(f"📈 Analytics data keys: {list(analytics_data.keys())}")
                        logger.info(f"📊 Calling track_session_comprehensive...")

                        # Track session creation synchronously
                        # (we're already in async context)
                        result = track_session_comprehensive(analytics_data)
                        logger.info(f"✅ Analytics tracking result: {result}")

                    else:
                        logger.warning("⚠️ No userprofile_id in session data, skipping analytics")

                except Exception as e:
                    logger.error(f"❌ Failed to track session creation analytics: {e}")
                    import traceback
                    logger.error(f"Analytics error traceback: {traceback.format_exc()}")

                logger.info(f"Session {session_id} enhanced successfully")
                return {"status": "enhanced", "session_id": session_id}

            except Exception as e:
                logger.error(f"Failed to update session {session_id}: {e}")
                return {"error": f"Update failed: {e}"}
        else:
            logger.info(f"No enhancements needed for session {session_id}")
            return {"status": "no_changes", "session_id": session_id}

    except Exception as e:
        logger.error(f"Session enhancement failed for {session_id}: {e}")

        # CRITICAL: End the session when enhancement fails
        # This prevents orphaned sessions that remain active after failed creation
        try:
            from accounts.models import UserSession

            session = UserSession.objects.filter(session_id=session_id).first()
            if session and session.is_active:
                session.mark_ended(
                    reason=f"enhancement_failed: {str(e)[:100]}",
                    from_cleanup=False
                )
                logger.warning(f"Session {session_id} ended due to enhancement failure")
            else:
                logger.warning(f"Session {session_id} not found or already ended")

        except Exception as cleanup_error:
            logger.error(f"Failed to end session {session_id} after enhancement failure: {cleanup_error}")

        return {"error": f"Enhancement failed: {e}"}


def preload_location_cache_for_session(session_id: str, location_data: dict):
    """
    Preload location cache for a session to enable fast lookups.

    Args:
        session_id: Session identifier
        location_data: Location data to cache

    Returns:
        Success status
    """
    try:
        from core.ip_location_service import fast_location_service

        fast_location_service.preload_session_location_cache(session_id, location_data)

        logger.debug(f"Location cache preloaded for session {session_id}")
        return {
            "session_id": session_id,
            "preloaded": True
        }

    except Exception as exc:
        logger.error(f"Failed to preload location cache for session {session_id}: {exc}")
        return {
            "session_id": session_id,
            "error": str(exc),
            "preloaded": False
        }


@shared_task
def warm_up_location_cache(ip_addresses: list):
    """
    Warm up location cache with frequently accessed IP addresses.
    Useful for pre-populating cache during low-traffic periods.

    Args:
        ip_addresses: List of IP addresses to warm up

    Returns:
        Warmup statistics
    """
    try:
        from core.ip_location_service import fast_location_service

        logger.info(f"Starting location cache warmup for {len(ip_addresses)} IPs")

        fast_location_service.warm_up_common_locations(ip_addresses)

        return {
            "total_ips": len(ip_addresses),
            "warmup_initiated": True
        }

    except Exception as exc:
        logger.error(f"Location cache warmup failed: {exc}")
        return {
            "total_ips": len(ip_addresses) if ip_addresses else 0,
            "error": str(exc),
            "warmup_initiated": False
        }


@shared_task
def batch_location_lookup(ip_addresses: list, priority: str = 'normal'):
    """
    Perform batch location lookups for multiple IP addresses.
    Useful for processing analytics data or warming up cache.

    Args:
        ip_addresses: List of IP addresses to lookup
        priority: Priority level ('high', 'normal', 'low')

    Returns:
        Batch lookup results
    """
    try:
        from core.utils import get_location_from_ip
        from core.ip_location_service import fast_location_service

        results = {}
        successful_lookups = 0
        failed_lookups = 0

        logger.info(f"Starting batch location lookup for {len(ip_addresses)} IPs (priority: {priority})")

        for ip_address in ip_addresses:
            try:
                # Skip if already cached
                cache_key = f"location:{ip_address}"
                if cache.get(cache_key):
                    results[ip_address] = {"status": "already_cached"}
                    continue

                # Perform lookup
                location_data = get_location_from_ip(ip_address)

                if location_data:
                    # Cache the result
                    fast_location_service._cache_location_data(ip_address, location_data)
                    results[ip_address] = {
                        "status": "success",
                        "location": location_data
                    }
                    successful_lookups += 1
                else:
                    # Cache empty result
                    cache.set(cache_key, {}, 3600)  # 1 hour
                    results[ip_address] = {"status": "no_data"}

            except Exception as ip_exc:
                logger.warning(f"Location lookup failed for {ip_address}: {ip_exc}")
                results[ip_address] = {
                    "status": "error",
                    "error": str(ip_exc)
                }
                failed_lookups += 1

        logger.info(
            f"Batch location lookup completed: {successful_lookups} successful, "
            f"{failed_lookups} failed"
        )

        return {
            "total_ips": len(ip_addresses),
            "successful_lookups": successful_lookups,
            "failed_lookups": failed_lookups,
            "results": results
        }

    except Exception as exc:
        logger.error(f"Batch location lookup failed: {exc}")
        return {
            "error": str(exc),
            "success": False
        }
