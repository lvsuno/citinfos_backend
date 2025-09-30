"""
Analytics Middleware for automatic tracking integration.

This middleware demonstrates how to integrate analytics tracking
into the request/response cycle to automatically collect data.
"""
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.contrib.auth.models import AnonymousUser
from analytics.tasks import (
    track_content_analytics,
    track_search_analytics,
    update_comprehensive_user_analytics,
    track_post_view
)
import logging

logger = logging.getLogger(__name__)


class AnalyticsTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track various analytics metrics.

    This middleware integrates with the authentication middleware to provide
    comprehensive analytics tracking across the application.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request):
        """Mark request start time for performance tracking."""
        request._analytics_start_time = time.time()
        return None

    def process_response(self, request, response):
        """
        Track analytics based on the request/response cycle.
        """
        try:
            # Calculate request processing time
            processing_time = (
                (time.time() - getattr(request, '_analytics_start_time', time.time())) * 1000
            )

            # Get user information
            user = getattr(request, 'user', None)
            user_profile = None
            if user and not isinstance(user, AnonymousUser) and hasattr(user, 'profile'):
                user_profile = user.profile

            # Get request metadata
            url_name = self._get_url_name(request)
            ip_address = self._get_client_ip(request)
            device_type = self._get_device_type(request)

            # Track based on URL patterns
            if url_name and response.status_code == 200:
                self._track_by_url_pattern(
                    request, response, url_name, user_profile,
                    processing_time, ip_address, device_type
                )

            # Track search queries
            if 'search' in request.GET or 'q' in request.GET:
                self._track_search_request(
                    request, response, user, processing_time, ip_address, device_type
                )

            # Update user analytics periodically
            if user_profile and hasattr(request, 'session'):
                session_key = request.session.session_key
                if session_key and session_key.endswith('0'):  # Sample 10% of requests
                    update_comprehensive_user_analytics.delay(str(user_profile.id))

            # Track page views for authenticated users
            self._track_page_view(request, response, user_profile)

        except Exception as e:
            logger.error("Error in analytics tracking middleware: %s", e)

        return response

    def _get_url_name(self, request):
        """Get the URL name from the request."""
        try:
            resolved = resolve(request.path_info)
            return resolved.url_name
        except Exception:
            return None

    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _get_device_type(self, request):
        """Determine device type from user agent."""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        else:
            return 'desktop'

    def _track_by_url_pattern(self, request, response, url_name, user_profile,
                             processing_time, ip_address, device_type):
        """Track analytics based on URL patterns."""

        # Content-related tracking
        if 'post' in url_name or 'thread' in url_name or 'comment' in url_name:
            self._track_content_interaction(
                request, url_name, user_profile, ip_address, device_type
            )


    def _track_content_interaction(self, request, url_name, user_profile,
                                  ip_address, device_type):
        """Track content-related interactions."""
        try:
            # Extract content information from URL parameters
            content_id = request.resolver_match.kwargs.get('pk') or request.GET.get('id')
            if not content_id:
                return

            # Determine content type and action
            if 'post' in url_name:
                content_type = 'post'
                action = 'view'

                # Special handling for PostSee tracking
                if request.method == 'GET' and action == 'view':
                    self._track_post_view(
                        request, content_id, user_profile, ip_address, device_type
                    )

            elif 'thread' in url_name:
                content_type = 'thread'
                action = 'view'
            elif 'comment' in url_name:
                content_type = 'comment'
                action = 'view'
            else:
                return

            # Check for specific actions
            if request.method == 'POST':
                if 'like' in request.path:
                    action = 'like'
                elif 'share' in request.path:
                    action = 'share'
                elif 'comment' in request.path:
                    action = 'comment'

            # Track the content analytics
            content_data = {
                'content_type': content_type,
                'content_id': content_id,
                'author_id': str(user_profile.id) if user_profile else None,
                'action': action,
                'user_id': str(user_profile.id) if user_profile else None,
                'ip_address': ip_address,
                'device_type': device_type,
            }

            # Add read time for view actions (simplified estimation)
            if action == 'view' and 'HTTP_REFERER' in request.META:
                # This is a simplified read time estimation
                # In production, you'd use JavaScript to track actual read time
                content_data['read_time'] = 30  # Default 30 seconds

            track_content_analytics.delay(content_data)

        except Exception as e:
            logger.error("Error tracking content interaction: %s", e)

    def _track_post_view(self, request, post_id, user_profile, ip_address, device_type):
        """Track PostSee view with enhanced analytics."""
        try:
            # Create PostSee tracking data
            post_view_data = {
                'post_id': post_id,
                'user_id': str(user_profile.id) if user_profile else None,
                'view_duration_seconds': 0,  # Will be updated by frontend
                'scroll_percentage': 0.0,    # Will be updated by frontend
                'source': self._determine_source(request),
                'device_type': device_type,
                'session_id': request.session.session_key or '',
                'ip_address': ip_address,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'clicked_links': [],
                'media_viewed': [],
                'is_engaged': False,
            }

            # Queue the post view tracking
            track_post_view.delay(post_view_data)

        except Exception as e:
            logger.error(f"Error tracking PostSee view: {e}")

    def _track_page_view(self, request, response, user_profile):
        """Track page view for authenticated users"""
        try:
            from analytics.tasks import track_page_view

            if user_profile and request.method == 'GET':
                # Only track GET requests for actual page views
                if response.status_code == 200:
                    # Pass UserProfile.id (UUID) not User.id (integer)
                    track_page_view.delay(str(user_profile.id))
        except Exception as e:
            logger.error(f"Error tracking page view: {e}")

    def _determine_source(self, request):
        """Determine the source of the post view."""
        referer = request.META.get('HTTP_REFERER', '')
        path = request.path

        if 'community' in path or 'community' in referer:
            return 'community'
        elif 'profile' in path or 'profile' in referer:
            return 'profile'
        elif 'search' in referer:
            return 'search'
        elif 'notification' in referer:
            return 'notification'
        elif referer and 'share' in referer:
            return 'share'
        elif not referer:
            return 'direct_link'
        else:
            return 'feed'

    def _track_search_request(self, request, response, user, processing_time,
                             ip_address, device_type):
        """Track search-related requests."""
        try:
            # Get search query
            query = request.GET.get('search') or request.GET.get('q', '').strip()
            if not query:
                return

            # Determine search type
            if 'user' in request.path or 'profile' in request.path:
                search_type = 'users'
            elif 'community' in request.path:
                search_type = 'communities'
            else:
                search_type = 'global'

            # Extract search metadata
            filters_applied = {}
            for key, value in request.GET.items():
                if key not in ['search', 'q', 'page'] and value:
                    filters_applied[key] = value

            # Get session ID for tracking
            session_id = getattr(request.session, 'session_key', '')

            # Count results (simplified - in practice, you'd get this from the view)
            total_results = 0
            if hasattr(response, 'context_data') and response.context_data:
                # Try to extract result count from context
                results = response.context_data.get('results') or response.context_data.get('object_list')
                if hasattr(results, 'count'):
                    total_results = results.count()
                elif hasattr(results, '__len__'):
                    total_results = len(results)

            search_data = {
                'query': query,
                'user_id': user.id if user and not isinstance(user, AnonymousUser) else None,
                'session_id': session_id,
                'search_type': search_type,
                'filters_applied': filters_applied,
                'sort_criteria': request.GET.get('sort', ''),
                'total_results': total_results,
                'results_page': int(request.GET.get('page', 1)),
                'results_per_page': 20,  # Default pagination
                'search_time_ms': processing_time,
                'ip_address': ip_address,
                'device_type': device_type,
                'autocomplete_used': request.GET.get('autocomplete') == 'true',
                'voice_search': request.GET.get('voice') == 'true',
            }

            track_search_analytics.delay(search_data)

        except Exception as e:
            logger.error("Error tracking search request: %s", e)


class ContentAnalyticsSignalHandler:
    """
    Signal handler for content-related analytics.

    This class provides methods to connect to Django signals
    for automatic content analytics tracking.
    """

    @staticmethod
    def handle_post_save(sender, instance, created, **kwargs):
        """Handle post save signals for content analytics."""
        if created:
            content_data = {
                'content_type': sender._meta.model_name,
                'content_id': str(instance.id),
                'author_id': str(instance.author.id) if hasattr(instance, 'author') else None,
                'action': 'created',
            }
            track_content_analytics.delay(content_data)

    @staticmethod
    def handle_like_action(sender, instance, action, pk_set, **kwargs):
        """Handle like/unlike actions via m2m_changed signal."""
        if action == 'post_add':
            for user_id in pk_set:
                content_data = {
                    'content_type': sender._meta.model_name,
                    'content_id': str(instance.id),
                    'author_id': str(instance.author.id) if hasattr(instance, 'author') else None,
                    'action': 'like',
                    'user_id': str(user_id),
                }
                track_content_analytics.delay(content_data)

