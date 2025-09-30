"""
Async task implementations for accounts app to optimize user experience.
This module contains Celery tasks for handling time-consuming operations
asynchronously to reduce user waiting time.
"""
from datetime import timedelta
import logging
from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from typing import Any, Dict


logger = logging.getLogger('accounts.tasks')

@shared_task(bind=True, max_retries=3)
def send_password_reset_email_async(self, user_profile_id: str, reset_token: str) -> Dict[str, Any]:
    """
    Send password reset email asynchronously.

    Args:
        user_profile_id: UUID string of UserProfile
        reset_token: Password reset token

    Returns:
        Success message string
    """
    try:
        from accounts.models import UserProfile
        from notifications.utils import NotificationService
        from django.conf import settings

        profile = UserProfile.objects.get(id=user_profile_id, is_deleted=False)
        frontend_domain = getattr(settings, 'FRONTEND_DOMAIN', 'http://localhost:3000')
        reset_url = f"{frontend_domain}/reset-password/{reset_token}"
        success = NotificationService.send_email_notification(
            recipient=profile,
            subject='Password Reset Request',
            template='accounts/email/password_reset_email.html',
            context={
                'user': profile.user,
                'reset_url': reset_url,
                'expires_at': 5
            }
        )

        if success:
            logger.info(f"Password reset email sent to {profile.user.email}")
            return f"Password reset email sent to {profile.user.email}"
        else:
            raise Exception(f"Email sending failed for {profile.user.email}")

    except ObjectDoesNotExist:
        logger.error(f"UserProfile not found: {user_profile_id}")
        return {"error": f"UserProfile {user_profile_id} not found"}

    except Exception as exc:
        retries = getattr(self.request, "retries", 0)
        logger.warning(
            "Password reset email check failed (attempt %d): %s",
            retries + 1,
            exc
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))
        else:
            # Final attempt failed, return error status
            return {
                "error": f"Password reset email failed: {str(exc)}",
                "is_reset": False,
                "reset_time_expired": True
            }

@shared_task
def enhance_session_async(session_id: str, request_meta: dict):
    """
    Enhance session with full device info and location data asynchronously.
    This allows fast login while building comprehensive session data in background.

    Args:
        session_id: Session ID to enhance
        request_meta: Request META dictionary with headers and client info

    Returns:
        Enhanced session data
    """
    try:
        from core.session_manager import session_manager
        from core.utils import get_location_from_ip, get_device_info
        import json

        # Get current session data
        session_data = session_manager.get_session(session_id)
        if not session_data:
            logger.warning(f"Session {session_id} not found for enhancement")
            return None

        # Extract IP and get location data
        ip_address = (
            request_meta.get('HTTP_CF_CONNECTING_IP') or
            request_meta.get('HTTP_X_REAL_IP') or
            request_meta.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or
            request_meta.get('REMOTE_ADDR')
        )

        if ip_address:
            location_data = get_location_from_ip(ip_address)
            session_data['location_data'] = location_data
            session_data['ip_address'] = ip_address

        # OPTIMIZATION: Enhanced device fingerprint calculation
        # Work directly with available data instead of creating mock objects
        try:
            # Get client device info from session data
            client_device_info = session_data.get('client_device_info', {})

            # Generate enhanced fingerprint using direct data approach
            if client_device_info.get('client_fingerprint'):
                # Use client-provided fingerprint + server validation
                client_fp = client_device_info['client_fingerprint']
                ip_address = session_data.get('ip_address', '')
                user_agent = request_meta.get('HTTP_USER_AGENT', '')

                # Create secure combined fingerprint
                import hashlib
                secure_components = [client_fp, ip_address, user_agent[:50]]
                combined = '|'.join(str(comp) for comp in secure_components if comp)
                enhanced_fingerprint = hashlib.sha256(combined.encode('utf-8')).hexdigest()
            else:
                # Fallback: Generate fingerprint from available client data
                fingerprint_components = [
                    request_meta.get('HTTP_USER_AGENT', ''),
                    str(client_device_info.get('screen_resolution', '')),
                    str(client_device_info.get('timezone', '')),
                    str(client_device_info.get('platform', '')),
                    str(client_device_info.get('canvas_fingerprint', '')),
                    str(client_device_info.get('webgl_vendor', '')),
                ]

                import hashlib
                combined = '|'.join(comp for comp in fingerprint_components if comp)
                enhanced_fingerprint = hashlib.sha256(combined.encode('utf-8')).hexdigest()

            session_data['device_fingerprint'] = enhanced_fingerprint
            session_data['client_device_info'] = client_device_info
            session_data['user_agent'] = request_meta.get('HTTP_USER_AGENT', '')

        except Exception as e:
            logger.warning(f"Enhanced fingerprint generation failed: {e}")
            # Fallback to basic user agent
            session_data['user_agent'] = request_meta.get('HTTP_USER_AGENT', '')

        # Update session in Redis and Database
        if session_manager.use_redis:
            redis_key = f"session:{session_id}"
            session_manager.redis_client.setex(
                redis_key,
                session_manager.SESSION_DURATION_SECONDS,
                json.dumps(session_data, default=str)
            )

        # Update database session record
        from accounts.models import UserSession
        UserSession.objects.filter(
            session_id=session_id, is_active=True
        ).update(
            location_data=session_data.get('location_data', {}),
            device_info=session_data.get('detailed_device_info', {})
        )

        logger.info(f"Session {session_id} enhanced with location and device data")
        return session_data

    except Exception as exc:
        logger.error(f"Session enhancement failed for {session_id}: {exc}")
        return None


@shared_task(bind=True, max_retries=2)
def enhance_device_fingerprint_async(self, session_id: str, client_fingerprint_data: dict):
    """
    Enhanced device fingerprint processing in background.

    Combines server-side and client-side fingerprint data for
    improved security and device tracking accuracy.

    Args:
        session_id: Session identifier
        client_fingerprint_data: Client-side fingerprint data
    """
    try:
        from core.session_manager import session_manager
        from core.device_fingerprint import OptimizedDeviceFingerprint

        # Get current session data
        session_data = session_manager.get_session(session_id)
        if not session_data:
            logger.warning(f"Session {session_id} not found for fingerprint enhancement")
            return None

        # Cache client fingerprint data
        OptimizedDeviceFingerprint.cache_client_fingerprint(
            session_id, client_fingerprint_data
        )

        # Get server-side device info if available
        merged_device_info = session_data.get('device_info', {})

        # Create enhanced fingerprint from client + server data
        from django.test.client import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_USER_AGENT'] = session_data.get('user_agent', '')

        enhanced_fingerprint = OptimizedDeviceFingerprint.get_enhanced_fingerprint(
            request, client_fingerprint_data, merged_device_info
        )

        # Merge with existing fast fingerprint
        current_fingerprint = session_data.get('device_fingerprint', '')
        confidence_score = client_fingerprint_data.get('confidence', 0.8)

        final_fingerprint = OptimizedDeviceFingerprint.merge_fingerprints(
            current_fingerprint, enhanced_fingerprint, confidence_score
        )

        # Update session with enhanced fingerprint
        session_data['device_fingerprint'] = final_fingerprint
        session_data['client_fingerprint_data'] = client_fingerprint_data
        session_data['fingerprint_enhanced'] = True

        # Update Redis cache
        if session_manager.use_redis:
            import json
            redis_key = f"session:{session_id}"
            session_manager.redis_client.setex(
                redis_key,
                SESSION_DURATION_SECONDS,
                json.dumps(session_data, default=str)
            )

        # Update database
        try:
            from accounts.models import UserSession
            user_session = UserSession.objects.get(session_id=session_id)
            user_session.device_fingerprint = final_fingerprint
            user_session.device_info.update({
                'client_fingerprint': client_fingerprint_data,
                'fingerprint_enhanced': True
            })
            user_session.save(update_fields=['device_fingerprint', 'device_info'])

            logger.info(f"Enhanced fingerprint for session {session_id}")
            return final_fingerprint

        except UserSession.DoesNotExist:
            logger.warning(f"UserSession {session_id} not found in database")
            return final_fingerprint

    except Exception as exc:
        logger.error(f"Fingerprint enhancement failed for {session_id}: {exc}")
        # Don't retry on client data issues
        if 'client_fingerprint_data' in str(exc) or 'confidence' in str(exc):
            return None
        # Retry on network/database issues
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def assign_registration_index_async(user_profile_id: str):
    """
    Assign registration index asynchronously to avoid slowing down registration.

    Args:
        user_profile_id: UUID string of UserProfile

    Returns:
        Success message with assigned index
    """
    try:
        from accounts.models import UserProfile
        from django.db import transaction

        profile = UserProfile.objects.get(id=user_profile_id, is_deleted=False)

        # Only assign if not already assigned
        if profile.registration_index == 0:
            with transaction.atomic():
                profile.assign_registration_index()

        logger.info(f"Registration index {profile.registration_index} assigned to {profile.user.username}")
        return f"Registration index {profile.registration_index} assigned successfully"

    except ObjectDoesNotExist:
        logger.error(f"UserProfile not found: {user_profile_id}")
        return f"UserProfile {user_profile_id} not found"

    except Exception as exc:
        logger.error(f"Registration index assignment failed: {exc}")
        return f"Failed to assign registration index: {exc}"


@shared_task
def assign_index_and_evaluate_early_adopter_async(user_profile_id: str):
    """
    Combined task: Assign registration index AND evaluate early adopter badge.

    This task runs when a user completes verification, ensuring proper order:
    1. Assign registration index based on verification order
    2. Evaluate early adopter badge based on registration index

    Args:
        user_profile_id: UUID string of UserProfile

    Returns:
        Success message with index and badge info
    """
    try:
        from accounts.models import UserProfile
        from django.db import transaction

        profile = UserProfile.objects.get(id=user_profile_id, is_deleted=False)

        # Step 1: Assign registration index if not already assigned
        if profile.registration_index == 0:
            with transaction.atomic():
                # Use model method which handles MySQL optimization correctly
                profile.assign_registration_index()
                # Refresh to ensure we have the updated value
                profile.refresh_from_db(fields=['registration_index'])

        # Step 2: Evaluate early adopter badge if qualified
        if profile.registration_index <= 1000:
            try:
                from accounts.badge_triggers import trigger_badge_evaluation
                task_result = trigger_badge_evaluation(
                    profile,
                    'early_adopter_registration',
                    async_evaluation=True,
                    delay_seconds=2  # Quick evaluation after index assignment
                )
                badge_result = (
                    f"Early adopter evaluation queued (task: {task_result})"
                )
            except Exception as e:
                badge_result = f"Badge evaluation failed: {e}"
        else:
            badge_result = "Not eligible for early adopter badge"

        logger.info(
            f"Registration index {profile.registration_index} assigned "
            f"to {profile.user.username}"
        )
        return {
            'success': True,
            'user_id': str(profile.id),
            'username': profile.user.username,
            'registration_index': profile.registration_index,
            'badge_evaluation': badge_result
        }

    except ObjectDoesNotExist:
        logger.error(f"UserProfile not found: {user_profile_id}")
        return {
            'success': False,
            'error': f"UserProfile {user_profile_id} not found"
        }

    except Exception as exc:
        logger.error(f"Combined index+badge assignment failed: {exc}")
        return {
            'success': False,
            'error': f"Failed to assign index and evaluate badge: {exc}"
        }
