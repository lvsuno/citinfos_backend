"""Comprehensive global search system with permission-aware filtering.

This module provides a unified search interface across all content types
while respecting user permissions and privacy settings.
"""

from typing import Dict, Any, List, Optional
from django.db.models import Q, QuerySet
from django.contrib.auth.models import User
from django.conf import settings
from django.core.paginator import Paginator
import redis
import json
from datetime import timedelta
from django.utils import timezone

# Import all searchable models
from content.models import Post
from accounts.models import UserProfile
# Equipment functionality removed
# from equipment.models import Equipment, EquipmentModel
from communities.models import Community, CommunityMembership
from messaging.models import Message, ChatRoom
from polls.models import Poll
from ai_conversations.models import AIConversation


class GlobalSearchEngine:
    """
    Comprehensive search engine that respects permissions and privacy.

    Features:
    - Cross-app content search
    - Permission-based filtering
    - Relevance scoring
    - Search result caching
    - Analytics tracking
    """

    def __init__(self, user: User):
        self.user = user
        self.user_profile = (getattr(user, 'userprofile', None)
                             if user and user.is_authenticated else None)
        redis_url = getattr(settings, 'REDIS_URL', None)
        self.redis_client = (redis.Redis.from_url(redis_url)
                             if redis_url else None)

    def search(
        self,
        query: str,
        content_types: List[str] = None,
        filters: Dict[str, Any] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Perform comprehensive search across all content types.

        Args:
            query: Search query string
            content_types: List of content types to search
            filters: Additional filters (visibility, date_range, etc.)
            limit: Maximum results per content type
            offset: Pagination offset

        Returns:
            Dict with search results, counts, and metadata
        """
        if not query or not query.strip():
            return self._empty_results()

        query = query.strip()
        content_types = content_types or [
            'posts', 'users', 'communities',
            'messages', 'polls', 'ai_conversations'
        ]
        filters = filters or {}

        # Check cache first
        cache_key = self._get_cache_key(
            query, content_types, filters, limit, offset
        )
        cached_results = self._get_cached_results(cache_key)
        if cached_results:
            return cached_results

        results = {}
        total_count = 0

        # Search each content type
        for content_type in content_types:
            search_method = getattr(self, f'_search_{content_type}', None)
            if search_method:
                try:
                    type_results = search_method(query, filters, limit, offset)
                    results[content_type] = type_results['results']
                    results[f'{content_type}_count'] = type_results['count']
                    total_count += type_results['count']
                except Exception:
                    # Log error and continue with other content types
                    results[content_type] = []
                    results[f'{content_type}_count'] = 0

        search_results = {
            'query': query,
            'results': results,
            'total_count': total_count,
            'content_types': content_types,
            'filters': filters,
            'limit': limit,
            'offset': offset,
            'timestamp': timezone.now().isoformat()
        }

        # Cache results
        self._cache_results(cache_key, search_results)

        # Track search analytics
        self._track_search(query, content_types, total_count)

        return search_results

    def _search_posts(
        self, query: str, filters: Dict, limit: int, offset: int
    ) -> Dict:
        """Search posts with permission filtering."""
        queryset = Post.objects.filter(is_deleted=False)

        # Apply text search
        search_q = (Q(content__icontains=query) |
                    Q(author__user__username__icontains=query))
        queryset = queryset.filter(search_q)

        # Apply permission filtering
        queryset = self._filter_posts_by_permission(queryset)

        # Apply additional filters
        if filters.get('post_type'):
            queryset = queryset.filter(post_type=filters['post_type'])

        if filters.get('community_id'):
            queryset = queryset.filter(community_id=filters['community_id'])

        if filters.get('date_range'):
            date_range = filters['date_range']
            now = timezone.now()
            if date_range == 'today':
                queryset = queryset.filter(created_at__date=now.date())
            elif date_range == 'week':
                queryset = queryset.filter(
                    created_at__gte=now - timedelta(days=7)
                )
            elif date_range == 'month':
                queryset = queryset.filter(
                    created_at__gte=now - timedelta(days=30)
                )

        # Order by relevance (engagement + recency)
        queryset = queryset.order_by('-trend_score', '-created_at')

        # Paginate
        paginator = Paginator(queryset, limit)
        page_num = (offset // limit) + 1
        page = paginator.get_page(page_num)

        return {
            'results': [self._serialize_post(post) for post in page],
            'count': paginator.count
        }

    def _search_users(
        self, query: str, filters: Dict, limit: int, offset: int
    ) -> Dict:
        """Search users/profiles."""
        queryset = UserProfile.objects.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(bio__icontains=query) |
            Q(city__name__icontains=query)
        )

        # Apply filters
        if filters.get('role'):
            queryset = queryset.filter(role=filters['role'])

        if filters.get('location'):
            queryset = queryset.filter(location__icontains=filters['location'])

        # Order by relevance (followers + activity)
        queryset = queryset.order_by('-follower_count', '-user__last_login')

        # Paginate
        paginator = Paginator(queryset, limit)
        page_num = (offset // limit) + 1
        page = paginator.get_page(page_num)

        return {
            'results': [self._serialize_user(user) for user in page],
            'count': paginator.count
        }

    # Equipment functionality removed

    def _search_communities(
        self, query: str, filters: Dict, limit: int, offset: int
    ) -> Dict:
        """Search communities with access control."""
        queryset = Community.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query),
            is_deleted=False
        )

        # Filter by accessibility
        if not (self.user and self.user.is_authenticated):
            # Anonymous users can only see public communities
            queryset = queryset.filter(community_type='public')
        else:
            # Authenticated users can see public + member communities
            user_communities = CommunityMembership.objects.filter(
                user=self.user_profile,
                status='active'
            ).values_list('community_id', flat=True)

            queryset = queryset.filter(
                Q(community_type='public') |
                Q(id__in=user_communities)
            )

        # Apply filters
        if filters.get('community_type'):
            queryset = queryset.filter(
                community_type=filters['community_type']
            )

        # Order by relevance
        queryset = queryset.order_by('-members_count', '-posts_count')

        # Paginate
        paginator = Paginator(queryset, limit)
        page_num = (offset // limit) + 1
        page = paginator.get_page(page_num)

        return {
            'results': [
                self._serialize_community(community) for community in page
            ],
            'count': paginator.count
        }

    def _search_messages(
        self, query: str, filters: Dict, limit: int, offset: int
    ) -> Dict:
        """Search messages (only in user's accessible chat rooms)."""
        if not (self.user and self.user.is_authenticated) or not self.user_profile:
            return {'results': [], 'count': 0}

        # Get user's chat rooms
        user_rooms = ChatRoom.objects.filter(participants=self.user_profile)

        queryset = Message.objects.filter(
            room__in=user_rooms,
            content__icontains=query,
            is_deleted=False
        )

        # Apply filters
        if filters.get('room_type'):
            queryset = queryset.filter(room__room_type=filters['room_type'])

        # Order by recency
        queryset = queryset.order_by('-created_at')

        # Paginate
        paginator = Paginator(queryset, limit)
        page_num = (offset // limit) + 1
        page = paginator.get_page(page_num)

        return {
            'results': [self._serialize_message(message) for message in page],
            'count': paginator.count
        }

    def _search_polls(
        self, query: str, filters: Dict, limit: int, offset: int
    ) -> Dict:
        """Search polls with permission filtering."""
        queryset = Poll.objects.filter(
            Q(question__icontains=query) |
            Q(post__content__icontains=query),
            is_active=True
        )

        # Apply permission filtering via posts
        accessible_posts = self._filter_posts_by_permission(
            Post.objects.filter(post_type='poll')
        )
        queryset = queryset.filter(post__in=accessible_posts)

        # Apply filters
        if filters.get('poll_status'):
            if filters['poll_status'] == 'active':
                queryset = queryset.filter(is_closed=False)
            elif filters['poll_status'] == 'closed':
                queryset = queryset.filter(is_closed=True)

        # Order by activity
        queryset = queryset.order_by('-total_votes', '-created_at')

        # Paginate
        paginator = Paginator(queryset, limit)
        page_num = (offset // limit) + 1
        page = paginator.get_page(page_num)

        return {
            'results': [self._serialize_poll(poll) for poll in page],
            'count': paginator.count
        }

    def _search_ai_conversations(
        self, query: str, filters: Dict, limit: int, offset: int
    ) -> Dict:
        """Search AI conversations (only user's own)."""
        if not (self.user and self.user.is_authenticated) or not self.user_profile:
            return {'results': [], 'count': 0}

        # Users can only search their own AI conversations
        queryset = AIConversation.objects.filter(
            user=self.user_profile,
            title__icontains=query
        )

        # Also search in AI messages
        message_conversations = AIConversation.objects.filter(
            user=self.user_profile,
            messages__content__icontains=query
        ).distinct()

        queryset = queryset.union(message_conversations)

        # Apply filters
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])

        # Order by recency
        queryset = queryset.order_by('-updated_at')

        # Paginate
        paginator = Paginator(queryset, limit)
        page_num = (offset // limit) + 1
        page = paginator.get_page(page_num)

        return {
            'results': [
                self._serialize_ai_conversation(conv) for conv in page
            ],
            'count': paginator.count
        }

    def _filter_posts_by_permission(self, queryset: QuerySet) -> QuerySet:
        """Apply permission-based filtering to posts."""
        if not (self.user and self.user.is_authenticated):
            # Anonymous users can only see public posts
            return queryset.filter(visibility='public')

        # Build permission query
        permission_q = Q(visibility='public')  # Public posts

        if self.user_profile:
            # User's own posts
            permission_q |= Q(author=self.user_profile)

            # Followers-only posts from users they follow
            following_ids = self.user_profile.following.values_list('followed_id', flat=True)
            permission_q |= Q(visibility='followers', author_id__in=following_ids)

            # Community posts from communities they're members of
            user_communities = CommunityMembership.objects.filter(
                user=self.user_profile,
                status='active'
            ).values_list('community_id', flat=True)
            permission_q |= Q(visibility='community', community_id__in=user_communities)

        return queryset.filter(permission_q)

    # Serialization methods
    def _serialize_post(self, post) -> Dict:
        """Serialize post for search results."""
        return {
            'id': str(post.id),
            'type': 'post',
            'title': post.content[:100] + ('...' if len(post.content) > 100 else ''),
            'content': post.content,
            'author': {
                'username': post.author.user.username,
                'display_name': post.author.display_name,
                'avatar': (post.author.profile_picture.url
                          if post.author.profile_picture else None)
            },
            'post_type': post.post_type,
            'visibility': post.visibility,
            'community': {
                'name': post.community.name,
                'slug': post.community.slug
            } if post.community else None,
            'engagement': {
                'likes': post.likes_count,
                'comments': post.comments_count,
                'shares': post.shares_count
            },
            'created_at': post.created_at.isoformat(),
            'url': f'/posts/{post.id}',
            'relevance_score': post.trend_score
        }

    def _serialize_user(self, user_profile) -> Dict:
        """Serialize user profile for search results."""
        return {
            'id': str(user_profile.id),
            'type': 'user',
            'username': user_profile.user.username,
            'display_name': user_profile.display_name,
            'bio': user_profile.bio[:200] + ('...' if len(user_profile.bio or '') > 200 else ''),
            'avatar': (user_profile.profile_picture.url
                      if user_profile.profile_picture else None),
            'role': user_profile.role,
            'location': user_profile.administrative_division.name if user_profile.administrative_division else None,
            'stats': {
                'followers': user_profile.follower_count,
                'following': user_profile.following_count,
                'posts': user_profile.posts.count()
            },
            'created_at': user_profile.created_at.isoformat(),
            'url': f'/profile/{user_profile.user.username}',
            'is_verified': user_profile.is_verified,
            'relevance_score': user_profile.follower_count
        }

    # Equipment serialization methods removed

    def _serialize_community(self, community) -> Dict:
        """Serialize community for search results."""
        return {
            'id': str(community.id),
            'type': 'community',
            'name': community.name,
            'description': community.description[:200] + ('...' if len(community.description or '') > 200 else ''),
            'slug': community.slug,
            'community_type': community.community_type,
            'creator': {
                'username': community.creator.user.username,
                'display_name': community.creator.get_display_name()
            },
            'stats': {
                'members': community.members_count,
                'posts': community.posts_count
            },
            'tags': community.tags,
            'avatar': community.avatar.url if community.avatar else None,
            'created_at': community.created_at.isoformat(),
            'url': f'/c/{community.slug}',
            'relevance_score': community.members_count
        }

    def _serialize_message(self, message) -> Dict:
        """Serialize message for search results."""
        return {
            'id': str(message.id),
            'type': 'message',
            'content': message.content[:200] + ('...' if len(message.content) > 200 else ''),
            'sender': {
                'username': message.sender.user.username,
                'display_name': message.sender.get_display_name()
            },
            'room': {
                'id': str(message.room.id),
                'name': message.room.name,
                'type': message.room.room_type
            },
            'message_type': message.message_type,
            'created_at': message.created_at.isoformat(),
            'url': f'/messages/{message.room.id}#{message.id}',
            'relevance_score': 1.0
        }

    def _serialize_poll(self, poll) -> Dict:
        """Serialize poll for search results."""
        return {
            'id': str(poll.id),
            'type': 'poll',
            'question': poll.question,
            'post': {
                'id': str(poll.post.id),
                'content': poll.post.content[:100] + ('...' if len(poll.post.content) > 100 else ''),
                'author': {
                    'username': poll.post.author.user.username,
                    'display_name': poll.post.author.get_display_name()
                }
            },
            'settings': {
                'multiple_choice': poll.multiple_choice,
                'anonymous_voting': poll.anonymous_voting
            },
            'stats': {
                'total_votes': poll.total_votes,
                'voters_count': poll.voters_count
            },
            'expires_at': poll.expires_at.isoformat() if poll.expires_at else None,
            'is_expired': poll.is_expired,
            'is_closed': poll.is_closed,
            'created_at': poll.created_at.isoformat(),
            'url': f'/posts/{poll.post.id}',
            'relevance_score': poll.total_votes
        }

    def _serialize_ai_conversation(self, conversation) -> Dict:
        """Serialize AI conversation for search results."""
        return {
            'id': str(conversation.id),
            'type': 'ai_conversation',
            'title': conversation.title,
            'status': conversation.status,
            'message_count': conversation.message_count,
            'last_activity': conversation.updated_at.isoformat(),
            'created_at': conversation.created_at.isoformat(),
            'url': f'/ai/conversations/{conversation.id}',
            'relevance_score': conversation.message_count
        }

    # Caching methods
    def _get_cache_key(self, query: str, content_types: List[str], filters: Dict, limit: int, offset: int) -> str:
        """Generate cache key for search results."""
        user_id = (str(self.user.id) if self.user and self.user and self.user.is_authenticated
                   else 'anonymous')
        content_types_str = ','.join(sorted(content_types))
        filters_str = json.dumps(filters, sort_keys=True)
        return f'search:{user_id}:{hash(query)}:{hash(content_types_str)}:{hash(filters_str)}:{limit}:{offset}'

    def _get_cached_results(self, cache_key: str) -> Optional[Dict]:
        """Get cached search results."""
        if not self.redis_client:
            return None

        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached.decode())
        except Exception:
            pass
        return None

    def _cache_results(self, cache_key: str, results: Dict, ttl: int = 300) -> None:
        """Cache search results for 5 minutes."""
        if not self.redis_client:
            return

        try:
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(results, default=str)
            )
        except Exception:
            pass

    def _track_search(self, query: str, content_types: List[str], result_count: int) -> None:
        """Track search for analytics."""
        if not (self.user and self.user.is_authenticated) or not self.user_profile:
            return

        try:
            from .models import UserSearchQuery

            # Create search query record for the primary content type
            primary_type = content_types[0] if content_types else 'other'

            UserSearchQuery.objects.create(
                user=self.user_profile,
                query=query[:255],  # Truncate if too long
                search_type=primary_type,
                filters={'content_types': content_types},
                results_count=result_count
            )
        except Exception:
            pass

    def _empty_results(self) -> Dict:
        """Return empty search results."""
        return {
            'query': '',
            'results': {},
            'total_count': 0,
            'content_types': [],
            'filters': {},
            'limit': 0,
            'offset': 0,
            'timestamp': timezone.now().isoformat()
        }


# Convenience functions
def global_search(user: User, query: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for global search."""
    engine = GlobalSearchEngine(user)
    return engine.search(query, **kwargs)


def search_by_type(user: User, query: str, content_type: str, **kwargs) -> Dict[str, Any]:
    """Search specific content type."""
    engine = GlobalSearchEngine(user)
    return engine.search(query, content_types=[content_type], **kwargs)
