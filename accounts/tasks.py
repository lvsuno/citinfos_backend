from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Q, F, Avg
from django.db import transaction
from datetime import timedelta
from accounts.models import UserProfile, UserEvent, UserSession, BadgeDefinition, VerificationCode
from analytics.models import ErrorLog, SystemMetric
import logging
import random
import string

logger = logging.getLogger(__name__)


@shared_task
def end_expired_sessions():
    """Automatically end sessions that have passed their expiration time."""
    try:
        now = timezone.now()
        expired_sessions = UserSession.objects.filter(
            expires_at__lte=now,
            is_active=True,
            is_ended=False,
            is_deleted=False,
        )

        count = expired_sessions.count()
        if count > 0:
            logger.info(f"Found {count} expired sessions to end")

            # End each session individually to trigger mark_ended logic
            for session in expired_sessions:
                session.mark_ended(
                    reason="Session expired automatically",
                    from_cleanup=True
                )

            logger.info(f"Successfully ended {count} expired sessions")
        else:
            logger.debug("No expired sessions found")

    except Exception as e:
        logger.error(f"Error ending expired sessions: {str(e)}")
        ErrorLog.objects.create(
            level='error',
            message=f'Error ending expired sessions: {str(e)}',
            extra_data={
                'task': 'end_expired_sessions',
                'timestamp': timezone.now().isoformat()
            }
        )


@shared_task
def cleanup_ended_sessions():
    """Clean up old ended sessions from Redis to save memory."""
    try:
        from django.conf import settings
        import redis
        import json

        use_redis = getattr(settings, 'USE_REDIS_SESSIONS', False)
        if not use_redis:
            return

        redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        redis_client = redis.from_url(redis_url, decode_responses=True)

        # Get all session keys
        session_keys = redis_client.keys("session:*")
        cleaned_count = 0

        for key in session_keys:
            try:
                session_data = redis_client.get(key)
                if session_data:
                    data = json.loads(session_data)
                    # If session is ended and older than 24 hours, remove it
                    if (data.get('is_ended') and
                            'ended_at' in data):
                        ended_at = timezone.datetime.fromisoformat(
                            data['ended_at'].replace('Z', '+00:00')
                        )
                        # 24 hours = 86400 seconds
                        if (timezone.now() - ended_at).total_seconds() > 86400:
                            redis_client.delete(key)
                            cleaned_count += 1
            except Exception as e:
                logger.warning(f"Error processing session key {key}: {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old ended sessions from Redis")

    except Exception as e:
        logger.error(f"Error cleaning up ended sessions: {str(e)}")
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning up ended sessions: {str(e)}',
            extra_data={
                'task': 'cleanup_ended_sessions',
                'timestamp': timezone.now().isoformat()
            }
        )


@shared_task
def update_user_counters():
    """Update user counter fields like follower_count, following_count, posts_count"""
    from accounts.models import Follow
    from content.models import Post

    users = UserProfile.objects.all()

    for user in users:
        try:
            # Update follower count
            follower_count = Follow.objects.filter(followed=user).count()

            # Update following count
            following_count = Follow.objects.filter(follower=user).count()

            # Update posts count
            posts_count = Post.objects.filter(author=user).count()

            # Update the user profile
            user.follower_count = follower_count
            user.following_count = following_count
            user.posts_count = posts_count
            user.save(update_fields=[
                'follower_count', 'following_count', 'posts_count'
            ])

        except Exception as e:
            ErrorLog.objects.create(
                level='error',
                message=f'Error updating counters for user {user.id}: {str(e)}',
                extra_data={
                    'user_id': str(user.id),
                    'task': 'update_user_counters'
                }
            )

    return f"Updated counters for {users.count()} users"


@shared_task
def update_user_engagement_scores():
    """Update engagement scores for all users based on their activity"""
    from content.models import Like, Comment
    from content.utils import calculate_engagement_score

    users = UserProfile.objects.all()
    updated_count = 0

    for user in users:
        try:
            # Normalize to 0-1
            user.engagement_score = calculate_engagement_score(user)
            user.save(update_fields=['engagement_score'])
            updated_count += 1

        except Exception as e:
            ErrorLog.objects.create(
                level='error',
                message=f'Error updating engagement score for user {user.id}: {str(e)}',
                extra_data={'user_id': str(user.id), 'task': 'update_user_engagement_scores'}
            )

    return f"Updated engagement scores for {updated_count} users"


@shared_task
def cleanup_old_user_events():
    """Clean up old user events to maintain database performance"""
    try:
        # Keep security events for 1 year, others for 90 days
        security_cutoff = timezone.now() - timedelta(days=365)
        general_cutoff = timezone.now() - timedelta(days=90)

        # Delete old security events
        security_events = UserEvent.objects.filter(
            created_at__lt=security_cutoff,
            severity__in=['high', 'critical']
        )
        security_deleted = security_events.count()
        security_events.delete()

        # Delete old general events
        general_events = UserEvent.objects.filter(
            created_at__lt=general_cutoff
        ).exclude(severity__in=['high', 'critical'])
        general_deleted = general_events.count()
        general_events.delete()

        return f"Deleted {security_deleted} old security events and {general_deleted} general events"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning up user events: {str(e)}',
            extra_data={'task': 'cleanup_old_user_events'}
        )
        return f"Error cleaning up user events: {str(e)}"


@shared_task
def analyze_user_security_events():
    """Analyze security events and flag suspicious patterns"""
    try:
        # Analyze events from last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)

        # Find users with multiple failed login attempts
        failed_logins = UserEvent.objects.filter(
            event_type='login_failed',
            created_at__gte=last_24h
        ).values('user').annotate(
            count=Count('id')
        ).filter(count__gte=5)

        # Find suspicious location changes
        location_changes = UserEvent.objects.filter(
            event_type='location_change',
            created_at__gte=last_24h,
            severity='high'
        )

        # Flag events for review
        flagged_count = 0
        for event in location_changes:
            if not event.requires_review:
                event.requires_review = True
                event.save(update_fields=['requires_review'])
                flagged_count += 1

        # Create system metric
        SystemMetric.objects.create(
            metric_type='security_events_analyzed',
            value=UserEvent.objects.filter(
                created_at__gte=last_24h,
                severity__in=['high', 'critical']
            ).count(),
            additional_data={
                'failed_login_users': len(failed_logins),
                'flagged_events': flagged_count
            }
        )

        return f"Analyzed security events: {len(failed_logins)} users with failed logins, {flagged_count} events flagged"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error analyzing security events: {str(e)}',
            extra_data={'task': 'analyze_user_security_events'}
        )
        return f"Error analyzing security events: {str(e)}"


@shared_task
def update_user_session_analytics():
    """Update session analytics and metrics"""
    try:
        # Calculate active sessions
        active_sessions = UserSession.objects.filter(is_active=True).count()

        # Calculate average session duration for completed sessions
        last_24h = timezone.now() - timedelta(hours=24)
        completed_sessions = UserSession.objects.filter(
            ended_at__isnull=False,
            started_at__gte=last_24h
        )

        # Calculate duration manually since time_spent field is not available
        total_duration = timedelta()
        session_count = 0
        for session in completed_sessions:
            if session.ended_at and session.started_at:
                total_duration += (session.ended_at - session.started_at)
                session_count += 1

        avg_duration = total_duration / session_count if session_count > 0 else None


        # Update system metrics
        SystemMetric.objects.create(
            metric_type='active_sessions',
            value=active_sessions
        )

        if avg_duration:
            SystemMetric.objects.create(
                metric_type='avg_session_duration',
                value=avg_duration.total_seconds() / 60  # Convert to minutes
            )

        return f"Updated session analytics: {active_sessions} active sessions"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating session analytics: {str(e)}',
            extra_data={'task': 'update_user_session_analytics'}
        )
        return f"Error updating session analytics: {str(e)}"


@shared_task
def process_user_event_alerts():
    """Process high-priority user events and send alerts"""
    try:
        # Find events that need immediate attention
        critical_events = UserEvent.objects.filter(
            severity='critical',
            requires_review=True,
            reviewed_at__isnull=True,
            created_at__gte=timezone.now() - timedelta(hours=1)
        )

        alerts_sent = 0
        for event in critical_events:
            # In a real implementation, you would send alerts here
            # For now, just log the event
            ErrorLog.objects.create(
                level='warning',
                message=(
                    f'Critical user event detected: {event.event_type} '
                    f'for user {event.user.user.username}'
                ),
                extra_data={
                    'event_id': str(event.id),
                    'event_type': event.event_type,
                    'user_id': str(event.user.id),
                    'severity': event.severity
                }
            )
            alerts_sent += 1

        return f"Processed {alerts_sent} critical user event alerts"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error processing user event alerts: {str(e)}',
            extra_data={'task': 'process_user_event_alerts'}
        )
        return f"Error processing user event alerts: {str(e)}"


@shared_task
def generate_user_analytics_report():
    """Generate analytics report for user activity"""
    try:
        # Generate summary statistics
        total_users = UserProfile.objects.count()
        active_users_24h = UserSession.objects.filter(
            started_at__gte=timezone.now() - timedelta(hours=24)
        ).values('user').distinct().count()

        events_24h = UserEvent.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()

        security_events_24h = UserEvent.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24),
            severity__in=['high', 'critical']
        ).count()

        # Store analytics
        SystemMetric.objects.create(
            metric_type='daily_user_analytics',
            value=total_users,
            additional_data={
                'total_users': total_users,
                'active_users_24h': active_users_24h,
                'events_24h': events_24h,
                'security_events_24h': security_events_24h
            }
        )

        return {
            'total_users': total_users,
            'active_users_24h': active_users_24h,
            'events_24h': events_24h,
            'security_events_24h': security_events_24h,
            'message': 'User analytics report generated successfully'
        }

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error generating user analytics report: {str(e)}',
            extra_data={'task': 'generate_user_analytics_report'}
        )
        return f"Error generating analytics report: {str(e)}"


@shared_task
def deactivate_expired_users():
    """
    Set is_verified=False for users whose last_verified_at is older than VERIFICATION_VALID_DAYS.
    Only updates users who are currently verified and have expired.
    """
    import os
    allowed_days = int(os.environ.get('VERIFICATION_VALID_DAYS', 7))
    now = timezone.now()
    expired_users = UserProfile.objects.filter(
        is_verified=True,
        last_verified_at__isnull=False,
        last_verified_at__lt=now - timedelta(days=allowed_days)
    )
    count = expired_users.update(is_verified=False)
    return f"Deactivated {count} expired users."


@shared_task
def evaluate_all_badges_periodic():
    """
    Periodic task: evaluate all badge definitions for all user profiles using
    the enhanced badge evaluation system with environment-based thresholds.
    Returns comprehensive statistics about badge awards.
    """
    try:
        from accounts.badge_evaluator import badge_evaluator

        # Initialize/update badge definitions from environment
        stats = badge_evaluator.evaluate_all_users(batch_size=100)

        # Store metrics
        SystemMetric.objects.create(
            metric_type='badge_evaluation_run',
            value=stats['total_badges_awarded'],
            additional_data={
                'scope': 'all',
                'users_processed': stats['users_processed'],
                'errors': stats['errors'],
                'batch_size': 100,
                'evaluation_type': 'periodic_comprehensive'
            }
        )

        return (f"Badge evaluation complete: {stats['total_badges_awarded']} "
                f"badges awarded to {stats['users_processed']} users "
                f"({stats['errors']} errors)")

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error in evaluate_all_badges_periodic: {e}',
            extra_data={'task': 'evaluate_all_badges_periodic'}
        )
        return f"Error evaluating badges: {e}"


@shared_task
def evaluate_badges_for_profile_task(profile_id: str):
    """
    Evaluate badges for a single profile using the enhanced evaluation system.
    Triggered after user actions like post creation, follow, etc.

    Args:
        profile_id: UUID string of the UserProfile to evaluate

    Returns:
        String describing the evaluation result
    """
    try:
        from accounts.badge_evaluator import badge_evaluator

        profile = UserProfile.objects.get(id=profile_id)
        awarded_count, new_badges = badge_evaluator.evaluate_user_badges(profile)

        # Log the evaluation event
        UserEvent.objects.create(
            user=profile,
            event_type='badge_evaluation',
            description=f'Badge evaluation completed: {awarded_count} new badges',
            severity='info',
            metadata={
                'awarded_count': awarded_count,
                'new_badges': new_badges,
                'evaluation_trigger': 'individual_task'
            }
        )

        if awarded_count > 0:
            return (f"Profile {profile_id}: {awarded_count} new badges awarded: "
                   f"{', '.join(new_badges)}")
        else:
            return f"Profile {profile_id}: No new badges awarded"

    except UserProfile.DoesNotExist:
        return f"Profile {profile_id} not found"
    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error evaluating badges for profile {profile_id}: {e}',
            extra_data={
                'task': 'evaluate_badges_for_profile_task',
                'profile_id': str(profile_id)
            }
        )
        return f"Error: {e}"


@shared_task
def initialize_badge_definitions():
    """
    Initialize or update badge definitions in the database based on current
    environment variable thresholds. Run this when thresholds change.
    """
    try:
        from accounts.badge_evaluator import badge_evaluator

        # This will initialize/update all badge definitions
        badge_evaluator._initialize_badge_definitions()

        # Count active badges
        active_badges = BadgeDefinition.objects.filter(
            is_active=True,
            is_deleted=False
        ).count()

        SystemMetric.objects.create(
            metric_type='badge_definitions_initialized',
            value=active_badges,
            additional_data={
                'task': 'initialize_badge_definitions',
                'timestamp': timezone.now().isoformat()
            }
        )

        return f"Badge definitions initialized: {active_badges} active badges"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error initializing badge definitions: {e}',
            extra_data={'task': 'initialize_badge_definitions'}
        )
        return f"Error initializing badge definitions: {e}"


@shared_task
def evaluate_badges_by_trigger(trigger_type: str, user_id: str = None):
    """
    Evaluate badges based on specific trigger events.
    More efficient than full evaluation when we know what changed.

    Args:
        trigger_type: Type of event that triggered evaluation
                     (post_created, follow_made, comment_made, etc.)
        user_id: UserProfile UUID to evaluate (optional, if None evaluates all)
    """
    try:
        from accounts.badge_evaluator import badge_evaluator

        if user_id:
            # Evaluate specific user
            profile = UserProfile.objects.get(id=user_id)
            awarded_count, new_badges = badge_evaluator.evaluate_user_badges(profile)

            if awarded_count > 0:
                # Log the trigger event
                UserEvent.objects.create(
                    user=profile,
                    event_type='badge_earned_trigger',
                    description=f'Trigger "{trigger_type}" resulted in {awarded_count} new badges',
                    severity='info',
                    metadata={
                        'trigger_type': trigger_type,
                        'awarded_count': awarded_count,
                        'new_badges': new_badges
                    }
                )

            return f"Trigger '{trigger_type}' for user {user_id}: {awarded_count} badges awarded"
        else:
            # Evaluate all users (use with caution)
            stats = badge_evaluator.evaluate_all_users(batch_size=50)
            return f"Trigger '{trigger_type}' for all users: {stats['total_badges_awarded']} badges awarded"

    except UserProfile.DoesNotExist:
        return f"User profile {user_id} not found"
    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error in evaluate_badges_by_trigger: {e}',
            extra_data={
                'task': 'evaluate_badges_by_trigger',
                'trigger_type': trigger_type,
                'user_id': user_id
            }
        )
        return f"Error: {e}"


@shared_task
def cleanup_expired_verification_codes():
    """
    Automatic cleanup of expired verification codes via Celery.
    Runs daily to remove codes older than 7 days.
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=7)

        # Get expired codes for logging
        expired_codes = VerificationCode.objects.filter(
            expires_at__lt=cutoff_date
        )

        total_count = expired_codes.count()

        if total_count == 0:
            return "No expired verification codes to cleanup"

        # Log codes before deletion for audit
        for code in expired_codes:
            logger.info(
                f'HARD DELETE verification code: {code.id} '
                f'for user {code.user.user.username}, '
                f'expired: {code.expires_at}, used: {code.is_used}'
            )

        # Perform hard deletion
        deleted_count = expired_codes.delete()[0]

        # Log cleanup event
        SystemMetric.objects.create(
            metric_type='verification_codes_cleaned',
            value=deleted_count,
            additional_data={
                'cleanup_date': timezone.now().isoformat(),
                'days_cutoff': 7
            }
        )

        return f"Successfully cleaned up {deleted_count} expired verification codes"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning up verification codes: {str(e)}',
            extra_data={'task': 'cleanup_expired_verification_codes'}
        )
        return f"Error cleaning up verification codes: {str(e)}"


@shared_task
def generate_verification_code_for_user(user_profile_id):
    """
    Generate a new verification code for a user whose verification expired.
    Called when user login is blocked due to expired verification.
    """
    try:
        user_profile = UserProfile.objects.get(id=user_profile_id)

        # Delete any existing verification code for this user
        VerificationCode.objects.filter(user=user_profile).delete()

        # Generate new unique 8-character alphanumeric code (uppercase)
        charset = string.ascii_uppercase + string.digits
        print(f"🔥 TASK: Using charset: {charset}")
        print(f"🔥 TASK: Charset length: {len(charset)}")

        while True:
            code = ''.join(random.choices(charset, k=8))
            print(f"🔥 TASK: Generated code: {code}")
            print(f"🔥 TASK: Code is numeric: {code.isdigit()}")
            if not VerificationCode.objects.filter(code=code).exists():
                break

        # Create new verification code
        verification_code = VerificationCode.objects.create(
            user=user_profile,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=5)
        )

        # Log the code generation event
        UserEvent.objects.create(
            user=user_profile,
            event_type='verification_code_generated',
            description='New verification code generated due to expired verification',
            severity='info',
            metadata={
                'reason': 'expired_verification',
                'code_id': str(verification_code.id)
            }
        )

        # Send verification code via email using your NotificationService
        from notifications.utils import NotificationService

        NotificationService.send_email_notification(
            recipient=user_profile,
            subject='Account Re-verification Required - Security Check',
            template='accounts/email/reverification_email.html',
            context={
                'code': code,
                'user': user_profile.user,
                'expires_at': verification_code.expires_at,
                'reason': 'Re-verification required for security.'
            }
        )

        return {
            'success': True,
            'code_id': str(verification_code.id),
            'user_id': str(user_profile_id),
            'message': f'Verification code generated for {user_profile.user.username}'
        }

    except UserProfile.DoesNotExist:
        return {
            'success': False,
            'error': f'UserProfile {user_profile_id} not found'
        }
    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error generating verification code: {str(e)}',
            extra_data={
                'task': 'generate_verification_code_for_user',
                'user_profile_id': str(user_profile_id)
            }
        )
        return {
            'success': False,
            'error': str(e)
        }
