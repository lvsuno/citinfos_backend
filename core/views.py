"""
Session validation views for checking active sessions.
Dashboard views for aggregated data.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .session_manager import SessionManager
from django.views.decorators.http import require_GET
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # set dynamically to avoid circular import
        fields = ['id', 'scope', 'community', 'title', 'body_html', 'created_by', 'is_published', 'is_sticky', 'created_at']


class AnnouncementViewSet(viewsets.ModelViewSet):
    """API for managing global announcements (app-level moderators/admins only)."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        from .models import Announcement
        return Announcement.objects.filter(is_published=True).order_by('-is_sticky', '-created_at')

    def get_serializer_class(self):
        from .models import Announcement
        class _AnnouncementSerializer(serializers.ModelSerializer):
            class Meta:
                model = Announcement
                fields = ['id', 'title', 'body_html', 'created_by', 'is_published', 'is_sticky',
                         'target_user_roles', 'target_countries', 'created_at']
                read_only_fields = ['id', 'created_at']
        return _AnnouncementSerializer

    def perform_create(self, serializer):
        from accounts.models import UserProfile

        try:
            profile = UserProfile.objects.get(user=self.request.user)
        except Exception:
            profile = None

        # Only allow app-level admins or moderators to create global announcements
        allowed_roles = ('admin', 'moderator')
        if not profile or profile.role not in allowed_roles:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only app-level admins or moderators can create global announcements')

        serializer.save(created_by=profile)

@require_GET
def api_timezones(request):
    """Return canonical list of timezones (IANA)."""
    cache_key = 'core_timezones_v1'
    zones = cache.get(cache_key)
    if zones is None:
        try:
            import pytz
            zones = list(getattr(pytz, 'all_timezones', []))
        except Exception:
            try:
                from zoneinfo import available_timezones
                zones = sorted(available_timezones())
            except Exception:
                zones = ['UTC']
        cache.set(cache_key, zones, timeout=24 * 3600)

    resp = JsonResponse({'timezones': zones})
    resp['Cache-Control'] = 'public, max-age=86400'
    return resp


@require_GET
def api_countries(request):
    """Return list of countries for autocomplete (supports ?search=&limit=).

    Returns {'countries': [{id,name,iso2}, ...]}
    """
    from .models import Country
    search = request.GET.get('search', '').strip()
    try:
        limit = min(max(int(request.GET.get('limit', 50)), 1), 500)
    except Exception:
        limit = 50

    cache_key = f'core_countries_autocomplete_v1:{search}:{limit}'
    results = cache.get(cache_key)
    if results is None:
        qs = Country.objects.all().order_by('name')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(iso2__icontains=search))
        items = qs[:limit]
        results = [
            {'id': str(c.id), 'name': c.name, 'iso2': c.iso2}
            for c in items
        ]
        cache.set(cache_key, results, timeout=24 * 3600)

    resp = JsonResponse({'countries': results})
    resp['Cache-Control'] = 'public, max-age=86400'
    return resp


@require_GET
def api_cities(request):
    """Return list of cities. Accept optional ?country=<id> to filter."""
    from .models import City
    country = request.GET.get('country')
    search = request.GET.get('search', '').strip()
    try:
        limit = min(max(int(request.GET.get('limit', 50)), 1), 500)
    except Exception:
        limit = 50

    cache_key = f'core_cities_autocomplete_v1:{country or "all"}:{search}:{limit}'
    results = cache.get(cache_key)
    if results is None:
        qs = City.objects.select_related('country').all().order_by('name')
        if country:
            qs = qs.filter(country_id=country)
        if search:
            # use icontains for simple autocomplete; consider trigram or full-text for better perf
            qs = qs.filter(name__icontains=search)

        items = qs[:limit]
        results = []
        for c in items:
            results.append({
                'id': str(c.id),
                'name': c.name,
                'country': str(c.country_id),
                'country_name': c.country.name,
            })

        cache.set(cache_key, results, timeout=60 * 60)

    resp = JsonResponse({'cities': results})
    resp['Cache-Control'] = 'public, max-age=300'
    return resp


@method_decorator(csrf_exempt, name='dispatch')
class SessionValidationView(APIView):
    """
    API endpoint to validate session status.
    """

    def __init__(self):
        super().__init__()
        self.session_manager = SessionManager()

    def get(self, request):
        """
        Check if current session is valid and active.
        """
        # Get session ID from various sources
        session_id = request.session.session_key
        if not session_id:
            session_id = request.META.get('HTTP_X_SESSION_ID')
        if not session_id:
            session_id = request.GET.get('session_id')

        if not session_id:
            return Response({
                'valid': False,
                'error': 'No session ID provided',
                'redirect': '/login'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Validate session
        session_data = self.session_manager.get_session(session_id)

        if not session_data or not session_data.get('is_active', False):
            return Response({
                'valid': False,
                'error': 'Invalid or expired session',
                'redirect': '/login'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Smart renew session if needed
        self.session_manager.smart_renew_session_if_needed(session_id)

        return Response({
            'valid': True,
            'session_data': {
                'user_id': session_data.get('user_id'),
                'username': session_data.get('user_username'),
                'session_id': session_data.get('session_id'),
                'device_info': session_data.get('device_info', {}),
                'started_at': session_data.get('started_at')
            }
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class SessionRefreshView(APIView):
    """
    API endpoint to refresh/extend session duration.
    """

    def __init__(self):
        super().__init__()
        self.session_manager = SessionManager()

    def post(self, request):
        """
        Refresh the current session to extend its duration.
        """
        session_id = request.session.session_key
        if not session_id:
            session_id = request.META.get('HTTP_X_SESSION_ID')

        if not session_id:
            return Response({
                'success': False,
                'error': 'No session ID provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate and refresh session
        session_data = self.session_manager.get_session(session_id)

        if not session_data:
            return Response({
                'success': False,
                'error': 'Invalid session'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Smart renew session if needed (only renews when 25% time remaining)
        self.session_manager.smart_renew_session_if_needed(session_id)

        return Response({
            'success': True,
            'message': 'Session refreshed successfully',
            'expires_in': 14400  # 4 hours in seconds
        }, status=status.HTTP_200_OK)


# Django function-based view for legacy support
@csrf_exempt
@require_http_methods(["GET", "POST"])
def check_session_status(request):
    """
    Check session status - function-based view for simpler integration.
    """
    session_manager = SessionManager()

    # Get session ID
    session_id = request.session.session_key
    if not session_id:
        session_id = request.META.get('HTTP_X_SESSION_ID')

    if not session_id:
        return JsonResponse({
            'valid': False,
            'error': 'No session found',
            'redirect': '/login'
        }, status=401)

    # Validate session
    session_data = session_manager.get_session(session_id)

    if not session_data or not session_data.get('is_active', False):
        return JsonResponse({
            'valid': False,
            'error': 'Session expired',
            'redirect': '/login'
        }, status=401)

    # Smart renew session if needed
    session_manager.smart_renew_session_if_needed(session_id)

    return JsonResponse({
        'valid': True,
        'user_id': session_data.get('user_id'),
        'username': session_data.get('user_username')
    })


# Dashboard Views
@method_decorator(csrf_exempt, name='dispatch')
class DashboardStatsView(APIView):
    """
    Dashboard statistics aggregation endpoint.
    """

    def get(self, request):
        """
        Get dashboard statistics from all apps.
        """
        try:
            from django.contrib.auth.models import User
            from content.models import Post, Comment, Like
            from communities.models import Community, CommunityMembership
            from polls.models import Poll, PollVote
            # Equipment functionality removed
            # from equipment.models import Equipment

            # Get user counts
            total_users = User.objects.count()
            active_users = User.objects.filter(
                last_login__gte=timezone.now() - timedelta(days=30)
            ).count()

            # Get content stats - exclude soft-deleted items
            total_posts = Post.objects.filter(is_deleted=False).count()
            total_comments = Comment.objects.filter(is_deleted=False).count()
            total_likes = Like.objects.filter(is_deleted=False).count()

            # Get community stats - exclude soft-deleted items
            total_communities = Community.objects.filter(is_deleted=False).count()
            total_memberships = CommunityMembership.objects.filter(is_deleted=False).count()

            # Get polls stats - exclude soft-deleted items
            total_polls = Poll.objects.filter(is_deleted=False).count()
            total_votes = PollVote.objects.filter(is_deleted=False).count()

            # Equipment functionality removed

            return Response({
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'new_this_month': User.objects.filter(
                        date_joined__gte=timezone.now() - timedelta(days=30)
                    ).count()
                },
                'content': {
                    'posts': total_posts,
                    'comments': total_comments,
                    'likes': total_likes,
                    'engagement_rate': round((total_likes / max(total_posts, 1)) * 100, 2)
                },
                'communities': {
                    'total': total_communities,
                    'memberships': total_memberships,
                    'avg_members': round(total_memberships / max(total_communities, 1), 2)
                },
                'polls': {
                    'total': total_polls,
                    'votes': total_votes,
                    'participation_rate': round((total_votes / max(total_polls, 1)) * 100, 2)
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'Error fetching dashboard stats: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class DashboardActivityView(APIView):
    """
    Dashboard recent activity endpoint.
    """

    def get(self, request):
        """
        Get recent activity across the platform.
        """
        try:
            from accounts.models import UserEvent

            # Get recent events (last 24 hours)
            recent_events = UserEvent.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).order_by('-created_at')[:50]

            activity_data = []
            for event in recent_events:
                activity_data.append({
                    'id': event.id,
                    'user': event.user.username if event.user else 'Anonymous',
                    'event_type': event.event_type,
                    'description': event.description,
                    'timestamp': event.created_at.isoformat(),
                    'url': getattr(event, 'url', '')
                })

            return Response({
                'recent_activity': activity_data,
                'total_events_24h': recent_events.count()
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'Error fetching activity data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class DashboardTrendingView(APIView):
    """
    Dashboard trending content endpoint.
    """

    def get(self, request):
        """
        Get trending content across different categories.
        """
        try:
            from content.models import Post, Like
            from polls.models import Poll, PollVote
            from communities.models import Community, CommunityMembership

            # Trending posts (by likes in last week)
            week_ago = timezone.now() - timedelta(days=7)
            trending_posts = Post.objects.filter(
                created_at__gte=week_ago
            ).order_by('-likes_count')[:10]

            # Trending polls (by votes in last week)
            trending_polls = Poll.objects.filter(
                created_at__gte=week_ago
            ).order_by('-total_votes')[:10]

            # Trending communities (by new memberships)
            trending_communities = Community.objects.filter(
                memberships__joined_at__gte=week_ago
            ).annotate(
                new_member_count=Count('memberships')
            ).order_by('-new_member_count')[:10]

            return Response({
                'trending_posts': [{
                    'id': post.id,
                    'content': (post.content[:100] + '...'
                                if len(post.content) > 100 else post.content),
                    'author': post.author.user.username,
                    'like_count': post.likes_count,
                    'created_at': post.created_at.isoformat()
                } for post in trending_posts],
                'trending_polls': [{
                    'id': poll.id,
                    'question': poll.question,
                    'creator': poll.post.author.user.username,
                    'vote_count': poll.total_votes,
                    'created_at': poll.created_at.isoformat()
                } for poll in trending_polls],
                'trending_communities': [{
                    'id': community.id,
                    'name': community.name,
                    'new_members': community.new_member_count,
                    'created_at': community.created_at.isoformat()
                } for community in trending_communities]
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'Error fetching trending data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
