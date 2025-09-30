/**
 * NotificationDropdown - Dropdown panel showing recent notifications
 *
 * Displays a list of recent notifications with actions
 */

import React, { useState, useEffect } from 'react';
import {
  FaBell,
  FaHeart,
  FaComment,
  FaUser,
  FaAt,
  FaShare,
  FaExclamationTriangle,
  FaTrophy,
  FaCog,
  FaTools,
  FaShieldAlt,
  FaCheckCircle,
  FaEye,
  FaTimes,
  FaSpinner
} from 'react-icons/fa';
import { useNotifications } from '../../context/NotificationContext';

// Icon mapping (same as NotificationToast)
const NotificationIcons = {
  like: FaHeart,
  comment: FaComment,
  follow: FaUser,
  mention: FaAt,
  message: FaComment,
  new_message: FaComment,
  share: FaShare,
  report: FaExclamationTriangle,
  repost: FaShare,
  system: FaCog,
  badge: FaTrophy,
  achievement: FaTrophy,
  warranty: FaShieldAlt,
  maintenance: FaTools,
  equipment_shared: FaShare,
  equipment_request: FaUser,
  equipment_approved: FaTrophy,
  welcome: FaUser,
  security_alert: FaShieldAlt,
  digest: FaBell,
  // Community-specific notifications
  community_invite: FaUser,
  community_join: FaUser,
  community_post: FaComment,
  community_role_change: FaShieldAlt,
  geo_restriction: FaExclamationTriangle,
  default: FaBell,
};

// Color mapping
const NotificationColors = {
  like: 'text-red-500',
  comment: 'text-blue-500',
  follow: 'text-green-500',
  mention: 'text-yellow-600',
  message: 'text-blue-500',
  new_message: 'text-blue-600',
  share: 'text-purple-500',
  report: 'text-red-600',
  repost: 'text-purple-400',
  system: 'text-gray-500',
  badge: 'text-yellow-500',
  achievement: 'text-green-500',
  warranty: 'text-orange-500',
  maintenance: 'text-indigo-500',
  equipment_shared: 'text-teal-500',
  equipment_request: 'text-cyan-500',
  equipment_approved: 'text-green-600',
  welcome: 'text-blue-400',
  security_alert: 'text-red-700',
  digest: 'text-gray-600',
  // Community-specific notifications
  community_invite: 'text-green-500',
  community_join: 'text-blue-500',
  community_post: 'text-purple-500',
  community_role_change: 'text-indigo-600',
  geo_restriction: 'text-orange-600',
  default: 'text-gray-500',
};

const NotificationDropdown = ({ onClose }) => {
  const {
    notifications,
    unreadCount,
    isConnected,
    connectionFailed,
    actions
  } = useNotifications();

  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState('all'); // all, unread

  // Load notifications on mount or when connection is established
  useEffect(() => {
    if (isConnected) {
      setIsLoading(true);
      actions.requestHistory(1, 20);
      // Simulate loading time (actual loading is handled by WebSocket)
      setTimeout(() => setIsLoading(false), 1000);
    }
  }, [isConnected]); // Always fetch when connected, regardless of current notifications

  // Also force refresh when dropdown opens
  useEffect(() => {
    if (isConnected) {
      actions.requestHistory(1, 20);
    }
  }, []); // Run once when component mounts

  // Calculate footer visibility
  const shouldShowFooter = (filter === 'all' && notifications.length > 5) || (filter === 'unread' && unreadCount > 5);

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now - time) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h`;
    return `${Math.floor(diffInMinutes / 1440)}d`;
  };

  const filteredNotifications = notifications
    .filter(notification => {
      if (filter === 'unread') return !notification.read;
      return true;
    })
    .slice(0, 5); // Show max 5 in dropdown for better UX

  const handleNotificationClick = (notification) => {
    // Mark as read if unread
    if (!notification.read) {
      actions.markAsRead(notification.id);
    }

    // Close dropdown
    onClose();

    // Navigate based on notification type and available data
    const notificationType = notification.notification_type || notification.type;

    switch (notificationType) {
      case 'comment':
      case 'like':
      case 'share':
      case 'repost':
        // Try target_url first, fallback to generic pages
        if (notification.target_url) {
          window.location.href = notification.target_url;
        } else if (notification.extra_data?.post_id) {
          window.location.href = `/posts/${notification.extra_data.post_id}`;
        } else {
          window.location.href = '/dashboard';
        }
        break;

      case 'follow':
        // Navigate to user profile
        if (notification.sender?.username) {
          window.location.href = `/user/${notification.sender.username}`;
        } else if (notification.sender_username) {
          window.location.href = `/user/${notification.sender_username}`;
        } else if (notification.extra_data?.user_id) {
          window.location.href = `/users/${notification.extra_data.user_id}`;
        } else {
          window.location.href = '/profile';
        }
        break;

      case 'mention':
        // Navigate to the content where user was mentioned
        if (notification.target_url) {
          window.location.href = notification.target_url;
        } else if (notification.extra_data?.post_id) {
          window.location.href = `/posts/${notification.extra_data.post_id}`;
        } else if (notification.extra_data?.comment_id) {
          window.location.href = `/comments/${notification.extra_data.comment_id}`;
        } else {
          window.location.href = '/dashboard';
        }
        break;

      case 'message':
      case 'new_message':
      case 'messaging':
        // Navigate to messages/chat
        if (notification.extra_data?.chat_id) {
          window.location.href = `/chat/${notification.extra_data.chat_id}`;
        } else if (notification.sender?.id) {
          window.location.href = `/chat?user=${notification.sender.id}`;
        } else {
          window.location.href = '/chat';
        }
        break;

      case 'equipment_shared':
      case 'equipment_request':
      case 'equipment_approved':
      case 'equipment':
        // Navigate to equipment pages
        if (notification.target_url) {
          window.location.href = notification.target_url;
        } else if (notification.extra_data?.equipment_id) {
          window.location.href = `/equipment/${notification.extra_data.equipment_id}`;
        } else {
          window.location.href = '/equipment';
        }
        break;

      case 'community':
      case 'community_notification':
      case 'community_invite':
      case 'community_join':
      case 'community_post':
      case 'geo_restriction':
        // Navigate to community (new short URL)
        if (notification.extra_data?.community_slug) {
          window.location.href = `/c/${notification.extra_data.community_slug}`;
        } else if (notification.extra_data?.community_id) {
          window.location.href = `/c/${notification.extra_data.community_id}`;
        } else {
          window.location.href = '/communities';
        }
        break;

      case 'community_role_change':
        // For role changes, show notification detail page to see full context
        window.location.href = `/notifications/${notification.id}`;
        break;

      case 'poll':
      case 'poll_notification':
        // Navigate to poll
        if (notification.extra_data?.poll_id) {
          window.location.href = `/polls/${notification.extra_data.poll_id}`;
        } else {
          window.location.href = '/polls';
        }
        break;

      case 'badge':
      case 'achievement':
        // Navigate to user badges
        window.location.href = '/badges';
        break;

      case 'ai_conversation':
      case 'ai_conversation_notification':
        // Navigate to AI conversations
        if (notification.extra_data?.conversation_id) {
          window.location.href = `/ai-conversations/${notification.extra_data.conversation_id}`;
        } else {
          window.location.href = '/ai-conversations';
        }
        break;

      case 'moderation':
      case 'moderation_notification':
      case 'report':
        // Navigate to profile or dashboard for moderation notices
        window.location.href = '/profile';
        break;

      case 'system':
      case 'security_alert':
      case 'welcome':
        // System notifications - show details or go to notifications page
        window.location.href = `/notifications/${notification.id}`;
        break;

      default:
        // Default: go to full notifications page to see details
        window.location.href = `/notifications/${notification.id}`;
    }
  };

  const handleMarkAsRead = (e, notificationId) => {
    e.stopPropagation();
    actions.markAsRead(notificationId);
  };

  const handleMarkAllRead = () => {
    actions.markAllAsRead();
  };

  return (
    <div className="w-80 bg-white rounded-lg shadow-xl border border-gray-200 max-h-96 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <FaBell className="h-4 w-4" />
            Notifications
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                {unreadCount}
              </span>
            )}
          </h3>

          <div className="flex items-center gap-2">
            {/* Connection status */}
            <div className={`h-2 w-2 rounded-full ${
              isConnected ? 'bg-green-500' : connectionFailed ? 'bg-red-500' : 'bg-yellow-500'
            }`} title={isConnected ? 'Connected' : connectionFailed ? 'Connection failed' : 'Connecting'} />

            {/* Close button */}
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-gray-200 transition-colors"
            >
              <FaTimes className="h-3 w-3 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Filter and actions */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex gap-2">
            <button
              onClick={() => {
                setFilter('all');
              }}
              className={`text-xs px-2 py-1 rounded transition-colors ${
                filter === 'all'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              All
            </button>
            <button
              onClick={() => {
                setFilter('unread');
              }}
              className={`text-xs px-2 py-1 rounded transition-colors ${
                filter === 'unread'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Unread ({unreadCount})
            </button>
          </div>

          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              <FaCheckCircle className="h-3 w-3" />
              Mark all read
            </button>
          )}
        </div>
      </div>

      {/* Notifications list */}
      <div className="max-h-48 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <FaSpinner className="h-6 w-6 text-gray-400 animate-spin" />
            <span className="ml-2 text-sm text-gray-500">Loading notifications...</span>
          </div>
        ) : filteredNotifications.length === 0 ? (
          <div className="text-center py-8">
            <FaBell className="h-8 w-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">
              {filter === 'unread' ? 'No unread notifications' : 'No notifications yet'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredNotifications.map((notification, index) => {
              const notificationType = notification.notification_type || notification.type;
              const IconComponent = NotificationIcons[notificationType] || NotificationIcons.default;
              const iconColor = NotificationColors[notificationType] || NotificationColors.default;

              return (
                <div
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  className={`
                    px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors relative
                    ${!notification.read ? 'bg-blue-50 border-l-2 border-blue-500' : ''}
                  `}
                >
                  <div className="flex items-start gap-3">
                    {/* Icon */}
                    <div className="flex-shrink-0 mt-0.5">
                      <IconComponent className={`h-4 w-4 ${iconColor}`} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${!notification.read ? 'font-medium text-gray-900' : 'text-gray-700'}`}>
                        {notification.title}
                      </p>
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                        {notification.message}
                      </p>

                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-400">
                          {formatTimeAgo(notification.timestamp)}
                        </span>

                        {!notification.read && (
                          <button
                            onClick={(e) => handleMarkAsRead(e, notification.id)}
                            className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                          >
                            <FaEye className="h-3 w-3" />
                            Mark read
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Unread indicator */}
                    {!notification.read && (
                      <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    )}
                  </div>

                  {/* Priority indicator */}
                  {notification.priority <= 2 && (
                    <div className={`absolute left-0 top-0 bottom-0 w-1 ${
                      notification.priority === 1 ? 'bg-red-500' : 'bg-orange-500'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Single footer that changes based on current filter */}
      {shouldShowFooter && (
        <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
          <button
            onClick={() => {
              onClose();
              window.location.href = filter === 'all' ? '/notifications' : '/notifications?filter=unread';
            }}
            className="w-full text-sm text-blue-600 hover:text-blue-800 flex items-center justify-center gap-2 py-2 px-3 rounded-md hover:bg-blue-50 transition-colors"
          >
            <FaEye className="h-4 w-4" />
            {filter === 'all'
              ? `View all notifications (${notifications.length - 5} more)`
              : `View all unread notifications (${unreadCount - 5} more)`
            }
          </button>
        </div>
      )}
    </div>
  );
};

export default NotificationDropdown;
