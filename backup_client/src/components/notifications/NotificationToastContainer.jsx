/**
 * NotificationToastContainer - Container for displaying notification toasts
 *
 * Manages the display and positioning of toast notifications
 */

import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import NotificationToast from './NotificationToast';
import { useNotifications } from '../../context/NotificationContext';

const NotificationToastContainer = () => {
  const { notifications, settings, actions } = useNotifications();
  const [toasts, setToasts] = useState([]);

  // Filter notifications for toast display
  useEffect(() => {
    if (!settings.showToasts) return;

    // Get recent unread notifications that should be shown as toasts
    const recentNotifications = notifications
      .filter(notification => {
        // Show unread notifications from the last 30 seconds
        const notificationTime = new Date(notification.timestamp);
        const thirtySecondsAgo = new Date(Date.now() - 30 * 1000);
        return !notification.read && notificationTime > thirtySecondsAgo;
      })
      .slice(0, settings.maxToasts)
      .reverse(); // Show oldest first

    setToasts(recentNotifications);
  }, [notifications, settings.showToasts, settings.maxToasts]);

  const handleCloseToast = (notificationId) => {
    setToasts(prev => prev.filter(toast => toast.id !== notificationId));
  };

  const handleReadToast = (notificationId) => {
    actions.markAsRead(notificationId);
  };

  const handleToastClick = (notification) => {
    // Mark as read
    if (!notification.read) {
      actions.markAsRead(notification.id);
    }

    // Handle navigation based on notification type
    const notificationType = notification.notification_type || notification.type;

    switch (notificationType) {
      case 'comment':
      case 'like':
        if (notification.target_url) {
          window.location.href = notification.target_url;
        }
        break;

      case 'follow':
        if (notification.sender_username) {
          window.location.href = `/profile/${notification.sender_username}`;
        }
        break;

      case 'mention':
        if (notification.target_url) {
          window.location.href = notification.target_url;
        }
        break;

      case 'message':
      case 'new_message':
        window.location.href = '/messages';
        break;

      case 'equipment_shared':
      case 'equipment_request':
      case 'equipment_approved':
        if (notification.target_url) {
          window.location.href = notification.target_url;
        } else {
          window.location.href = '/equipment';
        }
        break;

      case 'badge':
      case 'achievement':
        window.location.href = '/profile/badges';
        break;

      case 'community_role_change':
        // For role changes, show notification detail page
        window.location.href = `/notifications/${notification.id}`;
        break;

      case 'system':
        window.location.href = '/notifications';
        break;

      default:
        // For unknown types, go to notifications page
        window.location.href = '/notifications';
    }
  };

  if (!settings.showToasts || toasts.length === 0) {
    return null;
  }

  const toastContainer = (
    <div
      className="fixed top-4 right-4 z-50 pointer-events-none max-w-[400px] sm:top-4 sm:right-4 sm:left-auto sm:max-w-[400px] max-sm:top-4 max-sm:right-4 max-sm:left-4 max-sm:max-w-none"
    >
      <div className="space-y-3 pointer-events-auto">
        {toasts.map((notification) => (
          <NotificationToast
            key={notification.id}
            notification={notification}
            onClose={handleCloseToast}
            onRead={handleReadToast}
            onClick={handleToastClick}
            autoClose={true}
            duration={settings.toastDuration}
          />
        ))}
      </div>
    </div>
  );

  // Render toasts in a portal to avoid z-index issues
  return createPortal(
    toastContainer,
    document.body
  );
};

export default NotificationToastContainer;
