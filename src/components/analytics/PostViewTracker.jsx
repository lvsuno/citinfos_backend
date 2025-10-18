/**
 * Enhanced PostViewTracker Component with PostSee Integration
 * Tracks detailed post viewing behavior including scroll depth, time spent, and engagement
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import analyticsAPI from '../../services/analyticsAPI';

const PostViewTracker = React.forwardRef(({
  postId,
  postElement,
  source = 'feed',
  onViewTracked,
  onEngagement,
  trackScrollDepth = true,
  trackTimeSpent = true,
  trackClicks = true,
  minViewTime = 1000, // Minimum time to count as a view (ms)
  minScrollPercentage = 25, // Minimum scroll to count as engaged
  children,
  className,
  ...props
}, ref) => {
  const [isTracking, setIsTracking] = useState(false);
  const [viewStartTime, setViewStartTime] = useState(null);
  const [maxScrollPercentage, setMaxScrollPercentage] = useState(0);
  const [viewDuration, setViewDuration] = useState(0);
  const [clickedLinks, setClickedLinks] = useState([]);
  const [mediaViewed, setMediaViewed] = useState([]);
  const [hasTrackedView, setHasTrackedView] = useState(false);

  const intervalRef = useRef(null);
  const scrollTimeoutRef = useRef(null);

  // Custom intersection observer hook
  const useIntersectionObserver = (element, options = {}) => {
    const [isIntersecting, setIsIntersecting] = useState(false);
    const [entry, setEntry] = useState(null);
    const observer = useRef(null);

    useEffect(() => {
      if (!element) return;

      // Clean up previous observer
      if (observer.current) {
        observer.current.disconnect();
      }

      // Create new observer
      observer.current = new IntersectionObserver(
        ([entry]) => {
          setIsIntersecting(entry.isIntersecting);
          setEntry(entry);
        },
        {
          threshold: 0.5,
          rootMargin: '0px',
          ...options,
        }
      );

      // Start observing
      observer.current.observe(element);

      // Cleanup function
      return () => {
        if (observer.current) {
          observer.current.disconnect();
        }
      };
    }, [element, options.threshold, options.rootMargin]);

    return { isIntersecting, entry };
  };

  // Use ref for the container element if provided
  const containerRef = useRef(null);
  const elementToUse = ref || containerRef;

  // Track when post becomes visible - use the actual element or the ref
  const { isIntersecting, entry } = useIntersectionObserver(
    postElement || elementToUse.current,
    {
      threshold: 0.5, // Post is 50% visible
      rootMargin: '0px 0px -10% 0px' // Account for header/footer
    }
  );

  // Calculate scroll percentage within the post
  const calculateScrollPercentage = useCallback(() => {
    const element = postElement || elementToUse.current;
    if (!element || !entry) return 0;

    const rect = element.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    const postHeight = rect.height;

    // Calculate how much of the post has been scrolled past
    const scrolled = Math.max(0, windowHeight - rect.top);
    const percentage = Math.min(100, (scrolled / postHeight) * 100);

    return Math.max(0, percentage);
  }, [postElement, elementToUse, entry]);

  // Track scroll depth
  const handleScroll = useCallback(() => {
    if (!isTracking || !trackScrollDepth) return;

    const currentScrollPercentage = calculateScrollPercentage();
    setMaxScrollPercentage(prev => Math.max(prev, currentScrollPercentage));

    // Clear existing timeout
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    // Debounce scroll tracking
    scrollTimeoutRef.current = setTimeout(() => {
      // Trigger engagement callback if significant scroll
      if (currentScrollPercentage >= minScrollPercentage && onEngagement) {
        onEngagement('scroll', { scrollPercentage: currentScrollPercentage });
      }
    }, 500);
  }, [isTracking, trackScrollDepth, calculateScrollPercentage, minScrollPercentage, onEngagement]);

  // Track clicks within the post
  const handleClick = useCallback((event) => {
    if (!isTracking || !trackClicks) return;

    const target = event.target;

    // Track link clicks
    if (target.tagName === 'A' && target.href) {
      const linkData = {
        url: target.href,
        text: target.textContent?.trim(),
        timestamp: new Date().toISOString(),
        timeFromView: viewDuration
      };

      setClickedLinks(prev => [...prev, linkData]);

      if (onEngagement) {
        onEngagement('link_click', linkData);
      }
    }

    // Track media interactions
    if (['IMG', 'VIDEO', 'AUDIO'].includes(target.tagName)) {
      const mediaData = {
        type: target.tagName.toLowerCase(),
        src: target.src || target.currentSrc,
        timestamp: new Date().toISOString(),
        timeFromView: viewDuration
      };

      setMediaViewed(prev => [...prev, mediaData]);

      if (onEngagement) {
        onEngagement('media_interaction', mediaData);
      }
    }
  }, [isTracking, trackClicks, viewDuration, onEngagement]);

  // Start tracking when post becomes visible
  useEffect(() => {
    if (isIntersecting && !isTracking && !hasTrackedView) {
      setIsTracking(true);
      setViewStartTime(Date.now());

      // Start time tracking interval
      if (trackTimeSpent) {
        intervalRef.current = setInterval(() => {
          setViewDuration(prev => {
            const newDuration = prev + 1000;
            return newDuration;
          });
        }, 1000);
      }
    } else if (!isIntersecting && isTracking) {
      // Post is no longer visible - finalize tracking
      finalizeTracking();
    }
  }, [isIntersecting, isTracking, hasTrackedView, trackTimeSpent]);

  // Add event listeners
  useEffect(() => {
    const element = postElement || elementToUse.current;
    if (isTracking && element) {
      if (trackScrollDepth) {
        window.addEventListener('scroll', handleScroll, { passive: true });
      }

      if (trackClicks) {
        element.addEventListener('click', handleClick);
      }
    }

    return () => {
      if (trackScrollDepth) {
        window.removeEventListener('scroll', handleScroll);
      }

      if (trackClicks && element) {
        element.removeEventListener('click', handleClick);
      }

      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [isTracking, postElement, elementToUse, trackScrollDepth, trackClicks, handleScroll, handleClick]);

  // Finalize tracking and send data
  const finalizeTracking = useCallback(async () => {
    if (!isTracking || hasTrackedView) return;

    // Only track if minimum view time is met
    if (viewDuration < minViewTime) {
      setIsTracking(false);
      return;
    }

    try {
      const trackingData = {
        viewDuration: Math.floor(viewDuration / 1000), // Convert to seconds
        scrollPercentage: maxScrollPercentage,
        source,
        clickedLinks,
        mediaViewed,
        // Additional context
        extraData: {
          viewport_width: window.innerWidth,
          viewport_height: window.innerHeight,
          referrer: document.referrer,
          user_agent: navigator.userAgent,
        }
      };

      const result = await analyticsAPI.trackPostView(postId, trackingData);

      if (result && onViewTracked) {
        onViewTracked(result);
      }

      setHasTrackedView(true);
    } catch (error) {
      console.error('Failed to track post view:', error);
    } finally {
      setIsTracking(false);

      // Clean up interval
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, [
    isTracking, hasTrackedView, viewDuration, minViewTime, maxScrollPercentage,
    source, clickedLinks, mediaViewed, postId, onViewTracked
  ]);

  // Clean up on unmount or when post changes
  useEffect(() => {
    return () => {
      if (isTracking && !hasTrackedView) {
        finalizeTracking();
      }

      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }

      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  // Auto-finalize on page unload
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (isTracking && !hasTrackedView) {
        // Use sendBeacon for reliable tracking on page unload
        if (navigator.sendBeacon && viewDuration >= minViewTime) {
          const data = JSON.stringify({
            post_id: postId,
            view_duration_seconds: Math.floor(viewDuration / 1000),
            scroll_percentage: maxScrollPercentage,
            source,
            clicked_links: clickedLinks,
            media_viewed: mediaViewed,
          });

          navigator.sendBeacon('/api/analytics/postsee/track-view/', data);
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [isTracking, hasTrackedView, viewDuration, minViewTime, maxScrollPercentage,
      postId, source, clickedLinks, mediaViewed]);

  // If children are provided, render them in a container with the ref
  if (children) {
    return (
      <div
        ref={elementToUse}
        className={className}
        {...props}
      >
        {children}
      </div>
    );
  }

  // Otherwise, this component doesn't render anything visible
  return null;
});

// Add display name for debugging
PostViewTracker.displayName = 'PostViewTracker';

export default PostViewTracker;
