import React, { useState, useEffect, createContext, useContext } from 'react';
import PropTypes from 'prop-types';
import api from '../services/axiosConfig';

// Absolute API base from env (used only for fetch fallbacks like CSRF)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Simple session API calls
const sessionAPI = {
  // Get CSRF token from cookie or endpoint
  async getCSRFToken() {
    // Try cookie first
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') return value;
    }
    // Fallback to API (absolute URL)
    try {
      const res = await fetch(`${API_BASE_URL}/auth/csrf/`, { method: 'GET', credentials: 'include' });
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        return data.csrfToken || data.csrf || null;
      }
    } catch (_) {}
    return null;
  },

  async validateSession() {
    try {
      const response = await api.get('/auth/me/');

      const data = response.data || {};
      const user = data?.user ?? (Object.keys(data || {}).length ? data : null);
      return { isValid: !!user, user: user || null };
    } catch (error) {
      if (error?.response && (error.response.status === 401 || error.response.status === 403)) {
        return { isValid: false, user: null };
      }
      console.warn('Session validation warning:', error?.message || error);
      return { isValid: false, user: null };
    }
  },

  async login(username, password) {
    try {
      const response = await api.post('/auth/login/', { username, password });
      const data = response.data || {};
      return { success: true, user: data.user };
    } catch (error) {
      const message = error?.response?.data?.message || error?.response?.data?.detail || 'Login failed';
      console.error('Login error:', message);
      throw new Error(message);
    }
  },

  async logout() {
    try {
      await api.post('/auth/logout/');
      return { success: true };
    } catch (error) {
      const message = error?.response?.data?.message || error?.response?.data?.detail || 'Logout failed';
      console.error('Logout error:', message);
      throw new Error(message);
    }
  },
};

// Create Session Context
const SessionContext = createContext(null);

export const SessionProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isValid, setIsValid] = useState(false);

  // Validate session on mount
  useEffect(() => {
    const validateSession = async () => {
      setIsLoading(true);
      try {
        const result = await sessionAPI.validateSession();
        setIsValid(result.isValid);
        setUser(result.user);
      } catch (error) {
        console.error('Session validation error:', error);
        setIsValid(false);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    validateSession();
  }, []);

  const login = async (username, password) => {
    try {
      const result = await sessionAPI.login(username, password);
      setUser(result.user);
      setIsValid(true);
      return result;
    } catch (error) {
      setUser(null);
      setIsValid(false);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await sessionAPI.logout();
      setUser(null);
      setIsValid(false);
    } catch (error) {
      // Even if logout fails, clear local state
      setUser(null);
      setIsValid(false);
      throw error;
    }
  };

  // Refresh session data from server (used after login or on demand)
  const refreshSession = async (force = false) => {
    setIsLoading(true);
    try {
      const result = await sessionAPI.validateSession();
      setIsValid(result.isValid);
      setUser(result.user);
      return result;
    } finally {
      setIsLoading(false);
    }
  };

  const value = {
    user,
    isLoading,
    isValid,
    login,
    logout,
    refreshSession,
  };

  return React.createElement(SessionContext.Provider, { value }, children);
};

SessionProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

// Hook to use session context
export const useSimpleSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSimpleSession must be used within a SessionProvider');
  }
  return context;
};

export default useSimpleSession;
