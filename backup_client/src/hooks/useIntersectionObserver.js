/**
 * useIntersectionObserver Hook
 * A reusable hook for tracking element visibility using the Intersection Observer API
 */

import { useEffect, useRef } from 'react';

/**
 * Custom hook for intersection observer
 * @param {Function} callback - Function to call when intersection changes
 * @param {Object} options - Intersection observer options
 * @returns {React.RefObject} Ref to attach to the target element
 */
export const useIntersectionObserver = (callback, options = {}) => {
  const targetRef = useRef(null);
  const observerRef = useRef(null);

  useEffect(() => {
    const element = targetRef.current;
    if (!element) return;

    const defaultOptions = {
      threshold: 0.1,
      rootMargin: '0px',
      ...options
    };

    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        callback(entry.isIntersecting, entry);
      },
      defaultOptions
    );

    observerRef.current.observe(element);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [callback, options]);

  return targetRef;
};

/**
 * Hook variant that accepts an external ref
 * @param {React.RefObject} ref - External ref to observe
 * @param {Function} callback - Function to call when intersection changes
 * @param {Object} options - Intersection observer options
 */
export const useIntersectionObserverWithRef = (ref, callback, options = {}) => {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const defaultOptions = {
      threshold: 0.1,
      rootMargin: '0px',
      ...options
    };

    const observer = new IntersectionObserver(
      ([entry]) => {
        callback(entry.isIntersecting, entry);
      },
      defaultOptions
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [ref, callback, options]);
};

export default useIntersectionObserver;
