/**
 * NotificationToast - Individual toast notification component
 *
 * Displays individual notification toasts with animations and actions
 */

import React, { useState, useEffect } from 'react';
import {
  FaBell,
  FaHeart,
  FaComment,
  FaUser,
  FaAt,
  FaShare,
  FaTimes,
  FaExclamationTriangle,
  FaTrophy,
  FaCog,
  FaTools,
  FaShieldAlt
} from 'react-icons/fa';

// Icon mapping for different notification types
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

// Color mapping for different notification types
const NotificationColors = {
  like: 'bg-red-500',
  comment: 'bg-blue-500',
  follow: 'bg-green-500',
  mention: 'bg-yellow-500',
  message: 'bg-blue-500',
  new_message: 'bg-blue-600',
  share: 'bg-purple-500',
  report: 'bg-red-600',
  repost: 'bg-purple-400',
  system: 'bg-gray-500',
  badge: 'bg-yellow-400',
  achievement: 'bg-green-400',
  warranty: 'bg-orange-500',
  maintenance: 'bg-indigo-500',
  equipment_shared: 'bg-teal-500',
  equipment_request: 'bg-cyan-500',
  equipment_approved: 'bg-green-600',
  welcome: 'bg-blue-400',
  security_alert: 'bg-red-700',
  digest: 'bg-gray-600',
  // Community-specific notifications
  community_invite: 'bg-green-500',
  community_join: 'bg-blue-500',
  community_post: 'bg-purple-500',
  community_role_change: 'bg-indigo-600',
  geo_restriction: 'bg-orange-600',
  default: 'bg-gray-500',
};

// Priority colors
const PriorityColors = {
  1: 'border-red-500 shadow-red-200', // High priority
  2: 'border-orange-500 shadow-orange-200', // Elevated
  3: 'border-blue-500 shadow-blue-200', // Normal
  4: 'border-gray-400 shadow-gray-200', // Low
  5: 'border-gray-300 shadow-gray-100', // Very Low
};

const NotificationToast = ({
  notification,
  onClose,
  onRead,
  onClick,
  autoClose = true,
  duration = 5000
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);

  const notificationType = notification.notification_type || notification.type;
  const IconComponent = NotificationIcons[notificationType] || NotificationIcons.default;
  const iconColor = NotificationColors[notificationType] || NotificationColors.default;
  const priorityStyle = PriorityColors[notification.priority] || PriorityColors[3];

  // Animation effects
  useEffect(() => {
    // Animate in
    setTimeout(() => setIsVisible(true), 50);

    // Auto close
    if (autoClose && duration > 0) {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [autoClose, duration]);

  const handleClose = () => {
    setIsRemoving(true);
    setTimeout(() => {
      onClose(notification.id);
    }, 300);
  };

  const handleClick = () => {
    if (!notification.read && onRead) {
      onRead(notification.id);
    }
    if (onClick) {
      onClick(notification);
    }
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now - time) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  return (
    <div
      className={`
        transform transition-all duration-300 ease-in-out mb-3
        ${isVisible && !isRemoving ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
        ${isRemoving ? 'scale-95' : 'scale-100'}
      `}
    >
      <div
        className={`
          bg-white rounded-lg shadow-lg border-l-4 ${priorityStyle}
          max-w-sm p-4 cursor-pointer hover:shadow-xl transition-shadow
          ${!notification.read ? 'ring-2 ring-blue-200 ring-opacity-50' : ''}
        `}
        onClick={handleClick}
      >
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className={`flex-shrink-0 p-2 rounded-full ${iconColor}`}>
            <IconComponent className="h-4 w-4 text-white" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <p className={`text-sm font-medium text-gray-900 ${!notification.read ? 'font-semibold' : ''}`}>
                  {notification.title}
                </p>
                <p className="text-sm text-gray-600 mt-1 break-words">
                  {notification.message}
                </p>

                {/* Metadata */}
                <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                  <span>{formatTimeAgo(notification.timestamp)}</span>
                  {notification.sender_name && (
                    <>
                      <span>•</span>
                      <span>from {notification.sender_name}</span>
                    </>
                  )}
                  {notification.priority <= 2 && (
                    <>
                      <span>•</span>
                      <span className="text-red-500 font-medium">
                        {notification.priority === 1 ? 'High Priority' : 'Elevated Priority'}
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Close button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleClose();
                }}
                className="flex-shrink-0 p-1 rounded-full hover:bg-gray-100 transition-colors"
              >
                <FaTimes className="h-3 w-3 text-gray-400" />
              </button>
            </div>

            {/* Action buttons for certain notification types */}
            {(notificationType === 'equipment_request' || notificationType === 'follow') && (
              <div className="flex gap-2 mt-3">
                <button className="px-3 py-1 text-xs bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors">
                  View
                </button>
                {notificationType === 'equipment_request' && (
                  <button className="px-3 py-1 text-xs bg-green-600 text-white rounded-full hover:bg-green-700 transition-colors">
                    Approve
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Progress bar for auto-close */}
        {autoClose && duration > 0 && (
          <div className="mt-3 h-1 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all ease-linear"
              style={{
                width: '100%',
                animation: `shrink ${duration}ms linear forwards`
              }}
            />
          </div>
        )}
      </div>

      {/* Custom CSS for progress bar animation */}
      <style>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );
};

export default NotificationToast;
