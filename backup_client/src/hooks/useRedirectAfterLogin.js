import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

/**
 * Custom hook for handling redirect after login functionality
 */
export const useRedirectAfterLogin = () => {
  const location = useLocation();
  const navigate = useNavigate();

  /**
   * Store the current location for redirect after login
   * @param {string} path - Optional custom path to store (defaults to current location)
   */
  const storeRedirectLocation = (path = null) => {
    const redirectTo = path || (location.pathname + location.search + location.hash);

    // Don't store redirect for login/register pages to avoid loops
    if (!['/login', '/register', '/verify'].includes(location.pathname)) {
      localStorage.setItem('redirectAfterLogin', redirectTo);
      console.log('Stored redirect location:', redirectTo);
    }
  };

  /**
   * Navigate to the stored redirect location or default page
   * @param {string} defaultPath - Default path if no redirect is stored
   */
  const navigateToStoredLocation = (defaultPath = '/dashboard') => {
    const redirectTo = localStorage.getItem('redirectAfterLogin');

    if (redirectTo) {
      localStorage.removeItem('redirectAfterLogin'); // Clean up
      console.log('Redirecting to stored location:', redirectTo);
      navigate(redirectTo, { replace: true });
    } else {
      console.log('No stored location, redirecting to default:', defaultPath);
      navigate(defaultPath, { replace: true });
    }
  };

  /**
   * Get the stored redirect location without consuming it
   */
  const getStoredLocation = () => {
    return localStorage.getItem('redirectAfterLogin');
  };

  /**
   * Clear the stored redirect location
   */
  const clearStoredLocation = () => {
    localStorage.removeItem('redirectAfterLogin');
  };

  /**
   * Get a human-readable page name from a path
   */
  const getPageNameFromPath = (path) => {
    if (!path) return null;

    const pathMap = {
      '/dashboard': 'Dashboard',
      '/notifications': 'Notifications',
      '/communities': 'Communities',
      '/polls': 'Polls',
      '/equipment': 'Equipment',
      '/equipment2': 'Equipment (V2)',
      '/profile': 'Profile',
      '/homes': 'Homes',
      '/ai-conversations': 'AI Conversations',
      '/badges': 'Badges',
      '/chat': 'Private Chat',
      '/ab-testing': 'A/B Testing',
      '/search': 'Search Results'
    };

    // Handle dynamic routes
    if (path.startsWith('/notifications/')) return 'Notification Details';
    if (path.startsWith('/c/')) return 'Community Details';
    if (path.startsWith('/polls/')) {
      if (path.includes('/create')) return 'Create Poll';
      return 'Poll Details';
    }
    if (path.startsWith('/users/') || path.startsWith('/user/')) return 'User Profile';
    if (path.startsWith('/moderator-nomination')) return 'Moderator Nomination';

    // Extract path from query parameters
    const basePath = path.split('?')[0];
    return pathMap[basePath] || basePath.replace('/', '').split('/').map(
      segment => segment.charAt(0).toUpperCase() + segment.slice(1)
    ).join(' ') || 'Page';
  };

  /**
   * Check if there's a pending redirect
   */
  const hasPendingRedirect = () => {
    return !!localStorage.getItem('redirectAfterLogin');
  };

  /**
   * Get redirect information for display
   */
  const getRedirectInfo = () => {
    const redirectTo = getStoredLocation();
    if (!redirectTo) return null;

    return {
      path: redirectTo,
      pageName: getPageNameFromPath(redirectTo),
      displayText: `Continue to ${getPageNameFromPath(redirectTo)}`
    };
  };

  // Auto-cleanup on component unmount or location change to login
  useEffect(() => {
    // If user navigated directly to login, register, or verify pages,
    // and there's no proper referrer, clear stale redirects
    if (['/login', '/register', '/verify'].includes(location.pathname)) {
      const referrer = document.referrer;
      const isExternalNavigation = !referrer || !referrer.includes(window.location.origin);

      if (isExternalNavigation) {
        // User typed URL directly or came from external source
        clearStoredLocation();
      }
    }
  }, [location.pathname]);

  return {
    storeRedirectLocation,
    navigateToStoredLocation,
    getStoredLocation,
    clearStoredLocation,
    getPageNameFromPath,
    hasPendingRedirect,
    getRedirectInfo
  };
};

export default useRedirectAfterLogin;
