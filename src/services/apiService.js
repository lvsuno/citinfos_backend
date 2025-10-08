/**
 * API Service for React Frontend
 * Handles API requests with JWT token management and authentication
 */

import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

class ApiService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000, // Increased to 30 seconds to avoid premature timeouts
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Important: send cookies with requests
    });

    this.setupInterceptors();
  }

  setupInterceptors() {
    // Request interceptor to add JWT token
    this.api.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();

        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Handle FormData properly
        if (config.data instanceof FormData) {
          delete config.headers['Content-Type'];
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for token refresh
    this.api.interceptors.response.use(
      (response) => {
        // Check for new tokens in response headers (from middleware auto-renewal)
        const newAccessToken = response.headers['x-new-access-token'];
        const newRefreshToken = response.headers['x-new-refresh-token'];

        if (newAccessToken) {
          console.log('🔄 Middleware renewed tokens automatically');
          this.setTokens(newAccessToken, newRefreshToken);
        }

        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          const errorData = error.response?.data || {};
          const errorCode = errorData?.code;

          // Check if this is a session expiration (should redirect to login)
          if (errorCode === 'SESSION_INVALID' || errorCode === 'SESSION_EXPIRED') {
            this.clearTokens();
            window.dispatchEvent(new CustomEvent('sessionExpired', {
              detail: { reason: 'session_expired', redirect: errorData.redirect || '/login' }
            }));
            return Promise.reject(error);
          }

          // Check if middleware already renewed tokens in headers
          const newAccessToken = error.response.headers?.['x-new-access-token'];
          if (newAccessToken) {
            console.log('🔄 Middleware renewed token during error response');
            const newRefreshToken = error.response.headers?.['x-new-refresh-token'];
            this.setTokens(newAccessToken, newRefreshToken);

            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            originalRequest._retry = true;
            return this.api(originalRequest);
          }

          // If no renewal from middleware, session is invalid - redirect to login
          this.clearTokens();
          window.dispatchEvent(new CustomEvent('sessionExpired', {
            detail: { reason: 'token_refresh_failed' }
          }));
          return Promise.reject(error);
        }

        return Promise.reject(error);
      }
    );
  }

  // Token management
  getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  setTokens(accessToken, refreshToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
  }

  clearTokens() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem('currentUser');
  }

  isAuthenticated() {
    return !!this.getAccessToken();
  }

  // Authentication methods
  async login(usernameOrEmail, password, rememberMe = false) {
    try {
      const response = await this.api.post('/auth/login-with-verification-check/', {
        username_or_email: usernameOrEmail,
        password,
        remember_me: rememberMe,
      });

      const { access, refresh, user, verification_required, session } = response.data;

      // Always set tokens and user data (session is created on backend)
      if (access && refresh && user) {
        this.setTokens(access, refresh);
        localStorage.setItem('currentUser', JSON.stringify(user));

        // Check if verification is required
        if (verification_required) {
          return {
            success: true,
            user,
            tokens: { access, refresh },
            session,  // Include session data with last_visited_url
            verification_required: true,
            verification_status: response.data.verification_status,
            verification_message: response.data.verification_message,
            verification_code: response.data.verification_code,
            verification_expiry: response.data.verification_expiry,
            message: response.data.message || 'Login successful - email verification required'
          };
        }

        // No verification needed
        return {
          success: true,
          user,
          tokens: { access, refresh },
          session,  // Include session data with last_visited_url
          message: response.data.message || 'Login successful'
        };
      }

      // Fallback for unexpected response format
      return {
        success: false,
        error: 'Invalid login response format'
      };
    } catch (error) {
      console.error('Login error:', error);
      throw this.handleError(error);
    }
  }

  async register(userData) {
    try {
      const response = await this.api.post('/auth/register/', userData);

      return {
        success: true,
        message: response.data.message || 'Registration successful! Please check your email for verification.',
        user: response.data.user,
        email: userData.email
      };
    } catch (error) {
      console.error('Registration error:', error);
      throw this.handleError(error);
    }
  }

  async verifyEmail(email, code) {
    try {
      const response = await this.api.post('/auth/verify/', {
        email,
        code
      });

      const { access, refresh, user } = response.data;

      if (access && refresh) {
        this.setTokens(access, refresh);
        localStorage.setItem('currentUser', JSON.stringify(user));
      }

      return {
        success: true,
        message: response.data.message || 'Email verified successfully!',
        user,
        tokens: access ? { access, refresh } : null
      };
    } catch (error) {
      console.error('Email verification error:', error);
      throw this.handleError(error);
    }
  }

  async resendVerificationCode(email) {
    try {
      const response = await this.api.post('/auth/resend-code/', {
        email
      });

      return {
        success: true,
        message: response.data.message || 'Verification code sent!'
      };
    } catch (error) {
      console.error('Resend verification error:', error);
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

  async getCurrentUser() {
    try {
      const response = await this.api.get('/auth/user-info/');
      return response.data;
    } catch (error) {
      console.error('Get current user error:', error);
      throw this.handleError(error);
    }
  }

  async updateLastVisitedUrl(url) {
    try {
      const response = await this.api.post('/auth/update-last-visited/', { url });
      return response.data;
    } catch (error) {
      console.error('Update last visited URL error:', error);
      // Don't throw - this is not critical
      return null;
    }
  }

  // Generic HTTP methods
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

  // Error handling
  handleError(error) {
    if (error.response) {
      const { status, data } = error.response;

      switch (status) {
        case 400:
          return new Error(data.message || data.error || 'Invalid request');
        case 401:
          return new Error(data.message || 'Authentication required');
        case 403:
          return new Error(data.message || 'Access denied');
        case 404:
          return new Error(data.message || 'Resource not found');
        case 500:
          return new Error('Server error. Please try again later.');
        default:
          return new Error(data.message || data.error || 'An error occurred');
      }
    } else if (error.request) {
      return new Error('Network error. Please check your connection.');
    } else {
      return new Error(error.message || 'An unexpected error occurred');
    }
  }
}

// Create singleton instance
export const apiService = new ApiService();
export default apiService;