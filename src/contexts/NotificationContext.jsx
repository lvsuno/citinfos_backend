/**
 * Notification Context for Managing Real-time Notifications
 *
 * Provides global state management for notifications across the app
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { notificationWebSocket } from '../services/notificationWebSocket';
import { useAuth } from './AuthContext';
import apiService from '../services/apiService';

// Initial state
const initialState = {
  notifications: [],
  unreadCount: 0,
  isConnected: false,
  isConnecting: false,
  connectionFailed: false,
  lastUpdate: null,
  settings: {
    showToasts: true,
    playSound: true,
    maxToasts: 5,
    toastDuration: 5000,
  }
};

// Action types
const ActionTypes = {
  SET_CONNECTION_STATUS: 'SET_CONNECTION_STATUS',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  UPDATE_NOTIFICATION: 'UPDATE_NOTIFICATION',
  MARK_AS_READ: 'MARK_AS_READ',
  MARK_ALL_AS_READ: 'MARK_ALL_AS_READ',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION',
  SET_NOTIFICATIONS: 'SET_NOTIFICATIONS',
  UPDATE_UNREAD_COUNT: 'UPDATE_UNREAD_COUNT',
  UPDATE_SETTINGS: 'UPDATE_SETTINGS',
  CONNECTION_FAILED: 'CONNECTION_FAILED',
  CLEAR_NOTIFICATIONS: 'CLEAR_NOTIFICATIONS',
};

// Reducer function
function notificationReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_CONNECTION_STATUS:
      return {
        ...state,
        isConnected: action.payload.connected,
        isConnecting: action.payload.connecting || false,
        connectionFailed: action.payload.failed || false,
        lastUpdate: new Date().toISOString(),
      };

    case ActionTypes.ADD_NOTIFICATION:
      const newNotification = {
        ...action.payload,
        id: action.payload.id || `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: action.payload.timestamp || new Date().toISOString(),
        read: action.payload.read || false,
      };

      // Check if notification with same ID already exists
      const existingNotification = state.notifications.find(n => n.id === newNotification.id);
      if (existingNotification) {
        console.warn('Duplicate notification ID detected:', newNotification.id);
        return state; // Don't add duplicate
      }

      return {
        ...state,
        notifications: [newNotification, ...state.notifications],
        unreadCount: !newNotification.read ? state.unreadCount + 1 : state.unreadCount,
        lastUpdate: new Date().toISOString(),
      };

    case ActionTypes.UPDATE_NOTIFICATION:
      return {
        ...state,
        notifications: state.notifications.map(notification =>
          notification.id === action.payload.id
            ? { ...notification, ...action.payload }
            : notification
        ),
        lastUpdate: new Date().toISOString(),
      };

    case ActionTypes.MARK_AS_READ:
      return {
        ...state,
        notifications: state.notifications.map(notification =>
          notification.id === action.payload.id
            ? { ...notification, read: true }
            : notification
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
        lastUpdate: new Date().toISOString(),
      };

    case ActionTypes.MARK_ALL_AS_READ:
      return {
        ...state,
        notifications: state.notifications.map(notification => ({
          ...notification,
          read: true
        })),
        unreadCount: 0,
        lastUpdate: new Date().toISOString(),
      };

    case ActionTypes.REMOVE_NOTIFICATION:
      const removedNotification = state.notifications.find(n => n.id === action.payload.id);
      return {
        ...state,
        notifications: state.notifications.filter(notification =>
          notification.id !== action.payload.id
        ),
        unreadCount: removedNotification && !removedNotification.read
          ? Math.max(0, state.unreadCount - 1)
          : state.unreadCount,
        lastUpdate: new Date().toISOString(),
      };

    case ActionTypes.SET_NOTIFICATIONS:
      const unreadCount = action.payload.filter(n => !n.read).length;
      return {
        ...state,
        notifications: action.payload,
        unreadCount,
        lastUpdate: new Date().toISOString(),
      };

    case ActionTypes.UPDATE_UNREAD_COUNT:
      return {
        ...state,
        unreadCount: action.payload.count,
        lastUpdate: new Date().toISOString(),
      };

    case ActionTypes.UPDATE_SETTINGS:
      return {
        ...state,
        settings: { ...state.settings, ...action.payload },
      };

    case ActionTypes.CONNECTION_FAILED:
      return {
        ...state,
        isConnected: false,
        isConnecting: false,
        connectionFailed: true,
        lastUpdate: new Date().toISOString(),
      };

    case ActionTypes.CLEAR_NOTIFICATIONS:
      return {
        ...state,
        notifications: [],
        unreadCount: 0,
        lastUpdate: new Date().toISOString(),
      };

    default:
      return state;
  }
}

// Create context
const NotificationContext = createContext();

// Provider component
export const NotificationProvider = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const [state, dispatch] = useReducer(notificationReducer, initialState);

  // WebSocket message handler
  const handleWebSocketMessage = useCallback((message) => {
    console.log('📨 Notification context received:', message);

    switch (message.type) {
      case 'connection_established':
        dispatch({
          type: ActionTypes.SET_CONNECTION_STATUS,
          payload: { connected: true, connecting: false, failed: false }
        });
        break;

      case 'token_renewed':
        console.log('🔄 JWT token renewed via WebSocket - updating local storage');
        // Token has been automatically updated by the WebSocket service
        // Just log for debugging - no additional action needed
        break;

      case 'connection_lost':
        dispatch({
          type: ActionTypes.SET_CONNECTION_STATUS,
          payload: { connected: false, connecting: false, failed: false }
        });
        break;

      case 'connection_failed':
        dispatch({
          type: ActionTypes.CONNECTION_FAILED,
          payload: {}
        });
        break;

      case 'notification':
      case 'system_notification':
      case 'social_notification':
      case 'community_notification':
      case 'equipment_notification':
      case 'messaging_notification':
      case 'poll_notification':
      case 'ai_conversation_notification':
      case 'analytics_notification':
      case 'moderation_notification':
        dispatch({
          type: ActionTypes.ADD_NOTIFICATION,
          payload: message.data
        });

        // Play sound if enabled
        if (state.settings.playSound) {
          playNotificationSound();
        }
        break;

      case 'notification_read':
        dispatch({
          type: ActionTypes.MARK_AS_READ,
          payload: { id: message.data.notification_id }
        });
        break;

      case 'notifications_history':
        dispatch({
          type: ActionTypes.SET_NOTIFICATIONS,
          payload: message.data.notifications
        });
        break;

      case 'unread_count':
        dispatch({
          type: ActionTypes.UPDATE_UNREAD_COUNT,
          payload: { count: message.data.count }
        });
        break;

      default:
        console.log('Unknown notification message type:', message.type);
    }
  }, [state.settings.playSound]);

  // Play notification sound
  const playNotificationSound = useCallback(() => {
    try {
      // Create a simple notification sound using Web Audio API
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      console.log('Could not play notification sound:', error);
    }
  }, []);

  // Fetch existing notifications from API
  const fetchExistingNotifications = async () => {
    try {
      console.log('📥 Fetching existing notifications from API...');
      const response = await apiService.get('/notifications/?limit=50'); // Get last 50 notifications

      if (response.data && response.data.results) {
        const notifications = response.data.results.map(notif => ({
          id: notif.id,
          title: notif.title,
          message: notif.message,
          notification_type: notif.notification_type,
          priority: notif.priority,
          read: notif.is_read,
          timestamp: notif.created_at,
          sender: notif.sender ? {
            id: notif.sender.id,
            username: notif.sender.username || 'System',
            display_name: notif.sender.display_name
          } : null,
          extra_data: notif.extra_data || {}
        }));

        console.log(`📥 Loaded ${notifications.length} existing notifications`);

        dispatch({
          type: ActionTypes.SET_NOTIFICATIONS,
          payload: notifications
        });
      }
    } catch (error) {
      console.error('❌ Failed to fetch existing notifications:', error);
      // Don't show error to user for this background operation
    }
  };

  // Initialize WebSocket connection based on authentication status
  useEffect(() => {
    console.log('🔌 NotificationContext: Auth state changed', {
      isAuthenticated,
      hasUser: !!user,
      isConnected: state.isConnected,
      isConnecting: state.isConnecting
    });

    if (!isAuthenticated || !user) {
      // User is not authenticated, disconnect if connected
      if (state.isConnected) {
        console.log('🔌 Disconnecting WebSocket - user not authenticated');
        notificationWebSocket.disconnect();
        dispatch({
          type: ActionTypes.SET_CONNECTION_STATUS,
          payload: { connected: false, connecting: false, failed: false }
        });
      }
      return;
    }

    // User is authenticated, ensure WebSocket is connected
    const token = apiService.getAccessToken();
    const isTokenExpired = !token || notificationWebSocket.isTokenExpired(token);

    if (token && !isTokenExpired && !state.isConnected && !state.isConnecting) {
      console.log('🔌 Establishing WebSocket connection for authenticated user:', user.username);

      // Timing client-side notification startup tasks
      console.time('fetchExistingNotifications');
      dispatch({
        type: ActionTypes.SET_CONNECTION_STATUS,
        payload: { connected: false, connecting: true, failed: false }
      });

      // Fetch existing notifications first (non-blocking)
      fetchExistingNotifications().finally(() => console.timeEnd('fetchExistingNotifications'));

      // Connect with universal authentication - WebSocket service handles token and session ID internally
      notificationWebSocket.connect(handleWebSocketMessage);
    } else if (state.isConnected) {
      console.log('✅ WebSocket already connected for user:', user.username);
    } else if (state.isConnecting) {
      console.log('🔄 WebSocket connection in progress for user:', user.username);
    }

    // Add WebSocket listener for connection status updates
    const unsubscribe = notificationWebSocket.addListener((message) => {
      console.log('📡 WebSocket status update:', message);

      switch (message.type) {
        case 'connection_opened':
          console.log('✅ WebSocket connection established');
          dispatch({
            type: ActionTypes.SET_CONNECTION_STATUS,
            payload: { connected: true, connecting: false, failed: false }
          });
          break;
        case 'connection_closed':
          console.log('🔌 WebSocket connection closed');
          dispatch({
            type: ActionTypes.SET_CONNECTION_STATUS,
            payload: { connected: false, connecting: false, failed: false }
          });
          break;
        case 'connection_error':
          console.error('❌ WebSocket connection error');
          dispatch({
            type: ActionTypes.CONNECTION_FAILED,
            payload: {}
          });
          break;
        case 'connection_failed':
          console.error('❌ WebSocket connection failed');
          dispatch({
            type: ActionTypes.CONNECTION_FAILED,
            payload: {}
          });
          break;
        default:
          // Other messages are already handled by the main handleWebSocketMessage
          // Don't double-process them here
          break;
      }
    });

    return () => {
      unsubscribe();
    };
  }, [isAuthenticated, user, state.isConnected, state.isConnecting, handleWebSocketMessage]);

  // Action creators
  const actions = {
    markAsRead: async (notificationId) => {
      try {
        // Call API to mark notification as read
        await apiService.post('/notifications/mark-read/', {
          notification_ids: [notificationId]
        });

        // Update local state
        dispatch({
          type: ActionTypes.MARK_AS_READ,
          payload: { id: notificationId }
        });
      } catch (error) {
        console.error('Failed to mark notification as read:', error);
      }
    },

    markAllAsRead: async () => {
      try {
        // Call API to mark all notifications as read
        await apiService.post('/notifications/mark-read/', {
          notification_ids: []
        });

        // Update local state
        dispatch({
          type: ActionTypes.MARK_ALL_AS_READ,
          payload: {}
        });
      } catch (error) {
        console.error('Failed to mark all notifications as read:', error);
      }
    },

    removeNotification: (notificationId) => {
      dispatch({
        type: ActionTypes.REMOVE_NOTIFICATION,
        payload: { id: notificationId }
      });
    },

    requestHistory: async (page = 1, limit = 20) => {
      try {
        // Call API to get notification history
        const response = await apiService.get(`/notifications/?page=${page}&limit=${limit}`);

        if (response.data && response.data.results) {
          const notifications = response.data.results.map(notif => ({
            id: notif.id,
            title: notif.title,
            message: notif.message,
            notification_type: notif.notification_type,
            priority: notif.priority,
            read: notif.is_read,
            timestamp: notif.created_at,
            sender: notif.sender ? {
              id: notif.sender.id,
              username: notif.sender.username || 'System',
              display_name: notif.sender.display_name
            } : null,
            extra_data: notif.extra_data || {}
          }));

          dispatch({
            type: ActionTypes.SET_NOTIFICATIONS,
            payload: notifications
          });
        }
      } catch (error) {
        console.error('Failed to fetch notification history:', error);
      }
    },

    updateSettings: (newSettings) => {
      dispatch({
        type: ActionTypes.UPDATE_SETTINGS,
        payload: newSettings
      });

      // Save to localStorage
      localStorage.setItem('notificationSettings', JSON.stringify({
        ...state.settings,
        ...newSettings
      }));
    },

    clearNotifications: () => {
      dispatch({
        type: ActionTypes.CLEAR_NOTIFICATIONS,
        payload: {}
      });
    },

    reconnect: () => {
      const token = apiService.getAccessToken();
      const isTokenExpired = !token || notificationWebSocket.isTokenExpired(token);

      if (token && !isTokenExpired) {
        dispatch({
          type: ActionTypes.SET_CONNECTION_STATUS,
          payload: { connected: false, connecting: true, failed: false }
        });
        // Universal WebSocket authentication - service handles token and session ID
        notificationWebSocket.connect(handleWebSocketMessage);
      } else {
        console.warn('Cannot reconnect: No valid JWT token available');
      }
    }
  };

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('notificationSettings');
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings);
        dispatch({
          type: ActionTypes.UPDATE_SETTINGS,
          payload: settings
        });
      } catch (error) {
        console.error('Failed to load notification settings:', error);
      }
    }
  }, []);

  const contextValue = {
    ...state,
    actions
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
    </NotificationContext.Provider>
  );
};

// Hook to use the notification context
export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}

export default NotificationContext;
