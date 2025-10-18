/**
 * usePostViewTracker Hook
 * Provides comprehensive post view tracking functionality for React components
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useIntersectionObserver } from './useIntersectionObserver';
import analyticsAPI from '../services/analyticsAPI';

/**
 * Custom hook for tracking post views with advanced analytics
 * @param {string} postId - The unique identifier for the post
 * @param {Object} options - Configuration options for tracking
 * @returns {Object} Tracking state and methods
 */
export const usePostViewTracker = (postId, options = {}) => {
  const {
    threshold = 0.5, // How much of the post must be visible (50%)
    minViewTime = 1000, // Minimum time in milliseconds to count as a view (1 second)
    trackReadTime = true, // Whether to track reading time
    trackScrollDepth = true, // Whether to track scroll depth
    debounceTime = 300, // Debounce time for scroll events
    autoTrack = true, // Whether to automatically track views
    onViewTracked = null, // Callback when view is tracked
    onEngagement = null, // Callback when engagement is tracked
  } = options;

  // Refs for tracking
  const elementRef = useRef(null);
  const viewStartTime = useRef(null);
  const totalReadTime = useRef(0);
  const maxScrollDepth = useRef(0);
  const hasTrackedView = useRef(false);
  const isVisible = useRef(false);
  const scrollDepthInterval = useRef(null);

  // State
  const [viewData, setViewData] = useState({
    isViewing: false,
    readTime: 0,
    scrollDepth: 0,
    hasViewed: false,
    engagements: []
  });

  // Track scroll depth
  const updateScrollDepth = useCallback(() => {
    if (!elementRef.current || !trackScrollDepth) return;

    const element = elementRef.current;
    const rect = element.getBoundingClientRect();
    const elementHeight = element.offsetHeight;
    const viewportHeight = window.innerHeight;

    // Calculate how much of the element is visible
    const visibleTop = Math.max(0, -rect.top);
    const visibleBottom = Math.min(elementHeight, viewportHeight - rect.top);
    const visibleHeight = Math.max(0, visibleBottom - visibleTop);
    const scrollDepth = (visibleHeight / elementHeight) * 100;

    maxScrollDepth.current = Math.max(maxScrollDepth.current, scrollDepth);

    setViewData(prev => ({
      ...prev,
      scrollDepth: maxScrollDepth.current
    }));
  }, [trackScrollDepth]);

  // Debounced scroll handler
  const debouncedScrollHandler = useCallback(
    debounce(updateScrollDepth, debounceTime),
    [updateScrollDepth, debounceTime]
  );

  // Handle when element becomes visible
  const handleIntersection = useCallback(async (isIntersecting) => {
    if (!postId || !autoTrack) return;

    if (isIntersecting && !isVisible.current) {
      // Element became visible
      isVisible.current = true;
      if (trackReadTime) {
        viewStartTime.current = Date.now();
      }

      setViewData(prev => ({
        ...prev,
        isViewing: true
      }));

      // Start tracking scroll depth
      if (trackScrollDepth) {
        scrollDepthInterval.current = setInterval(updateScrollDepth, 500);
        window.addEventListener('scroll', debouncedScrollHandler, { passive: true });
      }

    } else if (!isIntersecting && isVisible.current) {
      // Element became invisible
      isVisible.current = false;
      const currentTime = Date.now();
      let sessionTime = 0;

      // Only calculate session time if read time tracking is enabled
      if (trackReadTime && viewStartTime.current) {
        sessionTime = currentTime - viewStartTime.current;
        totalReadTime.current += sessionTime;
      }

      setViewData(prev => ({
        ...prev,
        isViewing: false,
        readTime: trackReadTime ? totalReadTime.current : 0
      }));

      // Clean up scroll tracking
      if (scrollDepthInterval.current) {
        clearInterval(scrollDepthInterval.current);
        scrollDepthInterval.current = null;
      }
      window.removeEventListener('scroll', debouncedScrollHandler);

      // Track view if it meets minimum time requirement
      if (sessionTime >= minViewTime && !hasTrackedView.current) {
        await trackView({
          readTime: trackReadTime ? totalReadTime.current : 0,
          scrollDepth: maxScrollDepth.current,
          timeOnPage: currentTime - (window.pageLoadTime || currentTime)
        });
      }
    }
  }, [postId, autoTrack, minViewTime, trackReadTime, trackScrollDepth, updateScrollDepth, debouncedScrollHandler]);  // Use intersection observer
  useIntersectionObserver(elementRef, handleIntersection, {
    threshold,
    rootMargin: '0px'
  });

  // Track post view
  const trackView = useCallback(async (extraData = {}) => {
    if (!postId || hasTrackedView.current) return false;

    try {
      const result = await analyticsAPI.trackPostView(postId, {
        readTime: trackReadTime ? totalReadTime.current : 0,
        scrollDepth: maxScrollDepth.current,
        referrer: document.referrer,
        timeOnPage: Date.now() - (window.pageLoadTime || Date.now()),
        ...extraData
      });

      if (result) {
        hasTrackedView.current = true;
        setViewData(prev => ({
          ...prev,
          hasViewed: true
        }));

        if (onViewTracked) {
          onViewTracked(result);
        }

        return true;
      }
    } catch (error) {    }

    return false;
  }, [postId, trackReadTime, onViewTracked]);

  // Track engagement
  const trackEngagement = useCallback(async (action, metadata = {}) => {
    if (!postId) return false;

    try {
      const result = await analyticsAPI.trackPostEngagement(postId, action, {
        readTime: trackReadTime ? totalReadTime.current : 0,
        scrollDepth: maxScrollDepth.current,
        ...metadata
      });

      if (result) {
        setViewData(prev => ({
          ...prev,
          engagements: [...prev.engagements, { action, timestamp: Date.now(), ...metadata }]
        }));

        if (onEngagement) {
          onEngagement(action, result);
        }

        return true;
      }
    } catch (error) {    }

    return false;
  }, [postId, trackReadTime, onEngagement]);

  // Manual tracking methods
  const manualTrackView = useCallback(() => trackView(), [trackView]);
  const markAsRead = useCallback(async () => {
    if (!postId) return false;
    try {
      const result = await analyticsAPI.markPostAsRead(postId);
      return !!result;
    } catch (error) {      return false;
    }
  }, [postId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (scrollDepthInterval.current) {
        clearInterval(scrollDepthInterval.current);
      }
      window.removeEventListener('scroll', debouncedScrollHandler);

      // Track final view if component unmounts while viewing
      if (isVisible.current && !hasTrackedView.current && totalReadTime.current >= minViewTime) {
        trackView({
          readTime: trackReadTime ? totalReadTime.current : 0,
          scrollDepth: maxScrollDepth.current,
          isUnmountTracking: true
        });
      }
    };
  }, [debouncedScrollHandler, trackView, minViewTime, trackReadTime]);  // Store page load time
  useEffect(() => {
    if (!window.pageLoadTime) {
      window.pageLoadTime = Date.now();
    }
  }, []);

  return {
    // Ref to attach to the post element
    ref: elementRef,

    // View state
    isViewing: viewData.isViewing,
    hasViewed: viewData.hasViewed,
    readTime: viewData.readTime,
    scrollDepth: viewData.scrollDepth,
    engagements: viewData.engagements,

    // Manual tracking methods
    trackView: manualTrackView,
    trackEngagement,
    markAsRead,

    // Utility methods
    getReadTime: () => trackReadTime ? totalReadTime.current : 0,
    getScrollDepth: () => maxScrollDepth.current,
    resetTracking: () => {
      hasTrackedView.current = false;
      totalReadTime.current = 0;
      maxScrollDepth.current = 0;
      setViewData({
        isViewing: false,
        readTime: 0,
        scrollDepth: 0,
        hasViewed: false,
        engagements: []
      });
    }
  };
};

/**
 * Debounce utility function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

export default usePostViewTracker;
