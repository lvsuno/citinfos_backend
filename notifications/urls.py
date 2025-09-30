from django.urls import path
from notifications import views, test_views

app_name = 'notifications'

urlpatterns = [
    # Main notification endpoints
    path('api/notifications/',
         views.NotificationListView.as_view(),
         name='notification-list'),

    path('api/notifications/summary/',
         views.NotificationSummaryView.as_view(),
         name='notification-summary'),

    path('api/notifications/inline/',
         views.notification_inline_summary,
         name='notification-inline'),

    path('api/notifications/<uuid:id>/',
         views.NotificationDetailView.as_view(),
         name='notification-detail'),

    # Actions
    path('api/notifications/mark-read/',
         views.mark_notifications_read,
         name='mark-notifications-read'),

    path('api/notifications/<uuid:notification_id>/delete/',
         views.delete_notification,
         name='delete-notification'),

    # Test endpoints for real-time notifications
    path('api/notifications/test/create/',
         test_views.create_test_notification,
         name='create-test-notification'),

    path('api/notifications/test/bulk/',
         test_views.create_bulk_test_notifications,
         name='create-bulk-test-notifications'),

    path('api/notifications/test/websocket/',
         test_views.test_websocket_connection,
         name='test-websocket-connection'),
]
