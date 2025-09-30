from rest_framework import viewsets, permissions, status
from .models import UserSearchQuery
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import UserSearchQuerySerializer
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
import redis
from .tasks import cache_recent_searches_by_user_type
from .global_search import GlobalSearchEngine

from postal.parser import parse_address

# Import models for user search
from accounts.models import UserProfile, Follow
from communities.models import CommunityMembership
from django.db.models import Q
from django.contrib.auth.models import User

class UserSearchQueryViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profile'):
            return UserSearchQuery.objects.filter(user=user.profile, is_deleted=False)
        return UserSearchQuery.objects.none().filter(is_deleted=False)


    serializer_class = UserSearchQuerySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['search_type']

    @action(detail=False, methods=['get'], url_path='cached-recent')
    def cached_recent(self, request):
        user_id = str(request.user.userprofile.id)
        search_type = request.query_params.get('search_type', 'post')
        limit = int(request.query_params.get('limit', 5))
        r = redis.Redis.from_url(settings.REDIS_URL)
        cache_key = f'recent_searches:{user_id}:{search_type}'
        cached = r.get(cache_key)
        if cached:
            import ast
            data = ast.literal_eval(cached.decode())
        else:
            data = cache_recent_searches_by_user_type(user_id, search_type, limit)
        return Response(data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user.profile)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()


class ParseAddressView(APIView):
    def post(self, request):
        address = request.data.get('address', '')
        if not address:
            return Response({'error': 'No address provided'}, status=400)
        parsed = parse_address(address)
        result = {component: value for value, component in parsed}
        return Response(result)


class GlobalSearchView(APIView):
    """
    Comprehensive search endpoint for all content types.

    Supports:
    - Cross-app content search
    - Permission-based filtering
    - Content type filtering
    - Advanced filters
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        """
        Perform global search across all content types.

        Query parameters:
        - q: Search query string (required)
        - types: Comma-separated content types (optional)
        - limit: Results per type (default: 20)
        - offset: Pagination offset (default: 0)
        - filters: JSON string of additional filters
        """
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse content types
        types_param = request.query_params.get('types', '')
        if types_param:
            content_types = [t.strip() for t in types_param.split(',')]
        else:
            content_types = None

        # Parse pagination
        try:
            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))
        except ValueError:
            return Response(
                {'error': 'Invalid limit or offset'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse additional filters
        filters = {}
        filters_param = request.query_params.get('filters')
        if filters_param:
            try:
                import json
                filters = json.loads(filters_param)
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid filters JSON'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Add query params as filters
        for key in ['post_type', 'community_id', 'date_range', 'category',
                   'status', 'community_type', 'role', 'location']:
            value = request.query_params.get(key)
            if value:
                filters[key] = value

        # Perform search
        search_engine = GlobalSearchEngine(request.user)
        results = search_engine.search(
            query=query,
            content_types=content_types,
            filters=filters,
            limit=limit,
            offset=offset
        )

        return Response(results, status=status.HTTP_200_OK)


class QuickSearchView(APIView):
    """
    Quick search for autocomplete and suggestions.
    Returns limited results optimized for speed.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        """
        Quick search for autocomplete suggestions.

        Query parameters:
        - q: Search query (required)
        - type: Single content type (optional)
        - limit: Max results (default: 5)
        """
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response(
                {'suggestions': []},
                status=status.HTTP_200_OK
            )

        content_type = request.query_params.get('type', 'posts')
        limit = min(int(request.query_params.get('limit', 5)), 10)

        search_engine = GlobalSearchEngine(request.user)
        results = search_engine.search(
            query=query,
            content_types=[content_type],
            limit=limit,
            offset=0
        )

        # Extract suggestions
        suggestions = []
        if content_type in results['results']:
            for item in results['results'][content_type]:
                suggestion = {
                    'id': item['id'],
                    'title': item.get('title', item.get('name', '')),
                    'type': item['type'],
                    'url': item['url']
                }
                suggestions.append(suggestion)

        return Response(
            {'suggestions': suggestions},
            status=status.HTTP_200_OK
        )


class UserSearchView(APIView):
    """
    Global user search endpoint with various filtering options.

    Supports multiple search types:
    - followers_of: Users following a specific user
    - members_of: Members of a specific community
    - public: Public users (not private profiles)
    - professional: Users with professional role
    - commercial: Users with commercial role
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Search for users with various filters.

        Query parameters:
        - q: Search query (username, first name, last name, bio)
        - search_type: Type of search (followers_of, members_of, public, professional, commercial)
        - target_user_id: User ID for 'followers_of' search type
        - community_id: Community ID for 'members_of' search type
        - limit: Results limit (default: 20, max: 50)
        - offset: Pagination offset (default: 0)
        """
        import logging
        from django.core.exceptions import FieldError

        query = request.GET.get('q', '').strip()
        search_type = request.GET.get('search_type', 'public')
        target_user_id = request.GET.get('target_user_id')
        community_id = request.GET.get('community_id')

        # Pagination
        try:
            limit = min(int(request.GET.get('limit', 20)), 50)
            offset = int(request.GET.get('offset', 0))
        except ValueError:
            return Response({'error': 'Invalid limit or offset'}, status=status.HTTP_400_BAD_REQUEST)

        # Base queryset - exclude soft deleted profiles and inactive users
        queryset = UserProfile.objects.filter(is_deleted=False, user__is_active=True)

        # Exclude current user if they have a profile
        if hasattr(request.user, 'profile'):
            queryset = queryset.exclude(id=request.user.profile.id)

        try:
            # Apply search type filters
            if search_type == 'followers_of':
                if not target_user_id:
                    return Response({'error': 'target_user_id required for followers_of search'}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    target_profile = UserProfile.objects.get(id=target_user_id, is_deleted=False)
                except UserProfile.DoesNotExist:
                    return Response({'error': 'Target user not found'}, status=status.HTTP_404_NOT_FOUND)

                follower_ids = Follow.objects.filter(
                    followed=target_profile,
                    status='approved',
                    is_deleted=False
                ).values_list('follower_id', flat=True)

                queryset = queryset.filter(id__in=follower_ids)

            elif search_type == 'members_of':
                if not community_id:
                    return Response({'error': 'community_id required for members_of search'}, status=status.HTTP_400_BAD_REQUEST)

                member_ids = CommunityMembership.objects.filter(
                    community_id=community_id,
                    status='approved',
                    is_deleted=False
                ).values_list('user_id', flat=True)

                queryset = queryset.filter(id__in=member_ids)

            elif search_type == 'public':
                queryset = queryset.filter(is_private=False)

            elif search_type == 'professional':
                queryset = queryset.filter(role='professional')

            elif search_type == 'commercial':
                queryset = queryset.filter(role='commercial')

            else:
                return Response({'error': f'Invalid search_type: {search_type}'}, status=status.HTTP_400_BAD_REQUEST)

            # Apply text search if query provided. `display_name` is a @property
            # on UserProfile and not a database field, so search on real fields
            # (username, first_name, last_name, bio).
            if query:
                try:
                    queryset = queryset.filter(
                        Q(user__username__icontains=query) |
                        Q(user__first_name__icontains=query) |
                        Q(user__last_name__icontains=query) |
                        Q(bio__icontains=query)
                    )
                except FieldError:
                    # Defensive fallback for deployments where some fields
                    # may not exist: fall back to a minimal safe filter.
                    queryset = queryset.filter(
                        Q(user__username__icontains=query) |
                        Q(bio__icontains=query)
                    )

            # Pagination and ordering
            total_count = queryset.count()
            users_qs = queryset.select_related('user').order_by('-created_at')[offset:offset + limit]

            # Serialize results
            results = []
            for user in users_qs:
                user_data = {
                    'id': str(user.id),
                    'username': user.user.username,
                    'display_name': user.display_name or user.user.username,
                    'full_name': f"{user.user.first_name} {user.user.last_name}".strip(),
                    'bio': user.bio or '',
                    'avatar': user.profile_picture.url if user.profile_picture else None,
                    'role': user.role,
                    'is_private': user.is_private,
                    'follower_count': user.follower_count,
                    'following_count': user.following_count,
                    'is_verified': user.is_verified,
                    'is_professional': user.role == 'professional',
                    'is_commercial': user.role == 'commercial',
                }
                results.append(user_data)

            return Response({
                'results': results,
                'pagination': {
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_next': offset + limit < total_count,
                    'has_previous': offset > 0
                },
                'search_meta': {
                    'query': query,
                    'search_type': search_type,
                    'target_user_id': target_user_id,
                    'community_id': community_id
                }
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            logging.exception('User search failed')
            return Response({'error': 'User search failed', 'details': str(exc)}, status=status.HTTP_400_BAD_REQUEST)