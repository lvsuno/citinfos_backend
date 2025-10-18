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

        # Skip fingerprint generation for static assets and health checks
        SKIP_PATHS = [
            '/static/', '/media/', '/health/',
            '/favicon.ico', '/robots.txt'
        ]
        if any(request.path.startswith(p) for p in SKIP_PATHS):
            return None

        # Cache device fingerprint early for anonymous users
        # This avoids regenerating it multiple times per request
        user = getattr(request, 'user', None)
        if not user or isinstance(user, AnonymousUser):
            self._get_or_cache_fingerprint(request)

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

            # Send fingerprint to client in response header
            # This allows client to cache and reuse fingerprint for subsequent requests
            if not user_profile:  # Only for anonymous users
                try:
                    fingerprint = self._get_or_cache_fingerprint(request, response)
                    if fingerprint:
                        response['X-Device-Fingerprint'] = fingerprint
                except Exception as fp_error:
                    logger.error(f"Error adding fingerprint to response: {fp_error}")

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
        """Track page view for authenticated and anonymous users"""
        try:
            from analytics.tasks import track_page_view

            # Track authenticated user page views
            if user_profile and request.method == 'GET':
                # Only track GET requests for actual page views
                if response.status_code == 200:
                    # Pass UserProfile.id (UUID) not User.id (integer)
                    track_page_view.delay(str(user_profile.id))

                    # Check if this is a community page visit
                    community_data = self._extract_community_context(
                        request
                    )

                    if community_data:
                        # Track community visit event
                        self._track_community_visit(
                            request,
                            user_profile,
                            community_data,
                            is_authenticated=True
                        )

            # Track anonymous user page views and community visits
            elif not user_profile and request.method == 'GET':
                if response.status_code == 200:
                    # OPTIMIZATION: Only track anonymous page views for actual page loads
                    # Skip API endpoints to avoid performance overhead
                    if not request.path.startswith('/api/'):
                        # Track anonymous page view (all pages)
                        self._track_anonymous_page_view(request, response)

                    # Check for community page visit
                    community_data = self._extract_community_context(
                        request
                    )

                    if community_data:
                        # Track anonymous community visit
                        self._track_community_visit(
                            request,
                            None,
                            community_data,
                            is_authenticated=False
                        )
        except Exception as e:
            logger.error(f"Error tracking page view: {e}")

    def _track_anonymous_page_view(self, request, response):
        """
        Track anonymous user page views in Redis (OPTIMIZED).

        Creates/updates anonymous session with:
        - Device fingerprint identification (cached)
        - Page visit tracking
        - Session duration
        - Persist to DB every 5th page view

        OPTIMIZATION: Offload Redis operations to async task to avoid blocking
        """
        try:
            from analytics.tasks import track_anonymous_page_view_async

            # Get device fingerprint (cached or from cookie)
            device_fingerprint = self._get_or_cache_fingerprint(
                request,
                response
            )

            if not device_fingerprint:
                logger.warning("Could not generate device fingerprint")
                return

            # Collect minimal data and offload to async task
            # This avoids blocking the response with Redis operations
            page_view_data = {
                'device_fingerprint': device_fingerprint,
                'current_url': request.build_absolute_uri(),
                'page_type': self._determine_page_type(request.path),
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'device_type': self._get_device_type(request),
                'referrer': request.META.get('HTTP_REFERER', ''),
                'utm_params': self._extract_utm_params(request),
            }

            # Offload to Celery task (non-blocking)
            track_anonymous_page_view_async.delay(page_view_data)

        except Exception as e:
            logger.error(f"Error tracking anonymous page view: {e}")

    def _determine_page_type(self, path):
        """Determine page type from URL path."""
        if path == '/' or path == '/home':
            return 'home'
        elif '/communities/' in path or '/community/' in path:
            return 'community'
        elif '/posts/' in path or '/post/' in path:
            return 'post'
        elif '/profiles/' in path or '/profile/' in path:
            return 'profile'
        elif '/search' in path:
            return 'search'
        elif '/login' in path or '/register' in path or '/signup' in path:
            return 'auth'
        elif '/about' in path or '/contact' in path or '/help' in path:
            return 'about'
        else:
            return 'other'

    def _extract_utm_params(self, request):
        """Extract UTM tracking parameters from request."""
        utm_params = {}

        utm_fields = [
            'utm_source', 'utm_medium', 'utm_campaign',
            'utm_term', 'utm_content'
        ]

        for field in utm_fields:
            value = request.GET.get(field, '')
            if value:
                utm_params[field] = value

        return utm_params

    def _extract_browser(self, user_agent):
        """Extract browser name from user agent."""
        user_agent_lower = user_agent.lower()

        if 'edg' in user_agent_lower:
            return 'Edge'
        elif 'chrome' in user_agent_lower:
            return 'Chrome'
        elif 'safari' in user_agent_lower:
            return 'Safari'
        elif 'firefox' in user_agent_lower:
            return 'Firefox'
        elif 'opera' in user_agent_lower or 'opr' in user_agent_lower:
            return 'Opera'
        else:
            return 'Unknown'

    def _extract_os(self, user_agent):
        """Extract operating system from user agent."""
        user_agent_lower = user_agent.lower()

        if 'windows' in user_agent_lower:
            return 'Windows'
        elif 'mac os' in user_agent_lower or 'macos' in user_agent_lower:
            return 'macOS'
        elif 'linux' in user_agent_lower:
            return 'Linux'
        elif 'android' in user_agent_lower:
            return 'Android'
        elif (
            'ios' in user_agent_lower or
            'iphone' in user_agent_lower or
            'ipad' in user_agent_lower
        ):
            return 'iOS'
        else:
            return 'Unknown'

    def _extract_community_context(self, request):
        """Extract community ID and division from URL."""
        try:
            from communities.models import Community
            from django.db.models import Q

            # Check if URL contains community patterns
            path = request.path

            # Match patterns: /communities/{slug}/ or /api/communities/{slug}/
            if '/communities/' in path or '/community/' in path:
                # Try to get slug from URL
                parts = path.strip('/').split('/')

                if 'communities' in parts or 'community' in parts:
                    idx = (
                        parts.index('communities')
                        if 'communities' in parts
                        else parts.index('community')
                    )

                    if idx + 1 < len(parts):
                        slug_or_id = parts[idx + 1]

                        # Try to fetch community
                        try:
                            # Check if it's a valid UUID first
                            import uuid
                            try:
                                uuid.UUID(slug_or_id)
                                is_uuid = True
                            except ValueError:
                                is_uuid = False

                            # Build query - only check ID if it's a valid UUID
                            if is_uuid:
                                community = Community.objects.select_related(
                                    'division'
                                ).get(
                                    Q(slug=slug_or_id) | Q(id=slug_or_id)
                                )
                            else:
                                community = Community.objects.select_related(
                                    'division'
                                ).get(slug=slug_or_id)

                            return {
                                'community_id': str(community.id),
                                'community_slug': community.slug,
                                'community_division_id': (
                                    str(community.division.id)
                                    if community.division
                                    else None
                                )
                            }
                        except Community.DoesNotExist:
                            pass
                        except Community.MultipleObjectsReturned:
                            # Use first match if multiple found
                            if is_uuid:
                                community = Community.objects.select_related(
                                    'division'
                                ).filter(
                                    Q(slug=slug_or_id) | Q(id=slug_or_id)
                                ).first()
                            else:
                                community = Community.objects.select_related(
                                    'division'
                                ).filter(slug=slug_or_id).first()

                            if community:
                                return {
                                    'community_id': str(community.id),
                                    'community_slug': community.slug,
                                    'community_division_id': (
                                        str(community.division.id)
                                        if community.division
                                        else None
                                    )
                                }

            return None

        except Exception as e:
            logger.error(f"Error extracting community context: {e}")
            return None

    def _track_community_visit(
        self,
        request,
        user_profile,
        community_data,
        is_authenticated=True
    ):
        """
        Track community visit with division analytics for authenticated
        and anonymous visitors.
        """
        try:
            from communities.visitor_tracker import visitor_tracker
            from accounts.models import UserEvent

            # Get device fingerprint (cached to avoid regeneration)
            device_fingerprint = self._get_or_cache_fingerprint(request)

            # Get IP and user agent
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            community_id = community_data['community_id']
            community_division_id = community_data.get('community_division_id')

            if is_authenticated and user_profile:
                # Authenticated user tracking
                has_division = (
                    hasattr(user_profile, 'division') and
                    user_profile.division
                )
                visitor_division_id = (
                    str(user_profile.division.id)
                    if has_division
                    else None
                )

                user_id = str(user_profile.id)

                # Add visitor to Redis tracker
                visitor_result = visitor_tracker.add_visitor(
                    user_id=user_id,
                    community_id=community_id,
                    visitor_division_id=visitor_division_id,
                    community_division_id=community_division_id,
                    is_authenticated=True,
                    device_fingerprint=device_fingerprint,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                # Create UserEvent for authenticated community_visit
                UserEvent.objects.create(
                    user=user_profile,
                    event_type='community_visit',
                    description=(
                        f"Visited community {community_data['community_slug']}"
                    ),
                    metadata={
                        'community_id': community_id,
                        'community_slug': community_data['community_slug'],
                        'visitor_division_id': visitor_division_id,
                        'community_division_id': community_division_id,
                        'is_cross_division': visitor_result.get(
                            'is_cross_division',
                            False
                        ),
                        'is_authenticated': True,
                        'device_fingerprint': device_fingerprint,
                        'url': request.path,
                        'referrer': request.META.get('HTTP_REFERER', '')
                    },
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                logger.info(
                    f"Tracked authenticated community visit: "
                    f"user {user_profile.id} "
                    f"(division {visitor_division_id}) visiting "
                    f"community {community_id} "
                    f"(division {community_division_id})"
                )
            else:
                # Anonymous user tracking - use device fingerprint
                # No division tracking for anonymous (unless IP geolocation)
                visitor_division_id = None

                # Check if we have active session with fingerprint
                # (to detect if this device was previously authenticated)
                from accounts.models import UserSession

                recent_session = UserSession.objects.filter(
                    device_fingerprint=device_fingerprint,
                    is_active=True
                ).first()

                if recent_session and recent_session.user:
                    # This device has an active authenticated session
                    # Don't track as anonymous - will be tracked when auth
                    logger.debug(
                        f"Device {device_fingerprint[:8]}... has active "
                        f"session, skipping anonymous tracking"
                    )
                    return

                # Add anonymous visitor to Redis tracker
                visitor_result = visitor_tracker.add_visitor(
                    user_id=f"anonymous_{device_fingerprint[:16]}",
                    community_id=community_id,
                    visitor_division_id=visitor_division_id,
                    community_division_id=community_division_id,
                    is_authenticated=False,
                    device_fingerprint=device_fingerprint,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                # Log anonymous visit (no UserEvent for privacy)
                logger.info(
                    f"Tracked anonymous community visit: "
                    f"fingerprint {device_fingerprint[:16]}... visiting "
                    f"community {community_id} "
                    f"(division {community_division_id})"
                )

        except Exception as e:
            logger.error(f"Error tracking community visit: {e}")

    def _get_or_cache_fingerprint(self, request, response=None):
        """
        Get device fingerprint with intelligent caching.

        Priority order:
        1. Request-level cache (_cached_device_fingerprint)
        2. Client-provided header (X-Device-Fingerprint) ← OPTIMIZED!
        3. Cookie (device_fp)
        4. Server-side generation (fallback)

        Args:
            request: Django request object
            response: Django response object (optional, for setting cookie)

        Returns:
            Device fingerprint string
        """
        # Tier 1: Check request-level cache first (fastest)
        if hasattr(request, '_cached_device_fingerprint'):
            return request._cached_device_fingerprint

        # Tier 2: Check client-provided header (NEW - optimal for modern clients)
        client_fingerprint = request.META.get('HTTP_X_DEVICE_FINGERPRINT')
        if client_fingerprint:
            request._cached_device_fingerprint = client_fingerprint
            request._fingerprint_source = 'client_header'

            # Set cookie as backup for future requests
            if response:
                response.set_cookie(
                    'device_fp',
                    client_fingerprint,
                    max_age=30*24*60*60,  # 30 days
                    httponly=True,
                    samesite='Lax'
                )

            return client_fingerprint

        # Tier 3: Check cookie (existing users)
        cookie_fingerprint = request.COOKIES.get('device_fp')
        if cookie_fingerprint:
            request._cached_device_fingerprint = cookie_fingerprint
            request._fingerprint_source = 'cookie'
            return cookie_fingerprint

        # Tier 4: Server-side generation (fallback for old browsers)
        from core.device_fingerprint import OptimizedDeviceFingerprint
        server_fingerprint = (
            OptimizedDeviceFingerprint.get_fast_fingerprint(request)
        )

        request._cached_device_fingerprint = server_fingerprint
        request._fingerprint_source = 'server_generated'

        # Set cookie if response provided
        if server_fingerprint and response:
            response.set_cookie(
                'device_fp',
                server_fingerprint,
                max_age=30*24*60*60,  # 30 days
                httponly=True,
                samesite='Lax'
            )

        # Cache in request
        if server_fingerprint:
            request._cached_device_fingerprint = server_fingerprint

        return server_fingerprint

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

