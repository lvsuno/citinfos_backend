/**
 * Analytics Context
 * Provides global analytics configuration and state management
 */

import React, { createContext, useContext, useReducer, useEffect } from 'react';
import PropTypes from 'prop-types';
import analyticsAPI from '../services/analyticsAPI';

// Initial state
const initialState = {
  isEnabled: true,
  batchMode: false,
  batchSize: 10,
  batchInterval: 5000, // 5 seconds
  settings: {
    trackViews: true,
    trackEngagement: true,
    trackReadTime: true,
    trackScrollDepth: true,
    minViewTime: 1000,
    viewThreshold: 0.5
  },
  pendingViews: [],
  stats: {
    totalViews: 0,
    totalEngagements: 0,
    sessionsToday: 0
  },
  user: null,
  debug: process.env.NODE_ENV === 'development'
};

// Action types
const ANALYTICS_ACTIONS = {
  SET_ENABLED: 'SET_ENABLED',
  SET_SETTINGS: 'SET_SETTINGS',
  SET_BATCH_MODE: 'SET_BATCH_MODE',
  ADD_PENDING_VIEW: 'ADD_PENDING_VIEW',
  CLEAR_PENDING_VIEWS: 'CLEAR_PENDING_VIEWS',
  UPDATE_STATS: 'UPDATE_STATS',
  SET_USER: 'SET_USER',
  SET_DEBUG: 'SET_DEBUG'
};

// Reducer
const analyticsReducer = (state, action) => {
  switch (action.type) {
    case ANALYTICS_ACTIONS.SET_ENABLED:
      return { ...state, isEnabled: action.payload };

    case ANALYTICS_ACTIONS.SET_SETTINGS:
      return {
        ...state,
        settings: { ...state.settings, ...action.payload }
      };

    case ANALYTICS_ACTIONS.SET_BATCH_MODE:
      return {
        ...state,
        batchMode: action.payload.enabled,
        batchSize: action.payload.size || state.batchSize,
        batchInterval: action.payload.interval || state.batchInterval
      };

    case ANALYTICS_ACTIONS.ADD_PENDING_VIEW:
      return {
        ...state,
        pendingViews: [...state.pendingViews, action.payload]
      };

    case ANALYTICS_ACTIONS.CLEAR_PENDING_VIEWS:
      return { ...state, pendingViews: [] };

    case ANALYTICS_ACTIONS.UPDATE_STATS:
      return {
        ...state,
        stats: { ...state.stats, ...action.payload }
      };

    case ANALYTICS_ACTIONS.SET_USER:
      return { ...state, user: action.payload };

    case ANALYTICS_ACTIONS.SET_DEBUG:
      return { ...state, debug: action.payload };

    default:
      return state;
  }
};

// Create context
const AnalyticsContext = createContext();

// Provider component
export const AnalyticsProvider = ({ children, initialConfig = {} }) => {
  const [state, dispatch] = useReducer(analyticsReducer, {
    ...initialState,
    ...initialConfig
  });

  // Batch processing effect
  useEffect(() => {
    if (!state.batchMode || state.pendingViews.length === 0) return;

    const shouldFlush =
      state.pendingViews.length >= state.batchSize ||
      (state.pendingViews.length > 0 && Date.now() - state.pendingViews[0].timestamp > state.batchInterval);

    if (shouldFlush) {
      flushPendingViews();
    }

    const interval = setInterval(() => {
      if (state.pendingViews.length > 0) {
        flushPendingViews();
      }
    }, state.batchInterval);

    return () => clearInterval(interval);
  }, [state.pendingViews, state.batchMode, state.batchSize, state.batchInterval]);

  // Analytics methods
  const trackPostView = async (postId, data = {}) => {
    if (!state.isEnabled || !state.settings.trackViews) return false;

    const viewData = {
      postId,
      timestamp: Date.now(),
      userId: state.user?.id,
      ...data
    };

    if (state.batchMode) {
      dispatch({
        type: ANALYTICS_ACTIONS.ADD_PENDING_VIEW,
        payload: viewData
      });
      return true;
    } else {
      try {
        const result = await analyticsAPI.trackPostView(postId, data);
        if (result) {
          dispatch({
            type: ANALYTICS_ACTIONS.UPDATE_STATS,
            payload: { totalViews: state.stats.totalViews + 1 }
          });
        }
        return !!result;
      } catch (error) {
        console.error('Failed to track post view:', error);
        return false;
      }
    }
  };

  const trackEngagement = async (postId, action, metadata = {}) => {
    if (!state.isEnabled || !state.settings.trackEngagement) return false;

    try {
      const result = await analyticsAPI.trackPostEngagement(postId, action, metadata);
      if (result) {
        dispatch({
          type: ANALYTICS_ACTIONS.UPDATE_STATS,
          payload: { totalEngagements: state.stats.totalEngagements + 1 }
        });
      }
      return !!result;
    } catch (error) {
      console.error('Failed to track engagement:', error);
      return false;
    }
  };

  const flushPendingViews = async () => {
    if (state.pendingViews.length === 0) return;

    try {
      const viewsToFlush = [...state.pendingViews];
      dispatch({ type: ANALYTICS_ACTIONS.CLEAR_PENDING_VIEWS });

      await analyticsAPI.batchTrackPostViews(viewsToFlush);

      dispatch({
        type: ANALYTICS_ACTIONS.UPDATE_STATS,
        payload: { totalViews: state.stats.totalViews + viewsToFlush.length }
      });

      if (state.debug) {
        console.log(`Flushed ${viewsToFlush.length} pending views`);
      }
    } catch (error) {
      console.error('Failed to flush pending views:', error);
      // Re-add views to queue on failure
      state.pendingViews.forEach(view => {
        dispatch({
          type: ANALYTICS_ACTIONS.ADD_PENDING_VIEW,
          payload: view
        });
      });
    }
  };

  const updateSettings = (newSettings) => {
    dispatch({
      type: ANALYTICS_ACTIONS.SET_SETTINGS,
      payload: newSettings
    });
  };

  const setBatchMode = (enabled, options = {}) => {
    dispatch({
      type: ANALYTICS_ACTIONS.SET_BATCH_MODE,
      payload: { enabled, ...options }
    });
  };

  const setEnabled = (enabled) => {
    dispatch({
      type: ANALYTICS_ACTIONS.SET_ENABLED,
      payload: enabled
    });
  };

  const setUser = (user) => {
    dispatch({
      type: ANALYTICS_ACTIONS.SET_USER,
      payload: user
    });
  };

  const getAnalyticsData = async (postId) => {
    try {
      return await analyticsAPI.getPostAnalytics(postId);
    } catch (error) {
      console.error('Failed to get analytics data:', error);
      return null;
    }
  };

  const getReadingStats = async () => {
    try {
      return await analyticsAPI.getReadingStats();
    } catch (error) {
      console.error('Failed to get reading stats:', error);
      return null;
    }
  };

  // Context value
  const value = {
    // State
    ...state,

    // Methods
    trackPostView,
    trackEngagement,
    flushPendingViews,
    updateSettings,
    setBatchMode,
    setEnabled,
    setUser,
    getAnalyticsData,
    getReadingStats,

    // Utilities
    isTrackingEnabled: state.isEnabled && state.settings.trackViews,
    isEngagementTrackingEnabled: state.isEnabled && state.settings.trackEngagement,
    pendingViewsCount: state.pendingViews.length
  };

  return (
    <AnalyticsContext.Provider value={value}>
      {children}
    </AnalyticsContext.Provider>
  );
};

AnalyticsProvider.propTypes = {
  children: PropTypes.node.isRequired,
  initialConfig: PropTypes.object
};

// Hook to use analytics context
export const useAnalytics = () => {
  const context = useContext(AnalyticsContext);
  if (!context) {
    throw new Error('useAnalytics must be used within an AnalyticsProvider');
  }
  return context;
};

export default AnalyticsContext;
