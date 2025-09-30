/**
 * JWT Authentication Service for React Frontend
 *
 * This service handles JWT token management, API requests, and authentication.
 * It provides both JWT and session-based authentication support for hybrid authentication.
 */

import axios from 'axios';
import { useState, useEffect, createContext, useContext } from 'react';
import PropTypes from 'prop-types';
import { tokenManager } from '../utils/tokenManager';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

class JWTAuthService {
  api = null;
  isRefreshing = false;
  refreshSubscribers = [];

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Listen for centralized token updates
    this.tokenManagerUnsubscribe = tokenManager.addListener((event) => {
      if (event.event === 'token_updated') {
        // Update axios default header immediately when token changes from any source
        this.api.defaults.headers.common['Authorization'] = `Bearer ${event.token}`;
        console.log(`🔄 Axios headers updated from token manager (${event.source})`);
      } else if (event.event === 'token_cleared') {
        // Clear authorization header when token is cleared
        delete this.api.defaults.headers.common['Authorization'];
      }
    });

    // Add request interceptor to include JWT token and session ID
    this.api.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add session ID for hybrid authentication
        const sessionId = this.getSessionId();
        if (sessionId) {
          config.headers['X-Session-ID'] = sessionId;
        }

        // Debug: Log authentication headers being sent
        console.log('🔐 Auth headers:', {
          hasToken: !!token,
          hasSessionId: !!sessionId,
          sessionId: sessionId,
          url: config.url,
          method: config.method
        });

        // Handle FormData properly - remove Content-Type header to let axios set it automatically
        if (config.data instanceof FormData) {
          delete config.headers['Content-Type'];
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for token refresh and smart renewal
    this.api.interceptors.response.use(
      async (response) => {
        // Check if server sent new tokens in response headers
        const newAccessToken = response.headers['x-new-access-token'];
        const newRefreshToken = response.headers['x-new-refresh-token'];

        if (newAccessToken) {
          console.log('🔄 Server provided new JWT token in response headers');
          if (newRefreshToken) {
            this.setTokens(newAccessToken, newRefreshToken);
          } else {
            this.setToken(newAccessToken);
          }
        }

        // Check if server indicates JWT renewal is needed
        const renewalNeeded = response.headers['x-jwt-renewal-needed'];
        if (renewalNeeded === 'true') {
          console.log('⚠️ Server indicates JWT renewal needed - tokens will be renewed automatically');
          // The server middleware will handle renewal on subsequent requests
        }

        // Check if session was extended
        const sessionExtended = response.headers['x-session-extended'];
        if (sessionExtended === 'true') {
          console.log('📅 Session was extended by server');
        }

        return response;
      },
      async (error) => {
        // Handle 401 errors - server has already tried token renewal
        if (error.response?.status === 401) {
          console.log('🚪 401 Unauthorized - Session invalid or expired');

          // Server middleware already attempted token renewal
          // 401 means session is truly expired/invalid or user issues
          this.clearTokens();

          window.dispatchEvent(new CustomEvent('sessionExpired', {
            detail: {
              reason: 'session_expired',
              message: error.response?.data?.detail || 'Session expired'
            }
          }));

          return Promise.reject(error);
        }

        return Promise.reject(error);
      }
    );
  }

  // Authentication Methods
  async login(username, password, rememberMe = false) {
    try {
      const response = await this.api.post('/auth/login-with-verification-check/', {
        username,
        password,
        remember_me: rememberMe,
      });

      if (response.data.access && response.data.refresh) {
        this.setTokens(response.data.access, response.data.refresh);
        return {
          success: true,
          user: response.data.user,
          tokens: {
            access: response.data.access,
            refresh: response.data.refresh,
          },
        };
      }

      throw new Error('Invalid response format');
    } catch (error) {
      console.error('Login error:', error);
      throw this.handleError(error);
    }
  }

  async register(userData) {
    try {
      const response = await this.api.post('/auth/register/', userData);

      if (response.data.access && response.data.refresh) {
        this.setTokens(response.data.access, response.data.refresh);
        return {
          success: true,
          user: response.data.user,
          tokens: {
            access: response.data.access,
            refresh: response.data.refresh,
          },
        };
      }

      return {
        success: true,
        user: response.data.user,
        message: response.data.message || 'Registration successful',
      };
    } catch (error) {
      console.error('Registration error:', error);
      throw this.handleError(error);
    }
  }

  async logout() {
    try {
      const refreshToken = this.getRefreshToken();
      if (refreshToken) {
        await this.api.post('/auth/logout/', {
          refresh: refreshToken,
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearTokens();
    }
  }

  async refreshAccessToken() {
    if (this.isRefreshing) {
      return new Promise((resolve) => {
        this.refreshSubscribers.push((token) => resolve(token));
      });
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    this.isRefreshing = true;

    try {
      const response = await this.api.post('/auth/refresh/', {
        refresh: refreshToken,
      });

      const { access, refresh: newRefresh } = response.data;
      this.setTokens(access, newRefresh);
      this.onTokenRefreshed(access);

      return access;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.clearTokens();
      throw error;
    } finally {
      this.isRefreshing = false;
    }
  }

  async verifyToken(token = null) {
    try {
      const tokenToVerify = token || this.getAccessToken();
      if (!tokenToVerify) {
        throw new Error('No token to verify');
      }

      const response = await this.api.post('/auth/verify/', {
        token: tokenToVerify,
      });

      return response.data;
    } catch (error) {
      console.error('Token verification failed:', error);
      throw this.handleError(error);
    }
  }

  // Token Management
  setTokens(accessToken, refreshToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);

    // Use centralized token manager to notify all components
    tokenManager.updateToken(accessToken, 'login/register');

    // Reconnect WebSocket with new token
    this.reconnectWebSocket();
  }

  /**
   * Set only the access token (used when WebSocket renews JWT)
   * @param {string} accessToken - New access token
   */
  setToken(accessToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);

    // Use centralized token manager to notify all components
    tokenManager.updateToken(accessToken, 'websocket_renewal');

    // Reconnect WebSocket with new token
    this.reconnectWebSocket();
  }

  /**
   * Reconnect WebSocket when JWT token is renewed
   */
  reconnectWebSocket() {
    // Import here to avoid circular dependency
    import('./notificationWebSocket.js').then(({ default: notificationWebSocket }) => {
      if (notificationWebSocket.ws || notificationWebSocket.isConnected) {
        console.log('🔄 Reconnecting WebSocket with new JWT token...');
        notificationWebSocket.reconnectWithNewToken();
      }
    }).catch(err => {
      console.warn('Could not reconnect WebSocket:', err);
    });
  }

  clearTokens() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);

    // Clear from centralized token manager
    tokenManager.clearToken();
  }

  getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  /**
   * Alias for getAccessToken for compatibility
   */
  getToken() {
    return this.getAccessToken();
  }

  onTokenRefreshed(token) {
    this.refreshSubscribers.forEach((callback) => callback(token));
    this.refreshSubscribers = [];
  }

  isTokenExpired(token = null) {
    try {
      const tokenToCheck = token || this.getAccessToken();
      if (!tokenToCheck) return true;

      const payload = JSON.parse(atob(tokenToCheck.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);

      return payload.exp < currentTime;
    } catch (error) {
      console.error('Error checking token expiration:', error);
      return true;
    }
  }

  isAuthenticated() {
    const token = this.getAccessToken();
    return token && !this.isTokenExpired(token);
  }

  async getCurrentUser() {
    try {
      const token = this.getAccessToken();

      // If we have a valid, non-expired token, use it normally
      if (token && !this.isTokenExpired(token)) {
        const response = await this.api.get('/auth/user-info/');
        return response.data;
      }

      // If no token or token is expired, make request WITHOUT Authorization header
      // to trigger fingerprint fallback authentication
      console.log('🔄 No valid JWT token, attempting fingerprint fallback authentication');
      const response = await this.api.get('/auth/user-info/', {
        headers: {
          // Explicitly don't include Authorization header
          'Content-Type': 'application/json'
        },
        // Override the request interceptor for this specific call
        transformRequest: [(data, headers) => {
          // Remove Authorization header if it was added by interceptor
          delete headers.Authorization;
          return data;
        }]
      });
      return response.data;
    } catch (error) {
      console.error('Error getting current user:', error);

      // If we have a token, try parsing it as fallback
      const token = this.getAccessToken();
      if (token && !this.isTokenExpired(token)) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          return {
            id: payload.user_id,
            username: payload.username,
            // Add other user data from token payload
          };
        } catch (parseError) {
          console.error('Error parsing user from token:', parseError);
        }
      }

      return null;
    }
  }  /**
   * Extract session ID from JWT token payload
   * @param {string} token - JWT token (optional, uses current token if not provided)
   * @returns {string|null} Session ID or null if not found
   */
  getSessionId(token = null) {
    try {
      const tokenToCheck = token || this.getAccessToken();
      if (!tokenToCheck) return null;

      const payload = JSON.parse(atob(tokenToCheck.split('.')[1]));
      return payload.sid || null;
    } catch (error) {
      console.warn('Failed to extract session ID from JWT token:', error);
      return null;
    }
  }

  /**
   * Check if JWT token should be renewed based on remaining validity.
   * Only renew when token has 1/3 (33%) or less validity remaining.
   *
   * @param {string} token - JWT token to check (optional, uses current if not provided)
   * @returns {boolean} True if token should be renewed
   */
  shouldRenewToken(token = null) {
    try {
      const tokenToCheck = token || this.getAccessToken();
      if (!tokenToCheck) return false;

      const payload = JSON.parse(atob(tokenToCheck.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      const expTime = payload.exp;
      const issuedTime = payload.iat;

      if (!expTime || !issuedTime) return false;

      // Calculate token age and total lifetime
      const tokenAge = currentTime - issuedTime;
      const totalLifetime = expTime - issuedTime;

      // Renew if token has used 2/3 or more of its lifetime
      const renewalThreshold = totalLifetime * (2/3); // 66.7%

      return tokenAge >= renewalThreshold;

    } catch (error) {
      console.warn('Failed to check token renewal status:', error);
      return false;
    }
  }

  /**
   * Intelligently refresh token only when needed (1/3 validity remaining).
   *
   * @returns {Promise<string|null>} New access token if renewed, null if no renewal needed
   */
  async smartRenewTokenIfNeeded() {
    if (!this.shouldRenewToken()) {
      return null; // No renewal needed
    }

    try {
      const newToken = await this.refreshAccessToken();
      console.log('🔄 JWT token renewed intelligently');
      return newToken;
    } catch (error) {
      console.error('Smart token renewal failed:', error);
      throw error;
    }
  }

  /**
   * Get WebSocket authentication parameters
   * @returns {object} Object with token and session_id for WebSocket auth
   */
  getWebSocketAuthParams() {
    const token = this.getAccessToken();
    const sessionId = this.getSessionId(token);

    return {
      token,
      session_id: sessionId
    };
  }

  // API Methods
  async get(endpoint, config = {}) {
    return this.api.get(endpoint, config);
  }

  async post(endpoint, data, config = {}) {
    return this.api.post(endpoint, data, config);
  }

  async put(endpoint, data, config = {}) {
    return this.api.put(endpoint, data, config);
  }

  async patch(endpoint, data, config = {}) {
    return this.api.patch(endpoint, data, config);
  }

  async delete(endpoint, config = {}) {
    return this.api.delete(endpoint, config);
  }

  // Error Handling
  handleError(error) {
    if (error.response) {
      const { status, data } = error.response;

      switch (status) {
        case 400:
          return {
            message: data.detail || data.message || 'Bad request',
            errors: data.errors || data,
            status,
          };
        case 401:
          return {
            message: data.detail || 'Authentication required',
            status,
          };
        case 403:
          return {
            message: data.detail || 'Permission denied',
            status,
          };
        case 404:
          return {
            message: data.detail || 'Resource not found',
            status,
          };
        case 500:
          return {
            message: 'Internal server error',
            status,
          };
        default:
          return {
            message: data.detail || data.message || 'An error occurred',
            status,
          };
      }
    }

    if (error.request) {
      return {
        message: 'Network error - please check your connection',
        status: 0,
      };
    }

    return {
      message: error.message || 'An unexpected error occurred',
      status: 0,
    };
  }

  // Cleanup method
  destroy() {
    if (this.tokenManagerUnsubscribe) {
      this.tokenManagerUnsubscribe();
    }
  }
}

// React Hook for JWT Authentication
export const useJWTAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Always try to get current user - this will trigger backend fingerprint fallback
        // if JWT token is missing/expired but active session exists
        const currentUser = await jwtAuthService.getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
        }
      } catch (err) {
        console.error('Auth check failed:', err);
        // Don't set error for 401 (unauthorized) as it's expected when not logged in
        if (err.response?.status !== 401) {
          setError(err.message);
        }
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (username, password) => {
    setLoading(true);
    setError(null);

    try {
      const result = await jwtAuthService.login(username, password);
      setUser(result.user);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await jwtAuthService.logout();
      setUser(null);
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setLoading(true);
    setError(null);

    try {
      const result = await jwtAuthService.register(userData);
      if (result.user && result.tokens) {
        setUser(result.user);
      }
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    user,
    loading,
    error,
    login,
    logout,
    register,
    isAuthenticated: !!user,
    clearError: () => setError(null),
  };
};

// React Context for JWT Authentication
const JWTAuthContext = createContext({
  user: null,
  loading: false,
  error: null,
  login: () => {},
  logout: () => {},
  register: () => {},
  isAuthenticated: false,
  clearError: () => {},
});

export const JWTAuthProvider = ({ children }) => {
  const auth = useJWTAuth();

  return (
    <JWTAuthContext.Provider value={auth}>
      {children}
    </JWTAuthContext.Provider>
  );
};

JWTAuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

export const useJWTAuthContext = () => {
  const context = useContext(JWTAuthContext);
  if (!context) {
    throw new Error('useJWTAuthContext must be used within a JWTAuthProvider');
  }
  return context;
};

// Export singleton service
export const jwtAuthService = new JWTAuthService();
export default jwtAuthService;