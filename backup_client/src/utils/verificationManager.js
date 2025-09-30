// src/utils/verificationManager.js
// React/JavaScript compatible Automatic Verification Manager
// Integrates with existing VerifyAccount component and login flow

import toast from 'react-hot-toast';
import api from '../services/axiosConfig';

/**
 * React-compatible Verification Manager for automatic verification system
 * Handles login verification checks, automatic re-verification, and UI coordination
 */
export class VerificationManager {
  constructor() {
    this.isCheckingVerification = false;
    this.verificationCallbacks = new Set();
  }

  /**
   * Register a callback for verification state changes
   * @param {Function} callback - Function to call when verification status changes
   */
  onVerificationStateChange(callback) {
    this.verificationCallbacks.add(callback);
    return () => this.verificationCallbacks.delete(callback);
  }

  /**
   * Notify all registered callbacks of verification state changes
   * @param {Object} state - The new verification state
   */
  notifyVerificationStateChange(state) {
    this.verificationCallbacks.forEach(callback => {
      try {
        callback(state);
      } catch (error) {
        console.error('Verification state callback error:', error);
      }
    });
  }

  /**
   * Enhanced login with automatic verification checking
   * Integrates with your existing login flow
   * @param {string} username - Username (can be email)
   * @param {string} password - User password
   * @param {boolean} rememberMe - Whether to remember the user session
   * @returns {Object} Login result with verification status
   */
  async loginWithVerificationCheck(username, password, rememberMe = false) {
    try {
      const response = await api.post('/auth/login-with-verification-check/', {
        username,
        password,
        remember_me: rememberMe,
      });

      const result = response.data;

      // Check if login was successful (no verification issues)
      if (result.access && result.user) {
        // Successful login, store JWT tokens
        if (result.access) {
          localStorage.setItem('access_token', result.access);
        }
        if (result.refresh) {
          localStorage.setItem('refresh_token', result.refresh);
        }
        if (result.user) {
          localStorage.setItem('user', JSON.stringify(result.user));
        }

        toast.success(result.message || 'Login successful!');
        return {
          success: true,
          user: result.user,
          requiresVerification: false,
          tokens: {
            access: result.access,
            refresh: result.refresh
          }
        };

      } else {
        // This means the response is a verification error
        // The backend returns 403 status for verification issues
        throw new Error('Verification required');
      }

    } catch (error) {
      console.error('Login with verification check failed:', error);

      // Handle verification-specific errors (403 status)
      if (error.response && error.response.status === 403) {
        const errorData = error.response.data;

        if (errorData.verification_required) {
          const userEmail = errorData.user_id ?
            await this.getUserEmailFromId(errorData.user_id) :
            username; // fallback to username which might be email

          // Store pending email for verification component
          localStorage.setItem('pendingEmail', userEmail);

          // Notify components that verification is needed
          this.notifyVerificationStateChange({
            requiresVerification: true,
            userEmail: userEmail,
            message: errorData.error || errorData.message,
            type: errorData.status === 'expired' ? 'expired' : 'not_verified',
            userId: errorData.user_id
          });

          toast.error(errorData.error || 'Verification required. Please check your email.');

          return {
            success: false,
            requiresVerification: true,
            userEmail: userEmail,
            message: errorData.error || errorData.message,
            type: errorData.status === 'expired' ? 'expired' : 'not_verified',
            userId: errorData.user_id
          };
        }
      }

      // Handle other errors
      const errorMessage = error.response?.data?.error ||
                          error.response?.data?.message ||
                          error.message ||
                          'Login failed. Please try again.';
      toast.error(errorMessage);
      return { success: false, requiresVerification: false, message: errorMessage };
    }
  }

  /**
   * Helper method to get user email from user ID
   * @param {string} userId - User ID
   * @returns {string} User email
   */
  async getUserEmailFromId(userId) {
    try {
      // Try to get user email from stored user data first
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        const user = JSON.parse(storedUser);
        if (user.email) return user.email;
      }

      // If we can't get it from storage, return empty string
      // The backend should ideally return the email in the error response
      return '';
    } catch (error) {
      console.error('Failed to get user email:', error);
      return '';
    }
  }

  /**
   * Resend verification code using the new API
   * @param {string} email - User email
   * @returns {boolean} Success status
   */
  async resendVerificationCode(email) {
    try {
      const response = await api.post('/auth/resend-code/', {
        email
      });

      toast.success(response.data.message || 'Verification code sent!');
      return true;

    } catch (error) {
      console.error('Resend verification code failed:', error);
      const errorMessage = error.response?.data?.message || 'Failed to resend verification code.';
      toast.error(errorMessage);
      return false;
    }
  }

  /**
   * Verify registration code using the correct registration verification endpoint
   * @param {string} userId - User ID from registration
   * @param {string} code - Verification code
   * @param {Object} options - Additional options for UI handling
   * @returns {Object} Verification result
   */
  async verifyRegistrationCode(userId, code, options = {}) {
    try {
      const response = await api.post('/auth/verify/', {
        user_id: userId,
        code
      });

      const result = response.data;

      if (result.success) {
        // Show success notification (green toast)
        toast.success(result.message || 'Registration verified successfully!', {
          duration: 4000,
          icon: '✅',
          style: {
            background: '#10B981',
            color: '#fff',
          },
        });

        // Notify components of successful verification
        this.notifyVerificationStateChange({
          requiresVerification: false,
          verified: true,
          success: true,
          shouldCloseModal: true, // Signal to close verification modal/window
          message: result.message || 'Registration verified successfully!'
        });

        // Clear pending verification data
        localStorage.removeItem('pendingEmail');
        localStorage.removeItem('pendingUserId');

        // Optional: Auto-redirect after successful registration verification
        if (options.redirectUrl) {
          setTimeout(() => {
            window.location.href = options.redirectUrl;
          }, 2000); // 2 second delay to show success message
        }

        return {
          success: true,
          message: result.message,
          shouldCloseModal: true,
          verified: true
        };

      } else {
        toast.error(result.message || 'Invalid verification code.');
        return { success: false, message: result.message };
      }

    } catch (error) {
      console.error('Registration verification failed:', error);
      const errorMessage = error.response?.data?.message || 'Verification failed. Please try again.';
      toast.error(errorMessage);
      return { success: false, message: errorMessage };
    }
  }

  /**
   * Verify code and complete login using the new API
   * @param {string} email - User email
   * @param {string} code - Verification code
   * @param {Object} options - Additional options for UI handling
   * @returns {Object} Verification result
   */
  async verifyCodeAndLogin(email, code, options = {}) {
    try {
      const response = await api.post('/auth/verify/', {
        email,
        code
      });

      const result = response.data;

      if (result.success) {
        // Store authentication tokens
        if (result.access_token) {
          localStorage.setItem('access_token', result.access_token);
        }
        if (result.refresh_token) {
          localStorage.setItem('refresh_token', result.refresh_token);
        }
        if (result.user) {
          localStorage.setItem('user', JSON.stringify(result.user));
        }

        // Clear pending email
        localStorage.removeItem('pendingEmail');

        // Show success notification (green toast)
        toast.success(result.message || 'Verification successful! Welcome back!', {
          duration: 4000,
          icon: '🎉',
          style: {
            background: '#10B981',
            color: '#fff',
          },
        });

        // Notify successful verification with modal close signal
        this.notifyVerificationStateChange({
          requiresVerification: false,
          verified: true,
          success: true,
          shouldCloseModal: true, // Signal to close verification modal/window
          user: result.user,
          loggedIn: true,
          message: result.message || 'Verification successful!'
        });

        // Optional: Auto-redirect after successful login verification
        if (options.redirectUrl) {
          setTimeout(() => {
            window.location.href = options.redirectUrl;
          }, 1500); // 1.5 second delay to show success message
        }

        return {
          success: true,
          user: result.user,
          message: result.message,
          shouldCloseModal: true,
          verified: true,
          loggedIn: true
        };

      } else {
        toast.error(result.message || 'Invalid verification code.');
        return { success: false, message: result.message };
      }

    } catch (error) {
      console.error('Verification failed:', error);
      const errorMessage = error.response?.data?.message || 'Verification failed. Please try again.';
      toast.error(errorMessage);
      return { success: false, message: errorMessage };
    }
  }

  /**
   * Generic verification method for use in verification components
   * Handles both registration and login verification scenarios
   * @param {Object} verificationData - Verification data (code, userId/email, type)
   * @param {Object} options - UI and behavior options
   * @returns {Object} Verification result with UI signals
   */
  async verifyCode(verificationData, options = {}) {
    const { code, userId, email, type = 'registration' } = verificationData;
    const {
      onSuccess,
      onError,
      autoClose = true,
      redirectUrl,
      successMessage,
      showConfetti = false
    } = options;

    try {
      // Determine verification payload based on type
      const payload = { email, code };

      const response = await api.post('/auth/verify/', payload);
      const result = response.data;

      if (result.success) {
        // Store tokens if provided (login verification)
        if (result.access_token) {
          localStorage.setItem('access_token', result.access_token);
        }
        if (result.refresh_token) {
          localStorage.setItem('refresh_token', result.refresh_token);
        }
        if (result.user) {
          localStorage.setItem('user', JSON.stringify(result.user));
        }

        // Clear pending verification data
        localStorage.removeItem('pendingEmail');
        localStorage.removeItem('pendingUserId');

        // Show success notification with custom styling
        const message = successMessage || result.message ||
          (type === 'registration' ? 'Registration verified successfully! 🎉' : 'Verification successful! Welcome back! 🎉');

        toast.success(message, {
          duration: 4000,
          icon: showConfetti ? '🎉' : '✅',
          style: {
            background: '#10B981',
            color: '#fff',
            fontWeight: '500',
            borderRadius: '10px',
          },
        });

        // Create comprehensive success state
        const successState = {
          success: true,
          requiresVerification: false,
          verified: true,
          shouldCloseModal: autoClose,
          user: result.user,
          message: message,
          type: type,
          loggedIn: !!result.access_token, // True if tokens were provided
        };

        // Notify all listening components
        this.notifyVerificationStateChange(successState);

        // Call custom success callback if provided
        if (typeof onSuccess === 'function') {
          onSuccess(successState);
        }

        // Auto-redirect if specified
        if (redirectUrl && autoClose) {
          setTimeout(() => {
            window.location.href = redirectUrl;
          }, 2000);
        }

        // Emit custom success event for components that don't use callbacks
        window.dispatchEvent(new CustomEvent('verificationSuccess', {
          detail: successState
        }));

        return successState;

      } else {
        // Handle verification failure
        const errorMessage = result.message || 'Invalid verification code.';
        toast.error(errorMessage);

        const errorState = {
          success: false,
          message: errorMessage,
          shouldCloseModal: false
        };

        if (typeof onError === 'function') {
          onError(errorState);
        }

        return errorState;
      }

    } catch (error) {
      console.error('Verification failed:', error);
      const errorMessage = error.response?.data?.message || 'Verification failed. Please try again.';

      toast.error(errorMessage);

      const errorState = {
        success: false,
        message: errorMessage,
        shouldCloseModal: false
      };

      if (typeof onError === 'function') {
        onError(errorState);
      }

      return errorState;
    }
  }

  /**
   * Check if user's verification has expired on app load
   * Call this when your app initializes
   * @returns {Object} Verification status
   */
  async checkVerificationStatusOnLoad() {
    if (this.isCheckingVerification) {
      return { checking: true };
    }

    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      return { loggedIn: false };
    }

    this.isCheckingVerification = true;

    try {
      const response = await api.get('/auth/verification-status/', {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      const status = response.data;

      if (status.verification_expired) {
        // Auto-logout if verification expired
        this.handleExpiredVerification();
        return {
          loggedIn: false,
          expired: true,
          message: 'Your verification has expired. Please log in again.'
        };
      }

      return {
        loggedIn: true,
        expired: false,
        verificationStatus: status
      };

    } catch (error) {
      console.error('Failed to check verification status:', error);
      // If token is invalid, clear auth and redirect to login
      if (error.response?.status === 401) {
        this.clearAuthAndRedirect();
      }
      return { loggedIn: false, error: true };
    } finally {
      this.isCheckingVerification = false;
    }
  }

  /**
   * Handle expired verification by clearing auth and redirecting
   */
  handleExpiredVerification() {
    // Clear all authentication data
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('authToken');
    localStorage.removeItem('sessionId');
    localStorage.removeItem('userType');
    localStorage.removeItem('userEmail');

    // Clear session cookie
    document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';

    // Notify components of expiry
    this.notifyVerificationStateChange({
      expired: true,
      loggedOut: true,
      message: 'Your verification has expired. Please log in again.'
    });

    toast.error('Your verification has expired. Please log in again.');
  }

  /**
   * Clear authentication data and redirect to login
   */
  clearAuthAndRedirect() {
    this.handleExpiredVerification();

    // Emit session expired event for other components
    window.dispatchEvent(new CustomEvent('sessionExpired', {
      detail: { reason: 'verification_expired' }
    }));

    // Redirect to login page
    window.location.href = '/login';
  }

  /**
   * Get current verification status for UI components
   * @returns {Object} Current verification status
   */
  async getCurrentVerificationStatus() {
    try {
      const accessToken = localStorage.getItem('access_token');
      if (!accessToken) {
        return { loggedIn: false };
      }

      const response = await api.get('/auth/verification-status/');
      return response.data;

    } catch (error) {
      console.error('Failed to get verification status:', error);
      return { error: true };
    }
  }
}

// Create singleton instance
export const verificationManager = new VerificationManager();

/**
 * React Hook for using verification manager in components
 * @returns {Object} Verification manager methods and state
 */
export const useVerificationManager = () => {
  const [verificationState, setVerificationState] = React.useState({
    requiresVerification: false,
    checking: false,
    expired: false
  });

  React.useEffect(() => {
    // Register for verification state changes
    const unsubscribe = verificationManager.onVerificationStateChange(setVerificationState);

    // Check verification status on mount
    verificationManager.checkVerificationStatusOnLoad()
      .then(status => setVerificationState(prev => ({ ...prev, ...status })));

    return unsubscribe;
  }, []);

  return {
    verificationState,
    loginWithVerificationCheck: verificationManager.loginWithVerificationCheck.bind(verificationManager),
    resendVerificationCode: verificationManager.resendVerificationCode.bind(verificationManager),
    verifyCodeAndLogin: verificationManager.verifyCodeAndLogin.bind(verificationManager),
    verifyRegistrationCode: verificationManager.verifyRegistrationCode.bind(verificationManager),
    verifyCode: verificationManager.verifyCode.bind(verificationManager), // New generic method
    checkVerificationStatus: verificationManager.getCurrentVerificationStatus.bind(verificationManager)
  };
};

// Export for direct usage
export default verificationManager;
