/**
 * useRealTimeNotifications - Custom hook for real-time notifications
 *
 * Provides easy access to notification functionality and real-time updates
 */

import { useEffect, useCallback, useRef } from 'react';
import { useNotifications } from '../context/NotificationContext';
import { notificationWebSocket } from '../services/notificationWebSocket';

/**
 * Custom hook for managing real-time notifications
 * @param {Object} options - Configuration options
 * @param {boolean} options.autoConnect - Whether to auto-connect on mount
 * @param {boolean} options.enableToasts - Whether to show toast notifications
 * @param {boolean} options.enableSound - Whether to play notification sounds
 * @param {Function} options.onNotification - Callback for new notifications
 * @param {Function} options.onConnection - Callback for connection changes
 */
export const useRealTimeNotifications = (options = {}) => {
  const {
    autoConnect = true,
    enableToasts = true,
    enableSound = true,
    onNotification,
    onConnection
  } = options;

  const {
    notifications,
    unreadCount,
    isConnected,
    isConnecting,
    connectionFailed,
    settings,
    actions
  } = useNotifications();

  const onNotificationRef = useRef(onNotification);
  const onConnectionRef = useRef(onConnection);

  // Keep refs updated
  useEffect(() => {
    onNotificationRef.current = onNotification;
    onConnectionRef.current = onConnection;
  }, [onNotification, onConnection]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && !isConnected && !isConnecting) {
      const token = localStorage.getItem('access_token');
      if (token) {
        actions.reconnect();
      }
    }
  }, [autoConnect, isConnected, isConnecting, actions]);

  // Update settings
  useEffect(() => {
    if (enableToasts !== settings.showToasts || enableSound !== settings.playSound) {
      actions.updateSettings({
        showToasts: enableToasts,
        playSound: enableSound
      });
    }
  }, [enableToasts, enableSound, settings.showToasts, settings.playSound, actions]);

  // Listen for new notifications
  useEffect(() => {
    if (onNotificationRef.current && notifications.length > 0) {
      const latestNotification = notifications[0];
      const fiveSecondsAgo = new Date(Date.now() - 5000);
      const notificationTime = new Date(latestNotification.timestamp);

      // Only call callback for very recent notifications
      if (notificationTime > fiveSecondsAgo && !latestNotification.read) {
        onNotificationRef.current(latestNotification);
      }
    }
  }, [notifications]);

  // Listen for connection changes
  useEffect(() => {
    if (onConnectionRef.current) {
      onConnectionRef.current({
        isConnected,
        isConnecting,
        connectionFailed
      });
    }
  }, [isConnected, isConnecting, connectionFailed]);

  // Utility functions
  const connect = useCallback(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // Connect without callback - WebSocket service handles token internally
      notificationWebSocket.connect();
    }
  }, []);

  const disconnect = useCallback(() => {
    notificationWebSocket.disconnect();
  }, []);

  const markAsRead = useCallback((notificationId) => {
    actions.markAsRead(notificationId);
  }, [actions]);

  const markAllAsRead = useCallback(() => {
    actions.markAllAsRead();
  }, [actions]);

  const removeNotification = useCallback((notificationId) => {
    actions.removeNotification(notificationId);
  }, [actions]);

  const requestHistory = useCallback((page = 1, limit = 20) => {
    actions.requestHistory(page, limit);
  }, [actions]);

  const updateSettings = useCallback((newSettings) => {
    actions.updateSettings(newSettings);
  }, [actions]);

  const clearAllNotifications = useCallback(() => {
    actions.clearNotifications();
  }, [actions]);

  // Get notifications by type
  const getNotificationsByType = useCallback((type) => {
    return notifications.filter(notification => notification.type === type);
  }, [notifications]);

  // Get unread notifications
  const getUnreadNotifications = useCallback(() => {
    return notifications.filter(notification => !notification.read);
  }, [notifications]);

  // Get notifications from specific sender
  const getNotificationsFromSender = useCallback((senderId) => {
    return notifications.filter(notification =>
      notification.sender && notification.sender.toString() === senderId.toString()
    );
  }, [notifications]);

  return {
    // State
    notifications,
    unreadCount,
    isConnected,
    isConnecting,
    connectionFailed,
    settings,

    // Actions
    connect,
    disconnect,
    markAsRead,
    markAllAsRead,
    removeNotification,
    requestHistory,
    updateSettings,
    clearAllNotifications,

    // Utilities
    getNotificationsByType,
    getUnreadNotifications,
    getNotificationsFromSender,

    // Connection status helpers
    connectionStatus: isConnected ? 'connected' : isConnecting ? 'connecting' : 'disconnected'
  };
};

export default useRealTimeNotifications;
