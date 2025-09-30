"""
Test views for creating notifications to test the real-time system.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from notifications.utils import NotificationService
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_test_notification(request):
    """
    Create a test notification for the authenticated user.
    This endpoint is only for testing the real-time notification system.
    """
    try:
        user_profile = request.user.profile

        # Get notification parameters from request
        data = request.data
        notification_type = data.get('type', 'system')
        title = data.get('title', 'Test Notification')
        message = data.get(
            'message',
            'This is a test notification to verify the real-time system.'
        )
        priority = int(data.get('priority', 3))

        # Create the notification using NotificationService
        notification = NotificationService.create_notification(
            recipient=user_profile,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            extra_data={'test': True, 'created_via': 'test_endpoint'}
        )

        logger.info(
            f"Test notification created: {notification.id} "
            f"for user {user_profile.user.username}"
        )

        return Response({
            'success': True,
            'message': 'Test notification created successfully',
            'notification': {
                'id': str(notification.id),
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'priority': notification.priority,
                'created_at': notification.created_at.isoformat()
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating test notification: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_bulk_test_notifications(request):
    """
    Create multiple test notifications for testing the system.
    """
    try:
        user_profile = request.user.profile
        count = int(request.data.get('count', 3))

        if count > 10:
            count = 10  # Limit to prevent spam

        notifications = []
        notification_types = [
            'system', 'social', 'message', 'community'
        ]

        for i in range(count):
            notification_type = notification_types[i % len(notification_types)]

            notification = NotificationService.create_notification(
                recipient=user_profile,
                title=f'Test Notification #{i+1}',
                message=f'Test notification {i+1} of type {notification_type}.',
                notification_type=notification_type,
                priority=((i % 3) + 1),  # Priority 1-3
                extra_data={'test': True, 'batch_number': i+1}
            )

            notifications.append({
                'id': str(notification.id),
                'title': notification.title,
                'type': notification.notification_type,
                'priority': notification.priority
            })

        logger.info(
            f"Created {count} test notifications "
            f"for user {user_profile.user.username}"
        )

        return Response({
            'success': True,
            'message': f'Created {count} test notifications',
            'notifications': notifications
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating bulk test notifications: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_websocket_connection(request):
    """
    Test endpoint to check if WebSocket system is working.
    """
    try:
        user_profile = request.user.profile

        # Create a simple test notification
        notification = NotificationService.create_notification(
            recipient=user_profile,
            title='WebSocket Connection Test',
            message='If you received this notification in real-time, '
                   'your WebSocket connection is working!',
            notification_type='system',
            priority=2,
            extra_data={'test': True, 'connection_test': True}
        )

        return Response({
            'success': True,
            'message': 'WebSocket test notification sent',
            'notification_id': str(notification.id),
            'timestamp': notification.created_at.isoformat()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in WebSocket test: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
