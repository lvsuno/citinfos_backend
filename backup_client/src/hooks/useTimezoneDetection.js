/**
 * React Timezone Detection Hook
 *
 * Automatically detects user's device timezone using browser APIs
 * and provides methods for updating session timezone.
 */

import { useState, useEffect, useCallback } from 'react';
import { jwtAuthService } from '../services/jwtAuthService';

export const useTimezoneDetection = (options = {}) => {
  const {
    autoDetect = true,
    debugMode = false,
    fallbackTimezone = 'UTC'
  } = options;

  const [detectedTimezone, setDetectedTimezone] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Detect user's timezone using browser APIs
   */
  const detectTimezone = useCallback(() => {
    try {
      // Method 1: Modern browser Intl API (most accurate)
      if (Intl && Intl.DateTimeFormat) {
        try {
          const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
          if (debugMode) {
            console.log('Timezone detected via Intl API:', timezone);
          }
          setDetectedTimezone(timezone);
          return timezone;
        } catch (error) {
          console.warn('Intl.DateTimeFormat timezone detection failed:', error);
        }
      }

      // Method 2: Fallback using Date object timezone offset
      try {
        const offset = new Date().getTimezoneOffset();
        const timezone = offsetToTimezone(offset);
        if (timezone) {
          if (debugMode) {
            console.log('Timezone detected via offset fallback:', timezone);
          }
          setDetectedTimezone(timezone);
          return timezone;
        }
      } catch (error) {
        console.warn('Offset-based timezone detection failed:', error);
      }

      // Method 3: Final fallback
      if (debugMode) {
        console.warn('Using fallback timezone:', fallbackTimezone);
      }
      setDetectedTimezone(fallbackTimezone);
      return fallbackTimezone;
    } catch (error) {
      console.error('Timezone detection failed:', error);
      setError(error.message);
      setDetectedTimezone(fallbackTimezone);
      return fallbackTimezone;
    }
  }, [debugMode, fallbackTimezone]);

  /**
   * Convert timezone offset to timezone name (basic mapping)
   */
  const offsetToTimezone = useCallback((offset) => {
    const offsetMap = {
      '0': 'UTC',
      '-60': 'Europe/London',
      '-120': 'Europe/Berlin',
      '-300': 'America/New_York',
      '-360': 'America/Chicago',
      '-420': 'America/Denver',
      '-480': 'America/Los_Angeles',
      '-540': 'America/Anchorage',
      '-600': 'Pacific/Honolulu',
      '60': 'Africa/Lagos',
      '120': 'Africa/Cairo',
      '180': 'Europe/Moscow',
      '240': 'Asia/Dubai',
      '300': 'Asia/Karachi',
      '330': 'Asia/Kolkata',
      '360': 'Asia/Dhaka',
      '420': 'Asia/Bangkok',
      '480': 'Asia/Shanghai',
      '540': 'Asia/Tokyo',
      '600': 'Australia/Sydney',
      '660': 'Pacific/Noumea',
      '720': 'Pacific/Auckland'
    };

    return offsetMap[offset.toString()] || null;
  }, []);

  /**
   * Update session timezone on the server
   */
  const updateSessionTimezone = useCallback(async (timezone = null) => {
    const timezoneToUpdate = timezone || detectedTimezone;
    if (!timezoneToUpdate) {
      throw new Error('No timezone available to update');
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await jwtAuthService.api.post('/api/auth/update-session-timezone/', {
        timezone: timezoneToUpdate
      });

      if (debugMode) {
        console.log('Session timezone updated successfully:', response.data);
      }

      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to update session timezone';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [detectedTimezone, debugMode]);

  /**
   * Validate timezone-based access to a community
   */
  const validateCommunityTimezoneAccess = useCallback(async (communityId) => {
    try {
      const response = await jwtAuthService.api.post(
        `/api/communities/${communityId}/validate-timezone-access/`
      );
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to validate timezone access';
      throw new Error(errorMessage);
    }
  }, []);

  /**
   * Get detected timezone
   */
  const getTimezone = useCallback(() => {
    return detectedTimezone || fallbackTimezone;
  }, [detectedTimezone, fallbackTimezone]);

  /**
   * Store timezone in localStorage for social auth callbacks
   */
  const storeTimezoneLocally = useCallback(() => {
    try {
      const timezone = getTimezone();
      localStorage.setItem('user_timezone', timezone);
      if (debugMode) {
        console.log('Timezone stored in localStorage:', timezone);
      }
    } catch (error) {
      console.warn('Failed to store timezone in localStorage:', error);
    }
  }, [getTimezone, debugMode]);

  // Auto-detect timezone on mount
  useEffect(() => {
    if (autoDetect) {
      detectTimezone();
    }
  }, [autoDetect, detectTimezone]);

  // Store timezone locally when detected
  useEffect(() => {
    if (detectedTimezone) {
      storeTimezoneLocally();
    }
  }, [detectedTimezone, storeTimezoneLocally]);

  // Debug logging
  useEffect(() => {
    if (debugMode && detectedTimezone) {
      console.log('Timezone Detection Debug Info:', {
        detectedTimezone,
        isLoading,
        error,
        browserSupport: {
          intl: !!(Intl && Intl.DateTimeFormat),
          offset: !isNaN(new Date().getTimezoneOffset())
        }
      });
    }
  }, [debugMode, detectedTimezone, isLoading, error]);

  return {
    detectedTimezone,
    isLoading,
    error,
    detectTimezone,
    updateSessionTimezone,
    validateCommunityTimezoneAccess,
    getTimezone,
    storeTimezoneLocally
  };
};

/**
 * Higher-order component for automatic timezone detection and session update
 */
export const withTimezoneDetection = (WrappedComponent) => {
  return function TimezoneDetectionWrapper(props) {
    const timezone = useTimezoneDetection({
      autoDetect: true,
      debugMode: process.env.NODE_ENV === 'development'
    });

    return <WrappedComponent {...props} timezone={timezone} />;
  };
};

export default useTimezoneDetection;
