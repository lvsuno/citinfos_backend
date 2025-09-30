"""
Public profile views that don't require authentication.
These views allow anyone to view public user profiles and their public content.
Enhanced with server-side context filtering.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import UserProfile
from .serializers import UserProfileSerializer
from .profile_context import get_profile_context
from content.models import Post
from content.unified_serializers import UnifiedPostSerializer


class PublicUserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only access to user profiles with context-aware filtering.
    Only shows public profiles without requiring authentication.
    Automatically filters content based on viewing context.
    """
    queryset = UserProfile.objects.filter(is_deleted=False, is_private=False)
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        """Only return public, non-deleted profiles."""
        return UserProfile.objects.filter(
            is_deleted=False,
            is_private=False
        ).select_related('user')

    def retrieve(self, request, *args, **kwargs):
        """
        Context-aware profile retrieval.
        Returns profile data with interaction permissions and filtered content.
        """
        profile = self.get_object()
        context = get_profile_context(profile, request)

        # Check if profile can be viewed
        if not context.can_view_profile():
            return Response(
                {'error': 'Profile not found or is private'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Serialize profile data
        serializer = self.get_serializer(profile)
        profile_data = serializer.data

        # Add context data for frontend
        profile_data['context'] = context.get_context_data()

        # Add recent posts if allowed (limit to 3 for profile view)
        if context.can_view_posts():
            post_filter = context.get_post_visibility_filter()
            posts = Post.objects.filter(**post_filter).select_related(
                'author__user'
            ).prefetch_related(
                'media', 'polls'
            ).order_by('-created_at')[:3]

            posts_serializer = UnifiedPostSerializer(
                posts, many=True, context={'request': request}
            )
            profile_data['recent_posts'] = posts_serializer.data
        else:
            profile_data['recent_posts'] = []

        # Badges are only visible to profile owner (which is never the case
        # for public endpoints)
        profile_data['badges_visible'] = context.can_view_badges()

        return Response(profile_data)

    @action(detail=True, methods=['get'], url_path='posts')
    def posts(self, request, pk=None):
        """
        Get posts by this user with context-aware filtering.
        Returns more posts than the profile view (up to 20).
        """
        profile = self.get_object()
        context = get_profile_context(profile, request)

        # Check permissions
        if not context.can_view_posts():
            return Response(
                {'error': 'Posts not available'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get posts with context-aware filtering
        post_filter = context.get_post_visibility_filter()
        posts = Post.objects.filter(**post_filter).select_related(
            'author__user'
        ).prefetch_related(
            'media', 'polls'
        ).order_by('-created_at')[:20]

        # Serialize posts
        serializer = UnifiedPostSerializer(
            posts, many=True, context={'request': request}
        )

        return Response({
            'results': serializer.data,
            'count': len(serializer.data),
            'context': context.get_context_data()
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def public_profile_by_username(request, username):
    """
    Get a public user profile by username with context filtering.
    ⚠️ WARNING: Should only be used for search - multiple users can have
    the same username!
    """
    try:
        # Find public profiles with this username
        profiles = UserProfile.objects.filter(
            user__username=username,
            is_deleted=False,
            is_private=False
        )

        if not profiles.exists():
            return Response(
                {'error': 'No public profiles found with this username'},
                status=status.HTTP_404_NOT_FOUND
            )

        # If multiple profiles exist, return the first one with a warning
        profile = profiles.first()
        context = get_profile_context(profile, request)

        if not context.can_view_profile():
            return Response(
                {'error': 'Profile not found or is private'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserProfileSerializer(
            profile, context={'request': request}
        )
        response_data = serializer.data
        response_data['context'] = context.get_context_data()

        # Add warning if multiple profiles exist
        if profiles.count() > 1:
            response_data['warning'] = (
                f'Multiple users found with username "{username}". '
                f'Showing first match. Use UUID for specific access.'
            )

        return Response(response_data)

    except Exception:
        return Response(
            {'error': 'Profile not found or is private'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def public_user_posts(request, user_id):
    """
    Get public posts by a specific user with context filtering.
    Only returns posts based on viewing permissions.
    """
    try:
        profile = get_object_or_404(
            UserProfile,
            id=user_id,
            is_deleted=False,
            is_private=False
        )

        context = get_profile_context(profile, request)

        # Check if posts can be viewed
        if not context.can_view_posts():
            return Response(
                {'error': 'Posts not available'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get posts with context-aware filtering
        post_filter = context.get_post_visibility_filter()
        posts = Post.objects.filter(**post_filter).select_related(
            'author__user'
        ).prefetch_related(
            'media', 'polls'
        ).order_by('-created_at')[:20]

        serializer = UnifiedPostSerializer(
            posts, many=True, context={'request': request}
        )

        return Response({
            'results': serializer.data,
            'count': len(serializer.data),
            'context': context.get_context_data()
        })

    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User not found or profile is private'},
            status=status.HTTP_404_NOT_FOUND
        )
