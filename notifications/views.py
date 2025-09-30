"""
Notification API views.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404
from notifications.models import Notification
from notifications.serializers import (
    NotificationSerializer,
    NotificationWithContentSerializer,
    NotificationSummarySerializer,
    MarkAsReadSerializer,
    InlineNotificationSerializer
)
from notifications.utils import NotificationService
import logging

logger = logging.getLogger(__name__)


class NotificationListView(generics.ListAPIView):
    """List user's notifications with filtering and pagination."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_profile = self.request.user.profile
        queryset = Notification.objects.filter(
            recipient=user_profile,
            is_deleted=False
        ).select_related('sender', 'content_type').order_by('-created_at')

        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')

        # Filter by notification type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset


class NotificationSummaryView(generics.RetrieveAPIView):
    """Get notification summary (counts, latest notification, etc.)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_profile = request.user.profile

        # Get counts
        unread_count = NotificationService.get_unread_count(user_profile)
        total_count = Notification.objects.filter(
            recipient=user_profile,
            is_deleted=False
        ).count()

        # Check for high priority notifications
        has_high_priority = Notification.objects.filter(
            recipient=user_profile,
            is_read=False,
            priority__lte=2,
            is_deleted=False
        ).exists()

        # Get latest notification
        latest_notification = Notification.objects.filter(
            recipient=user_profile,
            is_deleted=False
        ).order_by('-created_at').first()

        data = {
            'unread_count': unread_count,
            'total_count': total_count,
            'has_high_priority': has_high_priority,
            'latest_notification': (
                NotificationSerializer(latest_notification).data
                if latest_notification else None
            )
        }

        return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notifications_read(request):
    """Mark notifications as read."""

    serializer = MarkAsReadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user_profile = request.user.profile
    notification_ids = serializer.validated_data.get('notification_ids', [])

    if notification_ids:
        # Mark specific notifications as read
        updated_count = NotificationService.mark_as_read(
            notification_ids, user_profile
        )
    else:
        # Mark all notifications as read
        updated_count = Notification.objects.filter(
            recipient=user_profile,
            is_read=False,
            is_deleted=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

    return Response({
        'message': f'{updated_count} notifications marked as read',
        'updated_count': updated_count
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    """Delete a specific notification."""

    user_profile = request.user.profile
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=user_profile,
        is_deleted=False
    )

    # Soft delete
    notification.is_deleted = True
    notification.deleted_at = timezone.now()
    notification.save(update_fields=['is_deleted', 'deleted_at'])

    return Response({
        'message': 'Notification deleted successfully'
    }, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_inline_summary(request):
    """Get inline notification summary for embedding in other API responses."""

    user_profile = request.user.profile
    serializer = InlineNotificationSerializer()
    data = serializer.to_representation(user_profile)

    return Response(data, status=status.HTTP_200_OK)


class NotificationDetailView(generics.RetrieveAPIView):
    """Get details of a specific notification with full content object."""

    serializer_class = NotificationWithContentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user.profile,
            is_deleted=False
        ).select_related(
            'sender', 'content_type'
        ).prefetch_related('content_object')

    def retrieve(self, request, *args, **kwargs):
        # Automatically mark as read when retrieved
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])

        return super().retrieve(request, *args, **kwargs)



# Utility function to add notification data to any API response
def add_notification_summary(response_data, user_profile):
    """
    Add notification summary to any API response.

    Usage:
        data = {'your': 'existing_data'}
        add_notification_summary(data, request.user.profile)
        return Response(data)
    """
    if user_profile:
        serializer = InlineNotificationSerializer()
        response_data['notifications'] = serializer.to_representation(user_profile)
    else:
        response_data['notifications'] = {
            'has_notifications': False,
            'unread_count': 0,
            'urgent_alerts': []
        }

    return response_data


# Decorator to automatically add notifications to API responses
def with_notifications(view_func):
    """
    Decorator to automatically add notification summary to API responses.

    Usage:
        @with_notifications
        def my_api_view(request):
            return Response({'data': 'value'})
    """
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)

        if (hasattr(request, 'user') and
            hasattr(request.user, 'profile') and
            isinstance(response.data, dict)):
            add_notification_summary(response.data, request.user.profile)

        return response

    return wrapper
