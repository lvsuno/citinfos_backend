/**
 * Hook to track page visits for smart redirect
 * Automatically updates backend session with current page
 */

import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import apiService from '../services/apiService';

// Throttle updates to avoid too many API calls
const UPDATE_THROTTLE_MS = 5000; // Only update every 5 seconds max

export const usePageTracking = (divisionData = null) => {
    const location = useLocation();
    const lastUpdateRef = useRef(0);
    const lastUrlRef = useRef('');

    useEffect(() => {
        const currentUrl = location.pathname;
        const now = Date.now();

        // Skip if URL hasn't changed or if too soon since last update
        if (currentUrl === lastUrlRef.current ||
            now - lastUpdateRef.current < UPDATE_THROTTLE_MS) {
            return;
        }

        // Skip tracking for certain pages
        const skipPages = ['/login', '/register', '/signup', '/verify-email', '/'];
        if (skipPages.includes(currentUrl)) {
            return;
        }

        // Only track if authenticated
        if (!apiService.isAuthenticated()) {
            return;
        }

        // Update last visited URL in backend session
        apiService.updateLastVisitedUrl(currentUrl)
            .then(() => {
                lastUpdateRef.current = now;
                lastUrlRef.current = currentUrl;            })
            .catch(error => {            });

    }, [location.pathname, divisionData]);
};

export default usePageTracking;
