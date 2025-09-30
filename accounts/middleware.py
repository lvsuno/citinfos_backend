"""
Middleware for updating user activity tracking and badge evaluation.
"""

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth import logout
from accounts.models import UserProfile


class UpdateLastActiveMiddleware(MiddlewareMixin):
    """
    Middleware to update UserProfile.last_active on every authenticated request
    and trigger daily login event tracking for badges.

    This middleware will update the last_active timestamp for authenticated users
    on every request they make to track user activity and log login events.
    """

    def process_response(self, request, response):
        """
        Update last_active field for authenticated users after view processing.

        This runs after the view has processed, so JWT authentication should
        have already set request.user.
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                profile = getattr(request.user, 'profile', None)
                if profile:
                    now = timezone.now()

                    # Only update if more than 60 seconds have passed since last update
                    # This reduces database writes while maintaining activity tracking
                    time_diff = (now - profile.last_active).total_seconds()
                    should_update = not profile.last_active or time_diff > 60

                    if should_update:
                        UserProfile.objects.filter(id=profile.id).update(
                            last_active=now
                        )

                        # Check if this is a new day (for daily login tracking)
                        last_active_date = profile.last_active.date() if profile.last_active else None
                        current_date = now.date()

                        if not last_active_date or last_active_date != current_date:
                            # Log daily login event for badge tracking
                            self._log_daily_login(request.user)

            except AttributeError:
                # Handle case where profile doesn't exist gracefully
                pass

        return response

    def process_request(self, request):
        """
        Block requests from authenticated users whose UserProfile is soft-deleted.

        Runs after Django AuthenticationMiddleware (so request.user is set). If a
        soft-deleted profile is detected, invalidate server session (if any),
        log the user out and return a 401 JSON response to stop further handling.
        """
        try:
            if hasattr(request, 'user') and request.user.is_authenticated:
                # support both user.userprofile and user.profile accessors
                profile = getattr(request.user, 'userprofile', None) or getattr(request.user, 'profile', None)
                if profile and getattr(profile, 'is_deleted', False):
                    # Invalidate hybrid session if session manager available
                    try:
                        from core.session_manager import session_manager
                        sid = request.session.session_key if hasattr(request, 'session') else None
                        if sid:
                            session_manager.invalidate_session(sid)
                    except Exception:
                        # don't fail request handling if session manager isn't available
                        pass

                    # Ensure Django logout and block access
                    try:
                        logout(request)
                    except Exception:
                        pass

                    return JsonResponse({'detail': 'User profile has been deleted'}, status=401)
        except Exception:
            # Be defensive: any unexpected error here shouldn't break requests
            pass

        return None

    def _log_daily_login(self, user):
        """Log a daily login event for badge tracking."""
        try:
            from .models import UserEvent

            # Use transaction.on_commit to ensure this runs after the main request
            transaction.on_commit(
                lambda: UserEvent.objects.create(
                    user=user,
                    event_type='DAILY_LOGIN',
                    metadata={'date': timezone.now().date().isoformat()}
                )
            )
        except Exception:
            # Fail silently to not break the main functionality
            pass
