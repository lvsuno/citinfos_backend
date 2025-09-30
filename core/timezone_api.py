"""
API endpoint for updating session timezone information.

This module provides endpoints for frontend timezone detection integration.
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .session_manager import session_manager
from .timezone_utils import normalize_timezone

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class UpdateSessionTimezoneView(View):
    """API endpoint to update user's timezone in current session."""

    def post(self, request):
        """Update session timezone from frontend detection."""
        try:
            # Parse request data
            data = json.loads(request.body)
            user_timezone = data.get('timezone')

            if not user_timezone:
                return JsonResponse({
                    'error': 'timezone_required',
                    'message': 'Timezone parameter is required'
                }, status=400)

            # Validate and normalize timezone
            try:
                normalized_timezone = normalize_timezone(user_timezone)
                if not normalized_timezone:
                    return JsonResponse({
                        'error': 'invalid_timezone',
                        'message': f'Invalid timezone: {user_timezone}'
                    }, status=400)
            except Exception as e:
                logger.warning(f"Timezone validation error: {e}")
                return JsonResponse({
                    'error': 'timezone_validation_error',
                    'message': 'Failed to validate timezone'
                }, status=400)

            # Update session with timezone information
            session_key = request.session.session_key
            if not session_key:
                return JsonResponse({
                    'error': 'no_session',
                    'message': 'No active session found'
                }, status=400)

            # Get current session data
            session_data = session_manager.get_session(session_key)
            if not session_data:
                return JsonResponse({
                    'error': 'session_not_found',
                    'message': 'Session not found in storage'
                }, status=404)

            # Update location data with timezone
            location_data = session_data.get('location_data', {})
            location_data['timezone'] = normalized_timezone
            location_data['timezone_updated_at'] = session_manager._get_current_timestamp()

            # Update session
            session_data['location_data'] = location_data

            # Save updated session data
            success = session_manager._store_session_data(session_key, session_data)

            if success:
                logger.info(f"Updated session timezone for user {request.user.id} to {normalized_timezone}")
                return JsonResponse({
                    'success': True,
                    'message': 'Timezone updated successfully',
                    'timezone': normalized_timezone
                })
            else:
                return JsonResponse({
                    'error': 'update_failed',
                    'message': 'Failed to update session timezone'
                }, status=500)

        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'invalid_json',
                'message': 'Invalid JSON in request body'
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating session timezone: {e}")
            return JsonResponse({
                'error': 'server_error',
                'message': 'Internal server error'
            }, status=500)


@require_http_methods(["POST"])
@csrf_exempt  # Will be handled by DRF or custom auth
def validate_community_timezone_access_api(request, community_id):
    """
    API endpoint to validate timezone-based access to a community.

    Used by frontend to check access before navigating to community.
    """
    try:
        from communities.models import Community
        from .timezone_access_control import validate_community_timezone_access

        # Get community
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return JsonResponse({
                'error': 'community_not_found',
                'message': 'Community not found'
            }, status=404)

        # Check if community has timezone restrictions
        if community.geo_restriction_type != 'timezone_based':
            return JsonResponse({
                'allowed': True,
                'message': 'Community has no timezone restrictions'
            })

        # Validate access
        is_allowed, error_message = validate_community_timezone_access(
            request, community, check_hours=True
        )

        return JsonResponse({
            'allowed': is_allowed,
            'message': error_message if not is_allowed else 'Access granted',
            'community_id': str(community_id),
            'community_name': community.name
        })

    except Exception as e:
        logger.error(f"Error validating community timezone access: {e}")
        return JsonResponse({
            'error': 'validation_error',
            'message': 'Failed to validate timezone access'
        }, status=500)


# URL pattern helper
def get_timezone_api_urls():
    """Get URL patterns for timezone API endpoints."""
    from django.urls import path

    return [
        path(
            'auth/update-session-timezone/',
            UpdateSessionTimezoneView.as_view(),
            name='update-session-timezone'
        ),
        path(
            'communities/<int:community_id>/validate-timezone-access/',
            validate_community_timezone_access_api,
            name='validate-community-timezone-access'
        ),
    ]
