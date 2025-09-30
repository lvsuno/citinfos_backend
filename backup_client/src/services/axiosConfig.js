/**
 * Axios configuration with JWT and session management
 * Uses JWTAuthService for consistent token management
 */

import axios from 'axios';
import jwtAuthService from './jwtAuthService.jsx';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  withCredentials: true,
  timeout: 10000,
});

let isRefreshing = false;
let refreshSubscribers = [];

function addSubscriber(callback) {
  refreshSubscribers.push(callback);
}

function onTokenRefreshed(token) {
  refreshSubscribers.forEach(callback => callback(token));
  refreshSubscribers = [];
}

// Use JWTAuthService functions for token management
function getAccessToken() {
  return jwtAuthService.getAccessToken();
}

function getRefreshToken() {
  return jwtAuthService.getRefreshToken();
}

function setTokens(accessToken, refreshToken) {
  return jwtAuthService.setTokens(accessToken, refreshToken);
}

function clearTokens() {
  return jwtAuthService.clearTokens();
}

async function refreshAccessToken() {
  try {
    // Use JWTAuthService's refresh method
    return await jwtAuthService.refreshAccessToken();
  } catch (error) {
    clearTokens();
    throw error;
  }
}

api.interceptors.request.use(
  async (config) => {
    // Check if token needs smart renewal before making the request
    try {
      await jwtAuthService.smartRenewTokenIfNeeded();
    } catch (error) {
      console.warn('Token smart renewal failed:', error);
    }

    // Add JWT token if available
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add session ID for hybrid authentication
    const sessionId = getSessionId();
    if (sessionId) config.headers['X-Session-ID'] = sessionId;

    // Add CSRF token for state-changing operations
    const method = (config.method || '').toLowerCase();
    if (['post', 'put', 'delete', 'patch'].includes(method)) {
      const csrfToken = await getCSRFToken();
      if (csrfToken) config.headers['X-CSRFToken'] = csrfToken;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error?.response?.status;
    const errorData = error?.response?.data || {};
    const code = errorData?.code;
    const reqUrl = (error?.config?.url || '').toString();
    const path = typeof window !== 'undefined' ? (window.location?.pathname || '') : '';
    const isAuthPage = ['/login', '/register', '/verify', '/'].includes(path);
    const isSessionProbe = reqUrl.includes('/auth/me');

    // Handle JWT token refresh for 401 errors
    if (status === 401 && !originalRequest._retry && getRefreshToken()) {
      if (isRefreshing) {
        // If already refreshing, wait for the new token
        return new Promise((resolve) => {
          addSubscriber((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await refreshAccessToken();
        isRefreshing = false;
        onTokenRefreshed(newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        clearTokens();

        // Only redirect if not on auth pages and not a probe request
        if (!isAuthPage && !isSessionProbe) {
          window.dispatchEvent(
            new CustomEvent('sessionExpired', { detail: { redirect: '/login' } })
          );
          setTimeout(() => {
            window.location.href = '/login';
          }, 100);
        }
        return Promise.reject(refreshError);
      }
    }

    // Handle session-based authentication errors
    if (status === 401 && code === 'SESSION_INVALID') {
      // Avoid redirect loops on auth pages and for the session probe call
      if (!isAuthPage && !isSessionProbe) {
        window.dispatchEvent(
          new CustomEvent('sessionExpired', { detail: { redirect: errorData.redirect || '/login' } })
        );
        setTimeout(() => {
          window.location.href = errorData.redirect || '/login';
        }, 100);
      }
    }

    return Promise.reject(error);
  }
);

function getSessionId() {
  // Use JWTAuthService to get session ID from token
  return jwtAuthService.getSessionId();
}

async function getCSRFToken() {
  try {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') return value;
    }
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
    const response = await fetch(`${baseURL}/auth/csrf/`, { method: 'GET', credentials: 'include' });
    if (response.ok) {
      const data = await response.json();
      return data.csrfToken || data.csrf || null;
    }
  } catch (error) {
    console.error('Failed to get CSRF token:', error);
  }
  return null;
}

// Export token management functions
export { getAccessToken, getRefreshToken, setTokens, clearTokens };
export default api;
