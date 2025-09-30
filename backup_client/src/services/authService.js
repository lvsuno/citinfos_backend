/**
 * Unified Authentication Service supporting both JWT and Session authentication
 *
 * This service provides a unified interface for authentication that works with
 * the backend's hybrid JWT/session authentication system.
 */

import api, { getAccessToken, getRefreshToken, setTokens, clearTokens } from './axiosConfig';

// Enhanced device fingerprinting for Phase 2.3 optimization
function getClientDeviceInfo() {
  const canvas = document.createElement('canvas');
  let glVendor = '', glRenderer = '', canvasFingerprint = '';

  try {
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl && typeof WebGLRenderingContext !== 'undefined' && gl instanceof WebGLRenderingContext) {
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (debugInfo) {
        glVendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
        glRenderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
      }
    }

    // Canvas fingerprinting for better uniqueness
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillText('Device fingerprint test 🔒', 2, 2);
      canvasFingerprint = canvas.toDataURL().slice(22, 32); // Short hash
    }
  } catch (_) {}

  // Enhanced device information collection
  const deviceInfo = {
    // Basic device info (existing)
    screen_resolution: `${window.screen.width}x${window.screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    platform: navigator.platform || navigator.userAgent,
    language: navigator.language,
    languages: navigator.languages ? navigator.languages.join(',') : '',
    color_depth: window.screen.colorDepth,
    hardware_concurrency: navigator.hardwareConcurrency,
    device_memory: navigator.deviceMemory || '',
    touch_support: ('ontouchstart' in window || (navigator.maxTouchPoints && navigator.maxTouchPoints > 0)) ? '1' : '0',
    cookie_enabled: navigator.cookieEnabled ? '1' : '0',
    webgl_vendor: glVendor,
    webgl_renderer: glRenderer,
    user_agent: navigator.userAgent,

    // Enhanced fingerprinting (Phase 2.3 optimization)
    canvas_fingerprint: canvasFingerprint,
    screen_color_depth: window.screen.colorDepth,
    pixel_ratio: window.devicePixelRatio || 1,
    available_screen: `${window.screen.availWidth}x${window.screen.availHeight}`,
    inner_dimensions: `${window.innerWidth}x${window.innerHeight}`,
    outer_dimensions: `${window.outerWidth}x${window.outerHeight}`,
    battery_charging: getBatteryInfo(),
    connection_type: getConnectionInfo(),
    storage_quota: getStorageQuota(),
    local_storage: getLocalStorageInfo(),
    session_storage: getSessionStorageInfo(),
    indexed_db: getIndexedDBInfo(),
    webgl_support: glVendor ? 'available' : 'not_available',
    fonts: getFontList(),
    plugins: getPluginsInfo(),

    // Client-side generated fingerprint hash
    client_fingerprint: generateClientFingerprint({
      canvas: canvasFingerprint,
      webgl: `${glVendor}_${glRenderer}`,
      screen: `${window.screen.width}x${window.screen.height}x${window.screen.colorDepth}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: navigator.language,
      platform: navigator.platform
    })
  };

  return deviceInfo;
}

// Helper functions for enhanced fingerprinting
function getBatteryInfo() {
  if ('getBattery' in navigator) {
    // Return promise indicator - actual data collected server-side if needed
    return 'available';
  }
  return 'not_available';
}

function getConnectionInfo() {
  if ('connection' in navigator) {
    const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    return conn ? `${conn.effectiveType || 'unknown'}_${conn.downlink || 0}` : 'unknown';
  }
  return 'not_available';
}

function getMediaDevicesInfo() {
  if ('mediaDevices' in navigator && 'enumerateDevices' in navigator.mediaDevices) {
    // Return count instead of actual devices for privacy
    return 'enumerable';
  }
  return 'not_available';
}

function getStorageQuota() {
  if ('storage' in navigator && 'estimate' in navigator.storage) {
    return 'available';
  }
  return 'not_available';
}

function getPermissionsInfo() {
  if ('permissions' in navigator) {
    return 'available';
  }
  return 'not_available';
}

function getFontList() {
  // Basic font detection - fast method
  const baseFonts = ['monospace', 'sans-serif', 'serif'];
  const testFonts = ['Arial', 'Times', 'Courier', 'Helvetica', 'Georgia', 'Verdana'];
  const detected = [];

  try {
    const testString = 'mmmmmmmmmmlli';
    const testSize = '72px';

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    for (const font of testFonts) {
      let matched = false;
      for (const baseFont of baseFonts) {
        context.font = testSize + ' ' + font + ', ' + baseFont;
        const baseWidth = context.measureText(testString).width;

        context.font = testSize + ' ' + baseFont;
        const testWidth = context.measureText(testString).width;

        if (baseWidth !== testWidth) {
          matched = true;
          break;
        }
      }
      if (matched) detected.push(font);
    }
  } catch (_) {}

  return detected.join(',');
}

function getLocalStorageInfo() {
  try {
    return typeof Storage !== 'undefined' && localStorage ? 'available' : 'not_available';
  } catch (_) {
    return 'not_available';
  }
}

function getSessionStorageInfo() {
  try {
    return typeof Storage !== 'undefined' && sessionStorage ? 'available' : 'not_available';
  } catch (_) {
    return 'not_available';
  }
}

function getIndexedDBInfo() {
  try {
    return 'indexedDB' in window ? 'available' : 'not_available';
  } catch (_) {
    return 'not_available';
  }
}

function getPluginsInfo() {
  try {
    if (navigator.plugins && navigator.plugins.length > 0) {
      // Return count instead of actual plugin names for privacy
      return `count_${navigator.plugins.length}`;
    }
    return 'none';
  } catch (_) {
    return 'not_available';
  }
}

function generateClientFingerprint(components) {
  // Simple client-side hash generation using existing data
  const str = Object.values(components).join('|');
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash).toString(16);
}

function getAudioFingerprint() {
  try {
    if ('AudioContext' in window || 'webkitAudioContext' in window) {
      return 'available';
    }
  } catch (_) {}
  return 'not_available';
}

class AuthService {
  constructor() {
    this.authMethod = 'jwt'; // Default to JWT
  }

  /**
   * Login user with username and password
   * Uses JWT authentication by default
   */
  async login(username, password) {
    try {
      const deviceInfo = getClientDeviceInfo();
      const payload = { username, password, ...deviceInfo };

      // Use the correct login endpoint
      const response = await api.post('auth/login-with-verification-check/', payload);
      const data = response.data || {};

      // Store JWT tokens
      if (data.access || data.access_token) {
        const accessToken = data.access || data.access_token;
        const refreshToken = data.refresh || data.refresh_token;
        setTokens(accessToken, refreshToken);
      }

      return {
        success: true,
        user: data.user,
        tokens: {
          access: data.access || data.access_token,
          refresh: data.refresh || data.refresh_token
        },
        verification_status: data.verification_status,
        verification_message: data.verification_message
      };
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Login user with verification check
   * Uses the new login-with-verification-check endpoint
   */
  async loginWithVerificationCheck(username, password) {
    try {
      const deviceInfo = getClientDeviceInfo();
      const payload = { username, password, ...deviceInfo };

      // Use the primary login-with-verification-check endpoint
      const response = await api.post('auth/login-with-verification-check/', payload);
      const data = response.data || {};

      // Store JWT tokens
      if (data.access) {
        setTokens(data.access, data.refresh);
      }

      return {
        success: true,
        user: data.user,
        tokens: {
          access: data.access,
          refresh: data.refresh
        },
        message: data.message
      };
    } catch (error) {
      // Handle verification errors specifically
      if (error?.response?.status === 403 && error?.response?.data?.verification_required) {
        const errorData = error.response.data;
        return {
          success: false,
          verification_required: true,
          verification_status: errorData.status,
          error: errorData.error,
          message: errorData.message,
          user_id: errorData.user_id,
          verification_sent: errorData.verification_sent
        };
      }
      throw this.handleAuthError(error);
    }
  }

  /**
   * Register new user
   */
  async register(userData) {
    try {
      const response = await api.post('auth/register/', userData);
      const data = response.data || {};

      // Store JWT tokens if provided
      if (data.access_token || data.access) {
        const accessToken = data.access_token || data.access;
        const refreshToken = data.refresh_token || data.refresh;
        setTokens(accessToken, refreshToken);
      }

      return {
        success: true,
        user: data.user,
        tokens: {
          access: data.access_token || data.access,
          refresh: data.refresh_token || data.refresh
        },
        message: data.message
      };
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Logout user
   */
  async logout() {
    try {
      const refreshToken = getRefreshToken();

      // Call logout endpoint with refresh token
      await api.post('auth/logout/', {
        refresh: refreshToken
      });

      // Clear tokens
      clearTokens();

      return { success: true };
    } catch (error) {
      // Even if logout fails, clear local tokens
      clearTokens();
      console.error('Logout error:', error);
      return { success: true }; // Don't throw on logout failure
    }
  }

  /**
   * Get current user info
   */
  async getCurrentUser() {
    try {
      const response = await api.get('auth/user-info/');
      return {
        success: true,
        user: response.data
      };
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Verify email with code
   */
  async verifyEmail(email, code) {
    try {
      const response = await api.post('auth/verify/', {
        email,
        code
      });
      return {
        success: true,
        message: response.data.message || 'Email verified successfully'
      };
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Resend verification code
   */
  async resendVerificationCode(email) {
    try {
      const response = await api.post('auth/resend-code/', {
        email
      });
      return {
        success: true,
        message: response.data.message || 'Verification code sent'
      };
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Check if user is authenticated
   * Now includes fallback check for post-restart scenarios
   */
  isAuthenticated() {
    return !!getAccessToken();
  }

  /**
   * Validate current session/token with fallback recovery
   * This method now handles post-restart authentication recovery
   */
  async validateSession() {
    try {
      // If no token, try session-based authentication recovery
      if (!this.isAuthenticated()) {
        console.log('No JWT token found, attempting session recovery...');
        return await this.attemptSessionRecovery();
      }

      // Try to validate existing token
      const response = await api.get('auth/user-info/');
      const userData = response.data || {};

      return {
        isValid: true,
        user: userData
      };
    } catch (error) {
      // If token validation fails, try session recovery before giving up
      if (error?.response && (error.response.status === 401 || error.response.status === 403)) {
        console.log('JWT validation failed, attempting session recovery...');
        clearTokens(); // Clear invalid tokens
        return await this.attemptSessionRecovery();
      }
      console.warn('Session validation warning:', error?.message || error);
      return { isValid: false, user: null };
    }
  }

  /**
   * Attempt to recover authentication using server-side session fallback
   * This handles post-restart scenarios where JWT is lost but session remains
   */
  async attemptSessionRecovery() {
    try {
      console.log('Attempting session-based authentication recovery...');

      // Make a request without Authorization header
      // This will trigger the server-side fingerprint fallback
      const response = await api.get('auth/user-info/');

      // Check if server provided new tokens in response headers
      const newAccessToken = response.headers['x-renewed-access'];
      const newRefreshToken = response.headers['x-renewed-refresh'];

      if (newAccessToken) {
        console.log('✅ Session recovery successful - new tokens received');
        setTokens(newAccessToken, newRefreshToken);

        return {
          isValid: true,
          user: response.data,
          recovered: true // Flag indicating recovery occurred
        };
      }

      // If we get user data but no new tokens, session is valid
      if (response.data) {
        console.log('✅ Session recovery successful - existing session valid');
        return {
          isValid: true,
          user: response.data,
          recovered: true
        };
      }

      return { isValid: false, user: null };

    } catch (error) {
      console.log('❌ Session recovery failed:', error?.response?.status || error.message);
      return { isValid: false, user: null };
    }
  }

  /**
   * Handle authentication errors consistently
   */
  handleAuthError(error) {
    if (error?.response?.data) {
      const data = error.response.data;

      // Check for detailed error message (common format: { detail: "message" })
      if (data.detail) {
        return new Error(data.detail);
      }

      // Check for error field (alternative format: { error: "message" })
      if (data.error) {
        return new Error(data.error);
      }

      // Check for message field (alternative format: { message: "message" })
      if (data.message) {
        return new Error(data.message);
      }

      // Handle validation errors (field-specific errors)
      if (typeof data === 'object' && !Array.isArray(data)) {
        const messages = Object.entries(data)
          .map(([field, msgs]) => {
            if (field === 'non_field_errors') {
              return Array.isArray(msgs) ? msgs.join(', ') : msgs;
            }
            return `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`;
          })
          .join(' | ');
        return new Error(messages);
      } else if (typeof data === 'string') {
        return new Error(data);
      } else {
        return new Error('Authentication failed');
      }
    }
    return new Error(error?.message || 'Authentication failed. Please try again.');
  }

  /**
   * Change password
   */
  async changePassword(oldPassword, newPassword, confirmPassword) {
    try {
      const response = await api.post('auth/change-password/', {
        old_password: oldPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      });
      return {
        success: true,
        message: response.data.message || 'Password changed successfully'
      };
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email) {
    try {
      const response = await api.post('auth/password-reset/', {
        email
      });
      return {
        success: true,
        message: response.data.message || 'Password reset email sent'
      };
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  /**
   * Reset password with token
   */
  async resetPassword(token, password, confirmPassword) {
    try {
      const response = await api.post('auth/password-reset/confirm/', {
        token,
        password,
        confirm_password: confirmPassword
      });
      return {
        success: true,
        message: response.data.message || 'Password reset successfully'
      };
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }
}

// Create and export singleton instance
export const authService = new AuthService();
export default authService;
