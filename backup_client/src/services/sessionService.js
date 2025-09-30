/**
 * Session management service for handling Redis-based sessions
 */

import api from './axiosConfig.js'; // Use configured axios instance instead of raw axios

class SessionService {
  static instance = null;
  isValidating = false;

  // Session validation URL
  VALIDATION_URL = '/api/core/session/validate/';
  REFRESH_URL = '/api/core/session/refresh/';
  CHECK_URL = '/api/core/session/check/';

  // Check interval (5 minutes)
  CHECK_INTERVAL = 5 * 60 * 1000;

  constructor() {}

  static getInstance() {
    if (!SessionService.instance) {
      SessionService.instance = new SessionService();
    }
    return SessionService.instance;
  }

  /**
   * Validate current session
   */
  async validateSession() {
    if (this.isValidating) {
      return { valid: false, error: 'Validation already in progress' };
    }

    // Skip validation on auth pages
    const currentPath = window.location.pathname;
    const authPaths = ['/login', '/register', '/forgot-password', '/verify-email', '/verify', '/'];

    if (authPaths.some(path => currentPath.startsWith(path))) {
      return { valid: false, error: 'On auth page', skipValidation: true };
    }

    this.isValidating = true;

    try {
      const response = await api.get(this.VALIDATION_URL, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      this.isValidating = false;
      return response.data;
    } catch (error) {
      this.isValidating = false;

      if (error.response && error.response.status === 401) {
        return {
          valid: false,
          error: 'Session expired',
          redirect: '/login',
        };
      }

      return {
        valid: false,
        error: 'Validation failed',
      };
    }
  }

  /**
   * Refresh current session to extend duration
   */
  async refreshSession() {
    try {
      const response = await api.post(this.REFRESH_URL, {}, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      return response.data;
    } catch (error) {
      return {
        success: false,
        error: 'Refresh failed',
      };
    }
  }

  /**
   * Check session status (lightweight check)
   */
  async checkSessionStatus() {
    try {
      const response = await api.get(this.CHECK_URL, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      return response.data;
    } catch (error) {
      return { valid: false };
    }
  }

  /**
   * Start session monitoring
   */
  startSessionMonitoring() {
    // Clear existing interval
    this.stopSessionMonitoring();

    // Start new interval
    this.sessionCheckInterval = setInterval(async () => {
      const result = await this.validateSession();

      if (!result.valid && !result.skipValidation) {
        this.handleSessionExpired(result.redirect);
      }
    }, this.CHECK_INTERVAL);

    // Also check immediately on start
    setTimeout(() => {
      this.validateSession().then(result => {
        if (!result.valid && !result.skipValidation) {
          this.handleSessionExpired(result.redirect);
        }
      });
    }, 1000);
  }

  /**
   * Stop session monitoring
   */
  stopSessionMonitoring() {
    if (this.sessionCheckInterval) {
      clearInterval(this.sessionCheckInterval);
      this.sessionCheckInterval = null;
    }
  }

  /**
   * Handle session expiration
   */
  handleSessionExpired(redirectUrl) {
    console.warn('Session expired, redirecting to login');

    // Clear any stored session data
    this.clearSessionData();

    // Emit custom event for components to listen to
    window.dispatchEvent(new CustomEvent('sessionExpired', {
      detail: { redirect: redirectUrl }
    }));

    // Redirect to login
    window.location.href = redirectUrl || '/login';
  }

  /**
   * Get session ID from cookie or localStorage
   */
  getSessionId() {
    // Try to get from cookie first
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'sessionid') {
        return value;
      }
    }

    // Fallback to localStorage
    return localStorage.getItem('sessionId');
  }

  /**
   * Clear session data
   */
  clearSessionData() {
    localStorage.removeItem('sessionId');
    localStorage.removeItem('userData');

    // Clear session cookie
    document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  }

  /**
   * Initialize session service
   */
  initialize() {
    // Start monitoring
    this.startSessionMonitoring();

    // Listen for page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        // Page became visible, check session
        this.validateSession().then(result => {
          if (!result.valid && !result.skipValidation) {
            this.handleSessionExpired(result.redirect);
          }
        });
      }
    });

    // Listen for focus events
    window.addEventListener('focus', () => {
      this.validateSession().then(result => {
        if (!result.valid && !result.skipValidation) {
          this.handleSessionExpired(result.redirect);
        }
      });
    });
  }

  /**
   * Cleanup on app unmount
   */
  cleanup() {
    this.stopSessionMonitoring();
  }
}

export default SessionService.getInstance();
