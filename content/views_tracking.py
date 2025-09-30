"""
API views for post view tracking system.
"""
import json
from django.db import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from content.models import Post, PostSee
from analytics.tasks import track_content_analytics
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_post_view(request):
    """
    Track a post view with detailed analytics.

    Expected payload:
    {
        "post_id": "uuid",
        "source": "feed|profile|community|search|notification|...",
        "device_type": "desktop|mobile|tablet",
        "session_id": "string",
        "view_context": {
            "scroll_percentage": 0-100,
            "view_duration": seconds,
            "viewport_height": pixels,
            "post_height": pixels
        }
    }
    """
    try:
        data = request.data
        post_id = data.get('post_id')

        if not post_id:
            return Response(
                {'error': 'post_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the post
        try:
            post = Post.objects.get(id=post_id, is_deleted=False)
        except Post.DoesNotExist:
            return Response(
                {'error': 'Post not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get user profile
        user_profile = request.user.profile

        # Extract tracking data
        source = data.get('source', 'feed')
        device_type = data.get('device_type', 'desktop')
        session_id = data.get('session_id', '')
        view_context = data.get('view_context', {})

        # Get client info
        ip_address = _get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Record the post view
        post_see, created = PostSee.record_post_view(
            user=user_profile,
            post=post,
            source=source,
            device_type=device_type,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Update view context if provided
        if view_context:
            scroll_percentage = view_context.get('scroll_percentage', 0)
            view_duration = view_context.get('view_duration', 0)

            if scroll_percentage > 0:
                post_see.update_scroll_percentage(scroll_percentage)

            if view_duration > 0:
                post_see.update_view_duration(view_duration)

        # Track analytics asynchronously
        analytics_data = {
            'content_type': 'post',
            'content_id': str(post.id),
            'author_id': str(post.author.id),
            'action': 'view',
            'user_id': str(user_profile.id),
            'read_time': view_context.get('view_duration', 0),
            'ip_address': ip_address,
            'device_type': device_type,
            'source': source,
        }

        # Queue analytics task
        track_content_analytics.delay(analytics_data)

        # Update post views count if this is a new view
        if created:
            Post.objects.filter(id=post.id).update(
                views_count=models.F('views_count') + 1
            )

        return Response({
            'success': True,
            'view_id': str(post_see.id),
            'is_new_view': created,
            'quality_score': post_see.engagement_quality,
        })

    except Exception as e:
        logger.error(f"Error tracking post view: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_post_interaction(request):
    """
    Track post interactions (engagement events).

    Expected payload:
    {
        "view_id": "uuid",  # PostSee ID
        "interaction_type": "link_click|media_view|scroll|engagement",
        "interaction_data": {
            "link_url": "string",  # for link_click
            "media_id": "uuid",    # for media_view
            "media_type": "image|video|audio",  # for media_view
            "scroll_percentage": 0-100,  # for scroll
            "duration": seconds    # for media_view
        }
    }
    """
    try:
        data = request.data
        view_id = data.get('view_id')
        interaction_type = data.get('interaction_type')
        interaction_data = data.get('interaction_data', {})

        if not view_id or not interaction_type:
            return Response(
                {'error': 'view_id and interaction_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the PostSee record
        try:
            post_see = PostSee.objects.get(
                id=view_id,
                user=request.user.profile,
                is_deleted=False
            )
        except PostSee.DoesNotExist:
            return Response(
                {'error': 'View record not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Handle different interaction types
        if interaction_type == 'link_click':
            link_url = interaction_data.get('link_url')
            if link_url:
                post_see.add_clicked_link(link_url)

        elif interaction_type == 'media_view':
            media_id = interaction_data.get('media_id')
            media_type = interaction_data.get('media_type', 'unknown')
            duration = interaction_data.get('duration', 0)

            if media_id:
                post_see.add_media_view(media_id, media_type, duration)

        elif interaction_type == 'scroll':
            scroll_percentage = interaction_data.get('scroll_percentage', 0)
            if scroll_percentage > 0:
                post_see.update_scroll_percentage(scroll_percentage)

        elif interaction_type == 'engagement':
            post_see.mark_engaged('generic')

        return Response({
            'success': True,
            'quality_score': post_see.engagement_quality,
            'is_engaged': post_see.is_engaged,
        })

    except Exception as e:
        logger.error(f"Error tracking post interaction: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_analytics(request, post_id):
    """
    Get analytics data for a specific post.
    Only accessible by post author or admins.
    """
    try:
        post = get_object_or_404(Post, id=post_id, is_deleted=False)

        # Check permissions
        if post.author != request.user.profile and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get analytics data
        analytics = PostSee.get_post_view_analytics(post)

        # Add post info
        analytics.update({
            'post_id': str(post.id),
            'post_created': post.created_at.isoformat(),
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
            'shares_count': post.shares_count,
        })

        return Response(analytics)

    except Exception as e:
        logger.error(f"Error getting post analytics: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_track_views(request):
    """
    Track multiple post views in a single request.
    Useful for feed scrolling where multiple posts come into view.

    Expected payload:
    {
        "views": [
            {
                "post_id": "uuid",
                "view_duration": seconds,
                "scroll_percentage": 0-100,
                "source": "feed"
            },
            ...
        ],
        "session_id": "string",
        "device_type": "desktop|mobile|tablet"
    }
    """
    try:
        data = request.data
        views_data = data.get('views', [])
        session_id = data.get('session_id', '')
        device_type = data.get('device_type', 'desktop')

        if not views_data:
            return Response(
                {'error': 'No views data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_profile = request.user.profile
        ip_address = _get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        tracked_views = []
        errors = []

        for view_data in views_data:
            try:
                post_id = view_data.get('post_id')
                if not post_id:
                    continue

                post = Post.objects.get(id=post_id, is_deleted=False)

                post_see, created = PostSee.record_post_view(
                    user=user_profile,
                    post=post,
                    source=view_data.get('source', 'feed'),
                    device_type=device_type,
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                # Update context data
                view_duration = view_data.get('view_duration', 0)
                scroll_percentage = view_data.get('scroll_percentage', 0)

                if view_duration > 0:
                    post_see.update_view_duration(view_duration)

                if scroll_percentage > 0:
                    post_see.update_scroll_percentage(scroll_percentage)

                # Track analytics
                analytics_data = {
                    'content_type': 'post',
                    'content_id': str(post.id),
                    'author_id': str(post.author.id),
                    'action': 'view',
                    'user_id': str(user_profile.id),
                    'read_time': view_duration,
                    'ip_address': ip_address,
                    'device_type': device_type,
                    'source': view_data.get('source', 'feed'),
                }
                track_content_analytics.delay(analytics_data)

                tracked_views.append({
                    'post_id': str(post.id),
                    'view_id': str(post_see.id),
                    'is_new_view': created,
                })

            except Post.DoesNotExist:
                errors.append(f"Post {post_id} not found")
            except Exception as e:
                errors.append(f"Error tracking {post_id}: {str(e)}")

        return Response({
            'success': True,
            'tracked_views': tracked_views,
            'errors': errors,
        })

    except Exception as e:
        logger.error(f"Error in batch track views: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Legacy view for non-DRF compatibility
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class LegacyTrackPostView(View):
    """Legacy view for tracking post views without DRF."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            post_id = data.get('post_id')

            if not post_id:
                return JsonResponse({'error': 'post_id required'}, status=400)

            post = get_object_or_404(Post, id=post_id, is_deleted=False)
            user_profile = request.user.profile

            post_see, created = PostSee.record_post_view(
                user=user_profile,
                post=post,
                source=data.get('source', 'feed'),
                device_type=data.get('device_type', 'desktop'),
                session_id=data.get('session_id', ''),
                ip_address=_get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )

            return JsonResponse({
                'success': True,
                'view_id': str(post_see.id),
                'is_new_view': created,
            })

        except Exception as e:
            logger.error(f"Error in legacy track view: {e}")
            return JsonResponse({'error': 'Server error'}, status=500)
