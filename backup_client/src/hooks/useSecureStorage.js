/**
 * Secure Storage Hook
 *
 * This hook provides secure storage methods that avoid exposing sensitive data
 */

import { useEffect } from 'react';

export const useSecureStorage = () => {

  // Clear sensitive data on app close/refresh
  useEffect(() => {
    const clearSensitiveData = () => {
      // Clear any sensitive data from localStorage
      const sensitiveKeys = ['temp_password', 'user_password', 'login_data'];
      sensitiveKeys.forEach(key => {
        localStorage.removeItem(key);
        sessionStorage.removeItem(key);
      });
    };

    // Clear on page unload
    window.addEventListener('beforeunload', clearSensitiveData);

    // Clear on visibility change (when user switches tabs)
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        clearSensitiveData();
      }
    });

    return () => {
      window.removeEventListener('beforeunload', clearSensitiveData);
      document.removeEventListener('visibilitychange', clearSensitiveData);
      clearSensitiveData();
    };
  }, []);

  /**
   * Store non-sensitive data only
   * @param {string} key - Storage key
   * @param {any} value - Value to store (should not contain passwords)
   */
  const setSecureItem = (key, value) => {
    // Never store passwords or sensitive credentials
    if (typeof value === 'object' && value !== null) {
      const sanitized = { ...value };
      delete sanitized.password;
      delete sanitized.Password;
      delete sanitized.credentials;
      localStorage.setItem(key, JSON.stringify(sanitized));
    } else {
      localStorage.setItem(key, value);
    }
  };

  /**
   * Get item from secure storage
   * @param {string} key - Storage key
   */
  const getSecureItem = (key) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch {
      return localStorage.getItem(key);
    }
  };

  /**
   * Remove item from storage
   * @param {string} key - Storage key
   */
  const removeSecureItem = (key) => {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  };

  return {
    setSecureItem,
    getSecureItem,
    removeSecureItem,
  };
};
