"""
Enhanced views for unified attachment system and multiple polls support.

These views demonstrate how to use the new unified attachment system
alongside the existing API structure.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import models
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.conf import settings

from content.models import Post, PostMedia, Hashtag
from content.permissions import IsAuthenticatedOrPublicContent
from content.utils import process_repost_comment_mentions
from polls.models import PollOption
from accounts.models import UserProfile
from accounts.utils import get_active_profile_or_404
from content.unified_serializers import (
    UnifiedPostSerializer,
    UnifiedPostCreateUpdateSerializer,
    EnhancedPostMediaSerializer,
    EnhancedPollSerializer
)


class UnifiedPostViewSet(viewsets.ModelViewSet):
    """
    Enhanced PostViewSet with unified attachment and multiple polls support.

    This viewset provides:
    1. Unified attachment handling via PostMedia
    2. Multiple polls per post
    3. Backward compatibility during migration
    4. Enhanced attachment management endpoints
    """

    queryset = Post.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Allow public access for list and retrieve, require auth for modifications
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UnifiedPostCreateUpdateSerializer
        return UnifiedPostSerializer

    def get_queryset(self):
        """
        Get optimized queryset with all related data.
        Filter by community (which has relationship with division).
        Handles both direct division->community and child division (arrondissement) cases.
        """
        queryset = Post.objects.select_related(
            'author__user', 'community', 'community__division'
        ).prefetch_related(
            'media',  # PostMedia attachments
            'polls__options',  # Multiple polls with options
            'child_reposts', 'comments'
        ).filter(is_deleted=False)

        # Filter by community ID (preferred method)
        community_id = self.request.query_params.get('community_id')
        if community_id:
            # Try to find community directly by ID
            from communities.models import Community
            try:
                community = Community.objects.get(id=community_id)
                queryset = queryset.filter(community=community)
            except Community.DoesNotExist:
                # If community_id doesn't exist as a community,
                # it might be a division ID - try to find community by division
                from core.models import AdministrativeDivision
                try:
                    division = AdministrativeDivision.objects.get(id=community_id)
                    # First try to find community for this division
                    try:
                        community = Community.objects.get(division=division)
                        queryset = queryset.filter(community=community)
                    except Community.DoesNotExist:
                        # If no community for this division, try parent division
                        # (for arrondissements/subdivisions)
                        if division.parent:
                            try:
                                community = Community.objects.get(division=division.parent)
                                queryset = queryset.filter(community=community)
                            except Community.DoesNotExist:
                                # No community found, return empty queryset
                                queryset = queryset.none()
                        else:
                            # No parent and no community, return empty queryset
                            queryset = queryset.none()
                except AdministrativeDivision.DoesNotExist:
                    # Invalid ID altogether
                    queryset = queryset.none()

        # Filter by community slug
        community_slug = self.request.query_params.get('community')
        if community_slug and not community_id:
            queryset = queryset.filter(community__slug=community_slug)

        # Filter by rubrique template (either ID or template_type)
        rubrique_id = self.request.query_params.get('rubrique_id')
        rubrique_slug = (
            self.request.query_params.get('rubrique') or
            self.request.query_params.get('rubrique_slug')
        )

        if rubrique_id:
            # Filter by rubrique UUID
            queryset = queryset.filter(rubrique_template_id=rubrique_id)
        elif rubrique_slug:
            # Filter by rubrique template_type (slug)
            # Special case: "accueil" shows ALL posts (no filter)
            if rubrique_slug.lower() != 'accueil':
                queryset = queryset.filter(
                    rubrique_template__template_type=rubrique_slug
                )

        return queryset

    def list(self, request, *args, **kwargs):
        """
        List posts with community filtering.
        All posts must belong to a community.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Apply ordering
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """
        Set the post author to current user.
        Ensure all posts belong to a community.
        """
        # Create an author profile if it doesn't exist
        author_profile, created = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={'display_name': self.request.user.username}
        )

        # Validate that a community is provided
        community = serializer.validated_data.get('community')
        if not community:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'community': 'All posts must belong to a community.'
            })

        serializer.save(author=author_profile)

    def update(self, request, *args, **kwargs):
        """Custom update that returns read format."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Use update serializer for processing the request
        update_serializer = UnifiedPostCreateUpdateSerializer(
            instance, data=request.data, partial=partial
        )
        update_serializer.is_valid(raise_exception=True)
        instance = update_serializer.save()

        # Refresh instance from database to get updated related data
        instance.refresh_from_db()

        # Also refresh related polls and options explicitly
        instance = self.get_queryset().get(pk=instance.pk)

        # Return data using read serializer
        read_serializer = UnifiedPostSerializer(
            instance, context={'request': request}
        )
        return Response(read_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Custom partial update that returns read format."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        """Soft delete posts with cascading deletion of related objects."""
        if instance.author.user != self.request.user and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own posts")

        # Cascade soft delete post and all related objects
        from core.cascade_deletion import cascade_soft_delete_post
        cascade_soft_delete_post(instance)

    @action(detail=True, methods=['get'])
    @method_decorator(xframe_options_exempt)
    def attachments(self, request, pk=None):
        """Get all attachments for a post."""
        post = self.get_object()
        attachments = post.media.all()
        serializer = EnhancedPostMediaSerializer(
            attachments, many=True, context={'request': request}
        )
        resp = Response({
            'count': len(attachments),
            'attachments': serializer.data,
            'attachments_by_type': post.attachments_by_type
        })

        # Build CSP frame-ancestors header from trusted origins + self.
        trusted = getattr(settings, 'CSRF_TRUSTED_ORIGINS', []) or []
        if isinstance(trusted, str):
            trusted = [trusted]
        # Ensure we always allow same-origin framing and explicitly allow trusted origins
        sources = ["'self'"] + [o for o in trusted if o]
        resp['Content-Security-Policy'] = 'frame-ancestors ' + ' '.join(sources)
        return resp

    @action(detail=True, methods=['post'])
    def add_attachment(self, request, pk=None):
        """Add a new attachment to a post."""
        # Debug logging for authentication issues

        post = self.get_object()

        # Check permissions
        if post.author.user != request.user and not request.user.is_staff:

            return Response(
                {'error': 'You can only add attachments to your own posts'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check attachment limit
        if not post.can_add_attachment():
            return Response(
                {'error': 'Maximum number of attachments reached'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create attachment

        serializer = EnhancedPostMediaSerializer(
            data=request.data, context={'request': request}
        )

        if serializer.is_valid():
            # Save with just the post reference - order comes from request data
            serializer.save(post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_attachment(self, request, pk=None):
        """Remove an attachment from a post."""
        post = self.get_object()
        attachment_id = request.data.get('attachment_id')

        if not attachment_id:
            return Response(
                {'error': 'attachment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            attachment = post.media.get(id=attachment_id)
        except PostMedia.DoesNotExist:
            return Response(
                {'error': 'Attachment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions
        if post.author.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only remove attachments from your own posts'},
                status=status.HTTP_403_FORBIDDEN
            )

        attachment.delete()
        return Response(
            {'message': 'Attachment removed successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def polls(self, request, pk=None):
        """Get all polls for a post."""
        post = self.get_object()
        polls = post.polls.filter(is_deleted=False)
        serializer = EnhancedPollSerializer(
            polls, many=True, context={'request': request}
        )
        return Response({
            'count': len(polls),
            'polls': serializer.data
        })

    @action(detail=True, methods=['post'])
    def add_poll(self, request, pk=None):
        """Add a new poll to a post."""
        post = self.get_object()

        # Check permissions
        if post.author.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only add polls to your own posts'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check poll limit
        if not post.can_add_poll():
            return Response(
                {'error': 'Maximum number of polls reached'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create poll
        serializer = EnhancedPollSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            # Set order as next in sequence
            next_order = (post.polls.count() + 1)
            poll = serializer.save(post=post, order=next_order)

            # Create poll options if provided
            options_data = request.data.get('options', [])
            for i, option_data in enumerate(options_data):
                PollOption.objects.create(
                    poll=poll,
                    text=option_data.get('text', ''),
                    order=i + 1
                )

            # Return poll with options
            response_serializer = EnhancedPollSerializer(
                poll, context={'request': request}
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def migrate_legacy_media(self, request, pk=None):
        """Migrate legacy media fields to PostMedia for a specific post."""
        post = self.get_object()

        # Check permissions
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can trigger migration'},
                status=status.HTTP_403_FORBIDDEN
            )

        if post.media_migrated_to_postmedia:
            return Response(
                {'message': 'Post already migrated'},
                status=status.HTTP_200_OK
            )

        try:
            post.migrate_legacy_media_to_postmedia()
            return Response(
                {
                    'message': 'Legacy media migrated successfully',
                    'migrated_files': post.legacy_media_backup
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': f'Migration failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def migration_status(self, request):
        """Get migration status for all posts."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can view migration status'},
                status=status.HTTP_403_FORBIDDEN
            )

        total_posts = Post.objects.count()
        migrated_posts = Post.objects.filter(
            media_migrated_to_postmedia=True
        ).count()
        pending_posts = Post.objects.filter(
            media_migrated_to_postmedia=False
        ).filter(
            models.Q(image__isnull=False) |
            models.Q(video__isnull=False) |
            models.Q(audio__isnull=False) |
            models.Q(file__isnull=False)
        ).count()

        return Response({
            'total_posts': total_posts,
            'migrated_posts': migrated_posts,
            'pending_migration': pending_posts,
            'migration_progress': (
                (migrated_posts / total_posts * 100)
                if total_posts > 0 else 100
            )
        })

    @action(detail=False, methods=['post'])
    def bulk_create_with_attachments(self, request):
        """
        Create multiple posts with attachments in a single request.

        Example payload:
        {
            "posts": [
                {
                    "content": "Post 1",
                    "attachments": [
                        {"media_type": "image", "file": "..."},
                        {"media_type": "video", "file": "..."}
                    ],
                    "polls": [
                        {
                            "question": "What do you think?",
                            "options": [
                                {"text": "Option 1"},
                                {"text": "Option 2"}
                            ]
                        }
                    ]
                }
            ]
        }
        """
        posts_data = request.data.get('posts', [])
        if not posts_data:
            return Response(
                {'error': 'posts array is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_posts = []
        errors = []

        for i, post_data in enumerate(posts_data):
            serializer = UnifiedPostCreateUpdateSerializer(
                data=post_data, context={'request': request}
            )
            if serializer.is_valid():
                user_profile = get_object_or_404(
                    UserProfile, user=request.user
                )
                post = serializer.save(author=user_profile)
                created_posts.append({
                    'index': i,
                    'post_id': str(post.id),
                    'success': True
                })
            else:
                errors.append({
                    'index': i,
                    'errors': serializer.errors
                })

        return Response({
            'created_posts': created_posts,
            'errors': errors,
            'success_count': len(created_posts),
            'error_count': len(errors)
        }, status=status.HTTP_201_CREATED if created_posts else status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def feed(self, request):
        """
        Get a combined feed of original posts and reposts.

        Returns posts in chronological order, including:
        - Original posts by followed users
        - Reposts by followed users (with repost metadata)
        """
        from accounts.models import Follow

        user_profile = get_object_or_404(UserProfile, user=request.user)

        # Get list of users that current user follows (including self)
        following_users = Follow.objects.filter(
            follower=user_profile,
            is_deleted=False
        ).values_list('followed', flat=True)

        # Include the user's own posts
        followed_user_ids = list(following_users) + [user_profile.id]

        # Get regular posts from followed users (excluding reposts)
        posts_queryset = self.get_queryset().filter(
            author__id__in=followed_user_ids,
            parent_post__isnull=True  # Exclude reposts
        ).order_by('-created_at')

        # Get repost posts: only from followed users
        repost_posts_queryset = Post.objects.filter(
            author__id__in=followed_user_ids,  # Only from followed users
            post_type__in=[
                'repost', 'repost_with_media', 'repost_quote', 'repost_remix'
            ],
            is_deleted=False,
            parent_post__isnull=False  # Only reposts
        ).select_related(
            'author__user', 'parent_post__author__user'
        ).prefetch_related(
            'parent_post__media',
            'parent_post__polls__options',
            'parent_post__comments'
        ).order_by('-created_at')

        # Keep track of original post IDs that will be shown as reposts
        # to avoid duplicating them as regular posts
        reposted_original_ids = set()
        for repost_post in repost_posts_queryset:
            if repost_post.parent_post and not repost_post.parent_post.is_deleted:
                # Always exclude reposted content to prevent duplicates
                reposted_original_ids.add(repost_post.parent_post.id)

        # Filter out original posts that are being reposted
        posts_queryset = posts_queryset.exclude(id__in=reposted_original_ids)

        # Combine and sort by creation time
        combined_feed = []

        # Add original posts
        for post in posts_queryset:
            serializer = UnifiedPostSerializer(
                post, context={'request': request}
            )
            combined_feed.append({
                'type': 'post',
                'created_at': post.created_at.isoformat(),
                'data': serializer.data
            })

        # Add reposts (now as Post objects)
        reposts_added = 0
        for repost_post in repost_posts_queryset:
            # Only include if the parent post still exists and isn't deleted
            if repost_post.parent_post and not repost_post.parent_post.is_deleted:
                reposts_added += 1
                # Serialize the parent post (original content)
                parent_serializer = UnifiedPostSerializer(
                    repost_post.parent_post, context={'request': request}
                )

                # Get reposter info
                display_name = (repost_post.author.display_name or
                                repost_post.author.user.username)

                # Process mentions in repost comment
                repost_mention_mappings = process_repost_comment_mentions(
                    repost_post.content or ""
                )

                combined_feed.append({
                    'type': 'repost',
                    'created_at': repost_post.created_at.isoformat(),
                    'repost_id': str(repost_post.id),
                    'reposted_by': {
                        'id': str(repost_post.author.id),
                        'username': repost_post.author.user.username,
                        'display_name': display_name,
                    },
                    'repost_comment': repost_post.content or "",
                    'repost_mentions': repost_mention_mappings,
                    'data': parent_serializer.data  # Original post data
                })

        # Sort combined feed by creation time (newest first)
        combined_feed.sort(key=lambda x: x['created_at'], reverse=True)

        # Apply pagination if needed
        page = 1
        page_size = 20

        # Handle both DRF and Django request objects
        if hasattr(request, 'query_params'):
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
        elif hasattr(request, 'GET'):
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        paginated_feed = combined_feed[start_idx:end_idx]

        return Response({
            'results': paginated_feed,
            'count': len(combined_feed),
            'page': page,
            'page_size': page_size,
            'has_next': end_idx < len(combined_feed),
            'has_previous': page > 1
        })

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def user_posts(self, request):
        """
        Get posts by a specific user (authenticated endpoint).

        Query parameters:
        - author: User profile ID to get posts for
        - page: Page number (default: 1)
        - page_size: Number of posts per page (default: 20)
        """
        author_id = request.query_params.get('author')
        if not author_id:
            return Response(
                {'error': 'author parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the target user profile (only non-deleted)
            target_profile = get_active_profile_or_404(id=author_id)
            current_user_profile = get_active_profile_or_404(user=request.user)

            # Permission check: users can always see their own posts
            # For other users, check if profile is public or if following
            if target_profile.id != current_user_profile.id:
                # Check if target profile is private
                is_private = (hasattr(target_profile, 'is_private') and
                              target_profile.is_private)
                if is_private:
                    # Check if current user follows the target user
                    from accounts.models import Follow
                    is_following = Follow.objects.filter(
                        follower=current_user_profile,
                        followed=target_profile,
                        is_deleted=False
                    ).exists()

                    if not is_following:
                        return Response(
                            {'error': 'This profile is private'},
                            status=status.HTTP_403_FORBIDDEN
                        )

            # Get posts by the target user
            posts_queryset = self.get_queryset().filter(
                author=target_profile,
                # Exclude reposts, get original posts only
                parent_post__isnull=True
            ).order_by('-created_at')

            # Apply pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))

            from django.core.paginator import Paginator
            paginator = Paginator(posts_queryset, page_size)
            page_obj = paginator.get_page(page)

            # Serialize the posts
            serializer = UnifiedPostSerializer(
                page_obj.object_list,
                many=True,
                context={'request': request}
            )

            return Response({
                'results': serializer.data,
                'count': paginator.count,
                'page': page,
                'page_size': page_size,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'total_pages': paginator.num_pages
            })

        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def drafts(self, request):
        """
        Get all draft posts for the current user.

        Query parameters:
        - page: Page number (default: 1)
        - page_size: Number of drafts per page (default: 20)
        """
        try:
            current_user_profile = get_active_profile_or_404(user=request.user)

            # Get drafts by the current user, only article type
            drafts_queryset = self.get_queryset().filter(
                author=current_user_profile,
                is_draft=True,
                post_type='article'
            ).order_by('-updated_at')

            # Apply pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))

            from django.core.paginator import Paginator
            paginator = Paginator(drafts_queryset, page_size)
            page_obj = paginator.get_page(page)

            # Serialize the drafts
            serializer = UnifiedPostSerializer(
                page_obj.object_list,
                many=True,
                context={'request': request}
            )

            return Response({
                'results': serializer.data,
                'count': paginator.count,
                'page': page,
                'page_size': page_size,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'total_pages': paginator.num_pages
            })

        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def publish_draft(self, request, pk=None):
        """
        Publish a draft post (set is_draft to False).

        Only the author can publish their own drafts.
        """
        draft = self.get_object()

        # Check if the current user is the author
        current_user_profile = get_active_profile_or_404(user=request.user)
        if draft.author.id != current_user_profile.id:
            return Response(
                {'error': 'You can only publish your own drafts'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if it's actually a draft
        if not draft.is_draft:
            return Response(
                {'error': 'This post is already published'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Publish the draft
        draft.is_draft = False
        draft.save()

        # Return the published post
        serializer = UnifiedPostSerializer(draft, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def upvote(self, request, pk=None):
        """
        Upvote a post in a thread (Stack Overflow style).
        Users can toggle their upvote.
        """
        from django.db.models import F
        from content.models import PostReaction

        post = self.get_object()
        user_profile = get_active_profile_or_404(user=request.user)

        # Check if post is in a thread
        if not post.thread:
            return Response(
                {'error': 'Upvoting is only available for posts in threads'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already upvoted
        existing_upvote = PostReaction.objects.filter(
            post=post,
            user=user_profile,
            reaction_type='upvote',
            is_deleted=False
        ).first()

        if existing_upvote:
            # Remove upvote (toggle)
            existing_upvote.delete()
            post.upvotes_count = max(0, post.upvotes_count - 1)
            post.save(update_fields=['upvotes_count'])
            action = 'removed'
        else:
            # Remove any existing downvote first
            PostReaction.objects.filter(
                post=post,
                user=user_profile,
                reaction_type='downvote',
                is_deleted=False
            ).delete()

            # Add upvote
            PostReaction.objects.create(
                post=post,
                user=user_profile,
                reaction_type='upvote'
            )
            post.upvotes_count = F('upvotes_count') + 1
            if post.downvotes_count > 0:
                post.downvotes_count = F('downvotes_count') - 1
            post.save(update_fields=['upvotes_count', 'downvotes_count'])
            action = 'added'

        post.refresh_from_db()
        serializer = UnifiedPostSerializer(post, context={'request': request})
        return Response({
            'action': action,
            'upvotes_count': post.upvotes_count,
            'downvotes_count': post.downvotes_count,
            'post': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def downvote(self, request, pk=None):
        """
        Downvote a post in a thread (Stack Overflow style).
        Users can toggle their downvote.
        """
        from django.db.models import F
        from content.models import PostReaction

        post = self.get_object()
        user_profile = get_active_profile_or_404(user=request.user)

        # Check if post is in a thread
        if not post.thread:
            return Response(
                {'error': 'Downvoting is only available for posts in threads'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already downvoted
        existing_downvote = PostReaction.objects.filter(
            post=post,
            user=user_profile,
            reaction_type='downvote',
            is_deleted=False
        ).first()

        if existing_downvote:
            # Remove downvote (toggle)
            existing_downvote.delete()
            post.downvotes_count = max(0, post.downvotes_count - 1)
            post.save(update_fields=['downvotes_count'])
            action = 'removed'
        else:
            # Remove any existing upvote first
            PostReaction.objects.filter(
                post=post,
                user=user_profile,
                reaction_type='upvote',
                is_deleted=False
            ).delete()

            # Add downvote
            PostReaction.objects.create(
                post=post,
                user=user_profile,
                reaction_type='downvote'
            )
            post.downvotes_count = F('downvotes_count') + 1
            if post.upvotes_count > 0:
                post.upvotes_count = F('upvotes_count') - 1
            post.save(update_fields=['downvotes_count', 'upvotes_count'])
            action = 'added'

        post.refresh_from_db()
        serializer = UnifiedPostSerializer(post, context={'request': request})
        return Response({
            'action': action,
            'upvotes_count': post.upvotes_count,
            'downvotes_count': post.downvotes_count,
            'post': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def mark_best_post(self, request, pk=None):
        """
        Mark a post as the best post in a thread.
        Only the thread creator can mark best posts.
        """
        from communities.models import Thread

        post = self.get_object()
        user_profile = get_active_profile_or_404(user=request.user)

        # Check if post is in a thread
        if not post.thread:
            return Response(
                {'error': 'Only posts in threads can be marked as best'},
                status=status.HTTP_400_BAD_REQUEST
            )

        thread = post.thread

        # Check if current user is the thread creator
        if thread.creator.id != user_profile.id:
            return Response(
                {'error': 'Only the thread creator can mark best posts'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Toggle best post
        if post.is_best_post:
            # Unmark as best post
            post.is_best_post = False
            post.save(update_fields=['is_best_post'])
            thread.best_post = None
            thread.save(update_fields=['best_post'])
            action = 'unmarked'
        else:
            # Unmark previous best post if exists
            if thread.best_post:
                previous_best = thread.best_post
                previous_best.is_best_post = False
                previous_best.save(update_fields=['is_best_post'])

            # Mark new best post
            post.is_best_post = True
            post.save(update_fields=['is_best_post'])
            thread.best_post = post
            thread.save(update_fields=['best_post'])
            action = 'marked'

        serializer = UnifiedPostSerializer(post, context={'request': request})
        return Response({
            'action': action,
            'is_best_post': post.is_best_post,
            'post': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def toggle_pin(self, request, pk=None):
        """
        Pin/unpin a post in a thread.
        Only the thread creator can pin posts.
        """
        post = self.get_object()
        user_profile = get_active_profile_or_404(user=request.user)

        # Check if post is in a thread
        if not post.thread:
            return Response(
                {'error': 'Only posts in threads can be pinned'},
                status=status.HTTP_400_BAD_REQUEST
            )

        thread = post.thread

        # Check if current user is the thread creator
        if thread.creator.id != user_profile.id:
            return Response(
                {'error': 'Only the thread creator can pin posts'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Toggle pin
        post.is_pinned = not post.is_pinned
        post.save(update_fields=['is_pinned'])

        serializer = UnifiedPostSerializer(post, context={'request': request})
        return Response({
            'action': 'pinned' if post.is_pinned else 'unpinned',
            'is_pinned': post.is_pinned,
            'post': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def react(self, request, pk=None):
        """React to a post with an emoji reaction.

        Updates reaction type if already exists.
        """
        from django.db import transaction
        from django.db.models import F
        from content.models import PostReaction

        post = self.get_object()
        user_profile = get_object_or_404(UserProfile, user=request.user)
        reaction_type = request.data.get('reaction_type', 'like')

        # Validate reaction type
        valid_reactions = [r[0] for r in PostReaction.REACTION_TYPES]
        if reaction_type not in valid_reactions:
            return Response(
                {'error': f'Invalid reaction type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Get existing reaction if any
            existing_reaction = PostReaction.objects.filter(
                user=user_profile,
                post=post,
                is_deleted=False
            ).first()

            # Track old sentiment for counter adjustment
            old_sentiment = None
            if existing_reaction:
                if existing_reaction.reaction_type in PostReaction.POSITIVE_REACTIONS:
                    old_sentiment = 'positive'
                elif existing_reaction.reaction_type in PostReaction.NEGATIVE_REACTIONS:
                    old_sentiment = 'negative'

            # Create or update reaction
            reaction, created = PostReaction.objects.update_or_create(
                user=user_profile,
                post=post,
                defaults={'reaction_type': reaction_type, 'is_deleted': False}
            )

            # Determine new sentiment
            new_sentiment = None
            if reaction_type in PostReaction.POSITIVE_REACTIONS:
                new_sentiment = 'positive'
            elif reaction_type in PostReaction.NEGATIVE_REACTIONS:
                new_sentiment = 'negative'

            # Update counters if sentiment changed
            if old_sentiment != new_sentiment:
                if old_sentiment == 'positive':
                    Post.objects.filter(pk=post.pk, likes_count__gt=0).update(
                        likes_count=F('likes_count') - 1
                    )
                elif old_sentiment == 'negative':
                    Post.objects.filter(
                        pk=post.pk, dislikes_count__gt=0
                    ).update(
                        dislikes_count=F('dislikes_count') - 1
                    )

                if new_sentiment == 'positive':
                    Post.objects.filter(pk=post.pk).update(
                        likes_count=F('likes_count') + 1
                    )
                elif new_sentiment == 'negative':
                    Post.objects.filter(pk=post.pk).update(
                        dislikes_count=F('dislikes_count') + 1
                    )

                post.refresh_from_db(fields=['likes_count', 'dislikes_count'])

        # Get emoji for response
        emoji = dict(PostReaction.REACTION_TYPES).get(reaction_type, '')

        # Return updated post data
        serializer = self.get_serializer(post)
        return Response({
            'message': f'Reacted with {emoji}',
            'reaction_type': reaction_type,
            'emoji': emoji,
            'post': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unreact(self, request, pk=None):
        """Remove user's reaction from a post."""
        from django.db import transaction
        from django.db.models import F
        from content.models import PostReaction

        post = self.get_object()
        user_profile = get_object_or_404(UserProfile, user=request.user)

        with transaction.atomic():
            reaction = PostReaction.objects.filter(
                user=user_profile,
                post=post,
                is_deleted=False
            ).first()

            if not reaction:
                return Response(
                    {'message': 'No reaction to remove'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Update counters based on reaction sentiment
            if reaction.reaction_type in PostReaction.POSITIVE_REACTIONS:
                Post.objects.filter(pk=post.pk, likes_count__gt=0).update(
                    likes_count=F('likes_count') - 1
                )
            elif reaction.reaction_type in PostReaction.NEGATIVE_REACTIONS:
                Post.objects.filter(
                    pk=post.pk, dislikes_count__gt=0
                ).update(
                    dislikes_count=F('dislikes_count') - 1
                )

            reaction.delete()
            post.refresh_from_db(fields=['likes_count', 'dislikes_count'])

        serializer = self.get_serializer(post)
        return Response({
            'message': 'Reaction removed',
            'post': serializer.data
        }, status=status.HTTP_200_OK)

    # LEGACY: Deprecated - use react() instead
    # Kept for backward compatibility
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """DEPRECATED: Use react endpoint with reaction_type='like'"""
        request.data['reaction_type'] = 'like'
        return self.react(request, pk)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def dislike(self, request, pk=None):
        """DEPRECATED: Use react endpoint with reaction_type='sad'"""
        request.data['reaction_type'] = 'sad'
        return self.react(request, pk)

    @action(detail=False, methods=['post'], url_path='comments/(?P<comment_id>[^/.]+)/react', permission_classes=[IsAuthenticated])
    def react_comment(self, request, comment_id=None):
        """React to a comment with an emoji reaction."""
        from django.db import transaction
        from django.db.models import F
        from content.models import CommentReaction, Comment

        comment = get_object_or_404(Comment, id=comment_id, is_deleted=False)
        user_profile = get_object_or_404(UserProfile, user=request.user)
        reaction_type = request.data.get('reaction_type', 'like')

        # Validate reaction type
        valid_reactions = [r[0] for r in CommentReaction.REACTION_TYPES]
        if reaction_type not in valid_reactions:
            return Response(
                {'error': 'Invalid reaction type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Get existing reaction if any
            existing_reaction = CommentReaction.objects.filter(
                user=user_profile,
                comment=comment,
                is_deleted=False
            ).first()

            # Track old sentiment for counter adjustment
            old_sentiment = None
            if existing_reaction:
                if existing_reaction.reaction_type in CommentReaction.POSITIVE_REACTIONS:
                    old_sentiment = 'positive'
                elif existing_reaction.reaction_type in CommentReaction.NEGATIVE_REACTIONS:
                    old_sentiment = 'negative'

            # Create or update reaction
            reaction, created = CommentReaction.objects.update_or_create(
                user=user_profile,
                comment=comment,
                defaults={'reaction_type': reaction_type, 'is_deleted': False}
            )

            # Determine new sentiment
            new_sentiment = None
            if reaction_type in CommentReaction.POSITIVE_REACTIONS:
                new_sentiment = 'positive'
            elif reaction_type in CommentReaction.NEGATIVE_REACTIONS:
                new_sentiment = 'negative'

            # Update counters if sentiment changed (signals will handle this)
            comment.refresh_from_db(fields=['likes_count', 'dislikes_count'])

        # Get emoji for response
        emoji = dict(CommentReaction.REACTION_TYPES).get(reaction_type, '')

        return Response({
            'message': f'Reacted with {emoji}',
            'reaction_type': reaction_type,
            'emoji': emoji,
            'comment': {
                'id': str(comment.id),
                'likes_count': comment.likes_count,
                'dislikes_count': comment.dislikes_count
            }
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='comments/(?P<comment_id>[^/.]+)/react', permission_classes=[IsAuthenticated])
    def unreact_comment(self, request, comment_id=None):
        """Remove user's reaction from a comment."""
        from django.db import transaction
        from content.models import CommentReaction, Comment

        comment = get_object_or_404(Comment, id=comment_id, is_deleted=False)
        user_profile = get_object_or_404(UserProfile, user=request.user)

        with transaction.atomic():
            reaction = CommentReaction.objects.filter(
                user=user_profile,
                comment=comment,
                is_deleted=False
            ).first()

            if not reaction:
                return Response(
                    {'message': 'No reaction to remove'},
                    status=status.HTTP_404_NOT_FOUND
                )

            reaction.delete()
            comment.refresh_from_db(fields=['likes_count', 'dislikes_count'])

        return Response({
            'message': 'Reaction removed',
            'comment': {
                'id': str(comment.id),
                'likes_count': comment.likes_count,
                'dislikes_count': comment.dislikes_count
            }
        }, status=status.HTTP_200_OK)

    # LEGACY: Deprecated comment endpoints - use react_comment instead
    @action(detail=False, methods=['post'], url_path='comments/(?P<comment_id>[^/.]+)/like', permission_classes=[IsAuthenticated])
    def like_comment(self, request, comment_id=None):
        """DEPRECATED: Use react_comment with reaction_type='like'"""
        request.data['reaction_type'] = 'like'
        return self.react_comment(request, comment_id)

    @action(detail=False, methods=['post'], url_path='comments/(?P<comment_id>[^/.]+)/dislike', permission_classes=[IsAuthenticated])
    def dislike_comment(self, request, comment_id=None):
        """DEPRECATED: Use react_comment with reaction_type='sad'"""
        request.data['reaction_type'] = 'sad'
        return self.react_comment(request, comment_id)

    def _can_user_view_post(self, post, user_profile):
        """Check if user can view a post based on visibility rules."""
        # Public posts can be viewed by anyone
        if post.visibility == 'public':
            return True

        # Own posts can always be viewed
        if post.author == user_profile:
            return True

        # Followers-only posts: user must be following the post author
        if post.visibility == 'followers':
            from content.models import Follow
            return Follow.objects.filter(
                follower=user_profile,
                followed=post.author,
                is_deleted=False
            ).exists()

        # Community posts: user must be a member of the community
        if post.visibility == 'community' and post.community:
            # Check if user is a member of the community
            # This would depend on your Community model implementation
            return hasattr(post.community, 'members') and post.community.members.filter(
                id=user_profile.id
            ).exists()

        # Private posts can only be viewed by the author
        return False

    def _can_user_repost_post(self, post, user_profile):
        """Check if user can repost a post based on visibility rules.

        Repost permissions are more restrictive than view permissions:
        - Can repost: public posts
        - Can repost: followers-only posts (if user follows the author)
        - Can repost: posts from public communities only
        - Cannot repost: private posts
        - Cannot repost: posts from private/restricted communities
        - Cannot repost: custom visibility posts (even if user can view them)
        """
        # Own posts can always be reposted (but not own reposts - checked elsewhere)
        if post.author == user_profile:
            return True

        # Only public and followers visibility allow reposting
        if post.visibility == 'public':
            return True

        if post.visibility == 'followers':
            from content.models import Follow
            return Follow.objects.filter(
                follower=user_profile,
                followed=post.author,
                is_deleted=False
            ).exists()

        # Community posts can be reposted if the community is public
        if post.visibility == 'community' and post.community:
            # Check if the community itself is public
            return post.community.community_type == 'public'

        # All other visibility types (private, custom) cannot be reposted
        return False

    def _update_repost_count(self, post):
        """Recalculate and update the repost count from actual database records."""
        actual_repost_count = Post.objects.filter(
            parent_post=post,
            post_type='repost',
            is_deleted=False
        ).count()

        if post.repost_count != actual_repost_count:
            post.repost_count = actual_repost_count
            post.save(update_fields=['repost_count'])

        return actual_repost_count

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def repost(self, request, pk=None):
        """Repost or unrepost a post by creating a new Post with parent_post reference.

        User can repost any post that is visible to them:
        - Public posts
        - Posts from users they follow (if visibility is 'followers')
        - Community posts (if they're a member)
        """
        from django.db import transaction

        original_post = self.get_object()
        user_profile = get_object_or_404(UserProfile, user=request.user)
        repost_content = request.data.get('comment', '').strip()

        # Check if user can repost this post (more restrictive than view permissions)
        if not self._can_user_repost_post(original_post, user_profile):
            return Response({
                'error': 'You cannot repost this post. Only public and followers-only posts can be reposted.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Prevent reposting your own reposts (but allow reposting your own original posts)
        if original_post.is_repost and original_post.author == user_profile:
            return Response({
                'error': 'You cannot repost your own repost.'
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Check if user already has a repost of this post
            existing_repost = Post.objects.filter(
                author=user_profile,
                parent_post=original_post,
                post_type='repost',
                is_deleted=False
            ).first()

            if existing_repost:
                # Toggle off - soft delete the repost
                existing_repost.is_deleted = True
                existing_repost.save()

                # Recalculate and update original post's repost counter
                self._update_repost_count(original_post)

                action = 'unreposted'
                repost_data = None

            else:
                # Create new repost Post
                repost_post = Post.objects.create(
                    author=user_profile,
                    parent_post=original_post,
                    content=repost_content,
                    post_type='repost',
                    visibility='public'  # Reposts are always public
                )

                # Recalculate and update original post's repost counter
                self._update_repost_count(original_post)

                action = 'reposted'
                repost_data = {
                    'id': str(repost_post.id),
                    'content': repost_post.content,
                    'created_at': repost_post.created_at.isoformat()
                }

                action = 'reposted'
                repost_data = {
                    'id': str(repost_post.id),
                    'content': repost_post.content,
                    'created_at': repost_post.created_at.isoformat()
                }

        # Return updated original post data
        serializer = self.get_serializer(original_post)
        response_data = {
            'message': f'Post {action}',
            'action': action,
            'post': serializer.data
        }

        if repost_data:
            response_data['repost'] = repost_data

        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def by_hashtag(self, request):
        """
        Get paginated list of posts that mention a specific hashtag.

        Query parameters:
        - hashtag: The hashtag name (without #)
        - page: Page number (default: 1)
        - page_size: Number of posts per page (default: 20)
        """
        hashtag_name = request.query_params.get('hashtag')
        if not hashtag_name:
            return Response(
                {'error': 'hashtag parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Remove # if provided
        hashtag_name = hashtag_name.lstrip('#').lower()

        try:
            # Check if hashtag exists
            hashtag = get_object_or_404(
                Hashtag.objects.filter(is_deleted=False),
                name=hashtag_name
            )

            # Get posts that have this hashtag and are not deleted
            posts_queryset = self.get_queryset().filter(
                content_hashtags__hashtag=hashtag,
                content_hashtags__is_deleted=False
            ).distinct().order_by('-created_at')

            # Apply pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))

            from django.core.paginator import Paginator
            paginator = Paginator(posts_queryset, page_size)
            page_obj = paginator.get_page(page)

            # Serialize the posts
            serializer = UnifiedPostSerializer(
                page_obj.object_list,
                many=True,
                context={'request': request}
            )

            return Response({
                'hashtag': {
                    'name': hashtag.name,
                    'posts_count': hashtag.posts_count,
                    'is_trending': hashtag.is_trending
                },
                'results': serializer.data,
                'count': paginator.count,
                'page': page,
                'page_size': page_size,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'total_pages': paginator.num_pages
            })

        except Hashtag.DoesNotExist:
            return Response(
                {'error': f'Hashtag "{hashtag_name}" not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def hashtags(self, request):
        """
        Get list of hashtags with optional filtering.

        Query parameters:
        - trending: 'true' to get only trending hashtags
        - search: Search hashtags by name
        - limit: Number of hashtags to return (default: 50, max: 100)
        """
        from content.models import Hashtag

        queryset = Hashtag.objects.filter(is_deleted=False)

        # Filter by trending
        if request.query_params.get('trending', '').lower() == 'true':
            queryset = queryset.filter(is_trending=True)

        # Search by name
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search.lstrip('#'))

        # Apply limit
        limit = int(request.query_params.get('limit', 50))
        limit = min(limit, 100)  # Max 100 hashtags

        # Order by posts count or trending status
        if request.query_params.get('trending', '').lower() == 'true':
            queryset = queryset.order_by('-is_trending', '-posts_count')
        else:
            queryset = queryset.order_by('-posts_count', 'name')

        hashtags = queryset[:limit]

        hashtag_data = [
            {
                'name': hashtag.name,
                'posts_count': hashtag.posts_count,
                'is_trending': hashtag.is_trending,
                'created_at': hashtag.created_at.isoformat()
            }
            for hashtag in hashtags
        ]

        return Response({
            'results': hashtag_data,
            'count': len(hashtag_data),
            'total_available': queryset.count()
        })

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def trending_hashtags(self, request):
        """
        Get trending hashtags.

        Query parameters:
        - limit: Number of hashtags to return (default: 20, max: 50)
        """
        from content.models import Hashtag

        limit = int(request.query_params.get('limit', 20))
        limit = min(limit, 50)  # Max 50 trending hashtags

        trending_hashtags = Hashtag.objects.filter(
            is_deleted=False,
            is_trending=True
        ).order_by('-posts_count')[:limit]

        hashtag_data = [
            {
                'name': hashtag.name,
                'posts_count': hashtag.posts_count,
                'is_trending': hashtag.is_trending,
                'created_at': hashtag.created_at.isoformat()
            }
            for hashtag in trending_hashtags
        ]

        return Response({
            'results': hashtag_data,
            'count': len(hashtag_data)
        })

# Example usage and API documentation
class UnifiedAttachmentAPIExamples:
    """
    Examples of how to use the unified attachment API.
    """

    # Example 1: Create a post with multiple attachments
    create_post_with_attachments = {
        "content": "Check out these awesome photos!",
        "post_type": "image",
        "attachments": [
            {
                "media_type": "image",
                "file": "<file_upload>",
                "order": 1
            },
            {
                "media_type": "image",
                "file": "<file_upload>",
                "order": 2
            },
            {
                "media_type": "video",
                "file": "<file_upload>",
                "order": 3
            }
        ]
    }

    # Example 2: Create a post with multiple polls
    create_post_with_polls = {
        "content": "Help me decide!",
        "post_type": "poll",
        "polls": [
            {
                "question": "Which color do you prefer?",
                "multiple_choice": False,
                "options": [
                    {"text": "Red", "order": 1},
                    {"text": "Blue", "order": 2},
                    {"text": "Green", "order": 3}
                ],
                "order": 1
            },
            {
                "question": "When should we meet?",
                "multiple_choice": True,
                "options": [
                    {"text": "Monday", "order": 1},
                    {"text": "Tuesday", "order": 2},
                    {"text": "Wednesday", "order": 3}
                ],
                "order": 2
            }
        ]
    }

    # Example 3: Response format for unified post
    unified_post_response = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "content": "My awesome post!",
        "author_username": "john_doe",
        "attachment_count": 3,
        "has_attachments": True,
        "attachments": [
            {
                "id": "456e7890-e89b-12d3-a456-426614174001",
                "media_type": "image",
                "file_url": "https://example.com/media/image1.jpg",
                "thumbnail_url": "https://example.com/media/thumb1.jpg",
                "order": 1,
                "file_size": 1024000
            }
        ],
        "attachments_by_type": {
            "image": ["..."],
            "video": ["..."]
        },
        "polls_count": 1,
        "has_polls": True,
        "polls": [
            {
                "id": "789e0123-e89b-12d3-a456-426614174002",
                "question": "What do you think?",
                "options": [
                    {
                        "id": "012e3456-e89b-12d3-a456-426614174003",
                        "text": "Great!",
                        "votes_count": 5,
                        "vote_percentage": 50.0
                    }
                ],
                "user_has_voted": False,
                "is_expired": False
            }
        ],
        "likes_count": 10,
        "media_migrated_to_postmedia": True
    }
