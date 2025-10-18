import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useNotifications } from '../contexts/NotificationContext';
import { FiBell, FiBellOff, FiCheck, FiCheckCircle, FiX, FiRefreshCw, FiFilter, FiSearch, FiExternalLink } from 'react-icons/fi';

const NotificationsPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const {
    notifications,
    unreadCount,
    isConnected,
    actions
  } = useNotifications();

  const [filter, setFilter] = useState('all'); // all, unread, read
  const [typeFilter, setTypeFilter] = useState('all'); // all, system, social, equipment, etc.
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNotifications, setSelectedNotifications] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [highlightedNotificationId, setHighlightedNotificationId] = useState(null);

  // Check if specific notification ID or filter is requested via URL
  useEffect(() => {
    const notificationId = searchParams.get('id');
    if (notificationId) {
      setHighlightedNotificationId(notificationId);
      // Clear URL parameter after highlighting
      const timer = setTimeout(() => {
        setHighlightedNotificationId(null);
      }, 3000);
      return () => clearTimeout(timer);
    }

    // Check for filter parameter in URL
    const filterParam = searchParams.get('filter');
    if (filterParam && ['all', 'unread', 'read'].includes(filterParam)) {
      setFilter(filterParam);
    }
  }, [searchParams]);

  // Filter and search notifications
  const filteredNotifications = useMemo(() => {
    let filtered = [...notifications];

    // Apply read/unread filter
    if (filter === 'unread') {
      filtered = filtered.filter(n => !n.read);
    } else if (filter === 'read') {
      filtered = filtered.filter(n => n.read);
    }

    // Apply type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(n => n.notification_type === typeFilter || n.type === typeFilter);
    }

    // Apply search filter
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(n =>
        n.title?.toLowerCase().includes(term) ||
        n.message?.toLowerCase().includes(term)
      );
    }

    return filtered;
  }, [notifications, filter, typeFilter, searchTerm]);

  // Get unique notification types for filter dropdown
  const availableTypes = useMemo(() => {
    const types = new Set();
    notifications.forEach(n => {
      if (n.notification_type) types.add(n.notification_type);
      if (n.type) types.add(n.type);
    });
    return Array.from(types).sort();
  }, [notifications]);

  // Handle individual notification click
  const handleNotificationClick = (notification) => {
    // Mark as read if unread
    if (!notification.read) {
      handleMarkAsRead(notification.id);
    }

    // Navigate based on notification type and available data
    const notificationType = notification.notification_type || notification.type;

    switch (notificationType) {
      case 'comment':
      case 'like':
      case 'share':
      case 'repost':
        if (notification.target_url) {
          navigate(notification.target_url);
        } else if (notification.extra_data?.post_id) {
          navigate(`/posts/${notification.extra_data.post_id}`);
        } else {
          navigate('/dashboard');
        }
        break;

      case 'follow':
        if (notification.sender?.username) {
          navigate(`/user/${notification.sender.username}`);
        } else if (notification.sender_username) {
          navigate(`/user/${notification.sender_username}`);
        } else if (notification.extra_data?.user_id) {
          navigate(`/users/${notification.extra_data.user_id}`);
        } else {
          navigate('/profile');
        }
        break;

      case 'mention':
        if (notification.target_url) {
          navigate(notification.target_url);
        } else if (notification.extra_data?.post_id) {
          navigate(`/posts/${notification.extra_data.post_id}`);
        } else if (notification.extra_data?.comment_id) {
          navigate(`/comments/${notification.extra_data.comment_id}`);
        } else {
          navigate('/dashboard');
        }
        break;

      case 'message':
      case 'new_message':
      case 'messaging':
        if (notification.extra_data?.chat_id) {
          navigate(`/chat/${notification.extra_data.chat_id}`);
        } else if (notification.sender?.id) {
          navigate(`/chat?user=${notification.sender.id}`);
        } else {
          navigate('/chat');
        }
        break;

      case 'equipment_shared':
      case 'equipment_request':
      case 'equipment_approved':
      case 'equipment':
        if (notification.target_url) {
          navigate(notification.target_url);
        } else if (notification.extra_data?.equipment_id) {
          navigate(`/equipment/${notification.extra_data.equipment_id}`);
        } else {
          navigate('/equipment');
        }
        break;

      case 'community':
      case 'community_notification':
      case 'community_invite':
      case 'community_join':
      case 'community_post':
      case 'geo_restriction':
        if (notification.extra_data?.community_slug) {
          navigate(`/c/${notification.extra_data.community_slug}`);
        } else if (notification.extra_data?.community_id) {
          navigate(`/c/${notification.extra_data.community_id}`);
        } else {
          navigate('/communities');
        }
        break;

      case 'community_role_change':
        // For role changes, go to notification detail page
        navigate(`/notifications/${notification.id}`);
        break;

      case 'poll':
      case 'poll_notification':
        if (notification.extra_data?.poll_id) {
          navigate(`/polls/${notification.extra_data.poll_id}`);
        } else {
          navigate('/polls');
        }
        break;

      case 'badge':
      case 'achievement':
        navigate('/badges');
        break;

      case 'ai_conversation':
      case 'ai_conversation_notification':
        if (notification.extra_data?.conversation_id) {
          navigate(`/ai-conversations/${notification.extra_data.conversation_id}`);
        } else {
          navigate('/ai-conversations');
        }
        break;

      case 'moderation':
      case 'moderation_notification':
      case 'report':
        navigate('/profile');
        break;

      case 'system':
      case 'security_alert':
      case 'welcome':
      default:
        // For system notifications or unknown types, just mark as read and stay on page        break;
    }
  };

  // Handle individual notification mark as read
  const handleMarkAsRead = async (notificationId) => {
    try {
      setIsLoading(true);
      await actions.markAsRead(notificationId);
    } catch (error) {    } finally {
      setIsLoading(false);
    }
  };

  // Handle mark all as read
  const handleMarkAllAsRead = async () => {
    try {
      setIsLoading(true);
      await actions.markAllAsRead();
    } catch (error) {    } finally {
      setIsLoading(false);
    }
  };

  // Handle bulk actions
  const handleBulkMarkAsRead = async () => {
    if (selectedNotifications.length === 0) return;

    try {
      setIsLoading(true);
      // Mark selected notifications as read
      await Promise.all(
        selectedNotifications.map(id => actions.markAsRead(id))
      );
      setSelectedNotifications([]);
    } catch (error) {    } finally {
      setIsLoading(false);
    }
  };

  // Toggle notification selection
  const toggleNotificationSelection = (notificationId) => {
    setSelectedNotifications(prev =>
      prev.includes(notificationId)
        ? prev.filter(id => id !== notificationId)
        : [...prev, notificationId]
    );
  };

  // Select all filtered notifications
  const handleSelectAll = () => {
    const allIds = filteredNotifications.map(n => n.id);
    setSelectedNotifications(allIds);
  };

  // Clear selection
  const handleClearSelection = () => {
    setSelectedNotifications([]);
  };

  // Get notification priority color
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 1: return 'text-red-600 bg-red-50 border-red-200';
      case 2: return 'text-orange-600 bg-orange-50 border-orange-200';
      case 3: return 'text-blue-600 bg-blue-50 border-blue-200';
      case 4: return 'text-gray-600 bg-gray-50 border-gray-200';
      case 5: return 'text-gray-400 bg-gray-50 border-gray-200';
      default: return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  // Get notification type badge color
  const getTypeColor = (type) => {
    switch (type) {
      case 'system': return 'bg-gray-100 text-gray-800';
      case 'social': return 'bg-pink-100 text-pink-800';
      case 'equipment': return 'bg-green-100 text-green-800';
      case 'community': return 'bg-purple-100 text-purple-800';
      case 'messaging': return 'bg-blue-100 text-blue-800';
      case 'poll': return 'bg-yellow-100 text-yellow-800';
      case 'ai_conversation': return 'bg-indigo-100 text-indigo-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Format notification time
  const formatNotificationTime = (timestamp) => {
    try {
      const now = new Date();
      const date = new Date(timestamp);
      const diffInMinutes = Math.floor((now - date) / (1000 * 60));

      if (diffInMinutes < 1) return 'Just now';
      if (diffInMinutes < 60) return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
      if (diffInMinutes < 1440) {
        const hours = Math.floor(diffInMinutes / 60);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
      }

      const days = Math.floor(diffInMinutes / 1440);
      if (days < 7) return `${days} day${days > 1 ? 's' : ''} ago`;

      const weeks = Math.floor(days / 7);
      if (weeks < 4) return `${weeks} week${weeks > 1 ? 's' : ''} ago`;

      const months = Math.floor(days / 30);
      if (months < 12) return `${months} month${months > 1 ? 's' : ''} ago`;

      const years = Math.floor(days / 365);
      return `${years} year${years > 1 ? 's' : ''} ago`;
    } catch (error) {
      return 'Unknown time';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <FiBell className="w-6 h-6 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs font-medium px-2 py-1 rounded-full">
                {unreadCount}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <div className={`flex items-center space-x-1 text-sm ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="space-y-4">
          {/* Search and Filters */}
          <div className="flex flex-wrap gap-4 items-center">
            {/* Search */}
            <div className="relative flex-1 min-w-64">
              <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search notifications..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Read/Unread Filter */}
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Notifications</option>
              <option value="unread">Unread Only</option>
              <option value="read">Read Only</option>
            </select>

            {/* Type Filter */}
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Types</option>
              {availableTypes.map(type => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2 items-center">
            <button
              onClick={handleMarkAllAsRead}
              disabled={isLoading || unreadCount === 0}
              className="flex items-center space-x-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FiCheckCircle className="w-4 h-4" />
              <span>Mark All Read</span>
            </button>

            {selectedNotifications.length > 0 && (
              <>
                <button
                  onClick={handleBulkMarkAsRead}
                  disabled={isLoading}
                  className="flex items-center space-x-1 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <FiCheck className="w-4 h-4" />
                  <span>Mark Selected Read ({selectedNotifications.length})</span>
                </button>

                <button
                  onClick={handleClearSelection}
                  className="flex items-center space-x-1 px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  <FiX className="w-4 h-4" />
                  <span>Clear Selection</span>
                </button>
              </>
            )}

            <button
              onClick={handleSelectAll}
              disabled={filteredNotifications.length === 0}
              className="flex items-center space-x-1 px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FiCheck className="w-4 h-4" />
              <span>Select All Visible</span>
            </button>
          </div>
        </div>
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {filteredNotifications.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
            <FiBellOff className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm || filter !== 'all' || typeFilter !== 'all' ? 'No matching notifications' : 'No notifications yet'}
            </h3>
            <p className="text-gray-600">
              {searchTerm || filter !== 'all' || typeFilter !== 'all'
                ? 'Try adjusting your filters or search terms.'
                : 'You\'ll see your notifications here when you receive them.'}
            </p>
          </div>
        ) : (
          filteredNotifications.map(notification => (
            <div
              key={notification.id}
              className={`group bg-white rounded-lg shadow-sm border p-4 transition-all duration-200 cursor-pointer ${
                !notification.read ? 'border-l-4 border-l-blue-500 bg-blue-50/30' : 'hover:bg-gray-50'
              } ${selectedNotifications.includes(notification.id) ? 'ring-2 ring-blue-500 ring-opacity-50' : ''}${
                highlightedNotificationId === notification.id ? ' ring-2 ring-yellow-400 bg-yellow-50' : ''
              }`}
              onClick={() => handleNotificationClick(notification)}
            >
              <div className="flex items-start space-x-4">
                {/* Selection Checkbox */}
                <div className="flex-shrink-0 pt-1" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={selectedNotifications.includes(notification.id)}
                    onChange={() => toggleNotificationSelection(notification.id)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                </div>

                {/* Notification Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="text-lg font-medium text-gray-900 mb-1">
                        {notification.title}
                      </h4>
                      <p className="text-gray-600 mb-3">
                        {notification.message}
                      </p>

                      {/* Metadata */}
                      <div className="flex flex-wrap items-center gap-2 text-sm">
                        {/* Type Badge */}
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(notification.notification_type || notification.type)}`}>
                          {(notification.notification_type || notification.type || 'system').replace('_', ' ')}
                        </span>

                        {/* Priority Badge */}
                        {notification.priority && (
                          <span className={`px-2 py-1 rounded border text-xs font-medium ${getPriorityColor(notification.priority)}`}>
                            Priority {notification.priority}
                          </span>
                        )}

                        {/* Timestamp */}
                        <span className="text-gray-500">
                          {formatNotificationTime(notification.timestamp)}
                        </span>

                        {/* Sender */}
                        {notification.sender && (
                          <span className="text-gray-500">
                            from {notification.sender.display_name || notification.sender.username}
                          </span>
                        )}

                        {/* Read Status */}
                        {!notification.read && (
                          <span className="text-blue-600 font-medium text-xs">
                            UNREAD
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Action Button */}
                    <div className="flex-shrink-0 ml-4 flex items-center space-x-2">
                      {/* Click indicator */}
                      <FiExternalLink className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />

                      {!notification.read && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleMarkAsRead(notification.id);
                          }}
                          disabled={isLoading}
                          className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          <FiCheck className="w-3 h-3" />
                          <span>Mark Read</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex items-center space-x-3">
            <FiRefreshCw className="w-5 h-5 animate-spin text-blue-600" />
            <span className="text-gray-900">Processing...</span>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      {notifications.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex flex-wrap gap-4 text-sm text-gray-600">
            <span>Total: {notifications.length}</span>
            <span>Unread: {unreadCount}</span>
            <span>Showing: {filteredNotifications.length}</span>
            {selectedNotifications.length > 0 && (
              <span>Selected: {selectedNotifications.length}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationsPage;
