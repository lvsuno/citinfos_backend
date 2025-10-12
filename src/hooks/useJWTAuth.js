import React, { useState, useEffect, createContext, useContext } from 'react';
import PropTypes from 'prop-types';
import apiService from '../services/apiService';
import { notificationWebSocket } from '../services/notificationWebSocket';

// Create Auth Context
const JWTAuthContext = createContext(null);

export const JWTAuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Initialize auth on mount
  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true);
      try {
        // Check if user is authenticated
        if (apiService.isAuthenticated()) {
          const userData = await apiService.getCurrentUser();
          if (userData) {
            setUser(userData);
            setIsAuthenticated(true);

            // Note: WebSocket connection is now handled by NotificationContext
            console.log('✅ User authenticated via JWT, WebSocket will be handled by NotificationContext');
          } else {
            setUser(null);
            setIsAuthenticated(false);
          }
        } else {
          setUser(null);
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Auth initialization error:', error);

        // Don't treat 401 as error - just means not authenticated
        if (error.response?.status === 401) {
          console.log('👤 User not authenticated (401) - this is normal for logged out users');
        }

        setUser(null);
        setIsAuthenticated(false);

        // Only clear tokens if it's not a 401 (unauthorized) error
        if (error.response?.status !== 401) {
          apiService.clearTokens();
        }
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();

    // Listen for session expired events
    const handleSessionExpired = (event) => {
      const { reason } = event.detail || {};
      setUser(null);
      setIsAuthenticated(false);
      apiService.clearTokens();
    };

    window.addEventListener('sessionExpired', handleSessionExpired);

    return () => {
      window.removeEventListener('sessionExpired', handleSessionExpired);
    };
  }, []);

  const login = async (username, password, rememberMe = false) => {
    setIsLoading(true);
    try {
      const result = await apiService.login(username, password, rememberMe);

      // After successful login, fetch complete user data
      const completeUserData = await apiService.getCurrentUser();
      setUser(completeUserData);
      setIsAuthenticated(true);

      // Note: WebSocket connection is now handled by NotificationContext
      console.log('✅ Login successful, WebSocket will be handled by NotificationContext');

      return {
        success: true,
        user: completeUserData,
        ...result // Include verification_required and other fields
      };
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData) => {
    setIsLoading(true);
    try {
      const result = await apiService.register(userData);

      // Registration no longer includes automatic authentication
      // User stays logged out and needs to login separately
      setUser(null);
      setIsAuthenticated(false);

      return result;
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      // Disconnect WebSocket before logging out
      notificationWebSocket.disconnect();
      console.log('📡 WebSocket disconnected on logout');

      await apiService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
    if (apiService.isAuthenticated()) {
      try {
        const userData = await apiService.getCurrentUser();
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('User refresh error:', error);
        await logout();
      }
    }
  };

  // Email verification methods (don't require authentication)
  const verifyEmail = async (email, code) => {
    try {
      const result = await apiService.verifyEmail(email, code);
      // After successful verification, refresh user data if authenticated
      if (apiService.isAuthenticated()) {
        await refreshUser();
      }
      return result;
    } catch (error) {
      throw error;
    }
  };

  const resendVerificationCode = async (email) => {
    try {
      return await apiService.resendVerificationCode(email);
    } catch (error) {
      throw error;
    }
  };

  const value = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUser,
    verifyEmail,
    resendVerificationCode,
    // Expose the API instance for other services
    api: apiService.api, // Access the axios instance directly
  };

  return React.createElement(JWTAuthContext.Provider, { value }, children);
};

JWTAuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

// Hook to use JWT auth context
export const useJWTAuth = () => {
  const context = useContext(JWTAuthContext);
  if (!context) {
    throw new Error('useJWTAuth must be used within a JWTAuthProvider');
  }
  return context;
};

export default useJWTAuth;
