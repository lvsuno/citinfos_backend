import React, { useState, useEffect, createContext, useContext } from 'react';
import PropTypes from 'prop-types';
import authService from '../services/authService';

// Create Auth Context
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Validate session on mount
  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true);
      try {
        if (authService.isAuthenticated()) {
          const result = await authService.validateSession();
          setIsAuthenticated(result.isValid);
          setUser(result.user);
        } else {
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        setIsAuthenticated(false);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();

    // Listen for session expired events
    const handleSessionExpired = () => {
      setIsAuthenticated(false);
      setUser(null);
    };

    window.addEventListener('sessionExpired', handleSessionExpired);

    return () => {
      window.removeEventListener('sessionExpired', handleSessionExpired);
    };
  }, []);

  const login = async (username, password) => {
    setIsLoading(true);
    try {
      const result = await authService.login(username, password);
      if (result.success) {
        setUser(result.user);
        setIsAuthenticated(true);
      }
      return result;
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithVerificationCheck = async (username, password) => {
    setIsLoading(true);
    try {
      const result = await authService.loginWithVerificationCheck(username, password);
      if (result.success) {
        setUser(result.user);
        setIsAuthenticated(true);
      }
      return result;
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
      const result = await authService.register(userData);
      if (result.success && result.user) {
        setUser(result.user);
        setIsAuthenticated(true);
      }
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
      await authService.logout();
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      // Even if logout fails, clear local state
      setUser(null);
      setIsAuthenticated(false);
      console.error('Logout error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
    if (authService.isAuthenticated()) {
      try {
        const result = await authService.getCurrentUser();
        if (result.success) {
          setUser(result.user);
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('User refresh error:', error);
        await logout();
      }
    }
  };

  const verifyEmail = async (email, code) => {
    try {
      const result = await authService.verifyEmail(email, code);
      if (result.success) {
        // Refresh user data after verification
        await refreshUser();
      }
      return result;
    } catch (error) {
      throw error;
    }
  };

  const resendVerificationCode = async (email) => {
    try {
      return await authService.resendVerificationCode(email);
    } catch (error) {
      throw error;
    }
  };

  const value = {
    user,
    isLoading,
    isAuthenticated,
    login,
    loginWithVerificationCheck,
    register,
    logout,
    refreshUser,
    verifyEmail,
    resendVerificationCode,
    // Additional auth methods
    changePassword: authService.changePassword.bind(authService),
    requestPasswordReset: authService.requestPasswordReset.bind(authService),
    resetPassword: authService.resetPassword.bind(authService)
  };

  return React.createElement(AuthContext.Provider, { value }, children);
};

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

// Hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default useAuth;
