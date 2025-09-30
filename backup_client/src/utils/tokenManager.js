/**
 * Centralized JWT Token Manager
 *
 * Ensures consistent JWT token management across:
 * - HTTP requests (axios interceptors)
 * - WebSocket connections
 * - All frontend services
 *
 * Single source of truth for JWT token state
 */

class TokenManager {
  constructor() {
    this.listeners = new Set();
    this.currentToken = null;

    // Load current token from localStorage on initialization
    this.currentToken = localStorage.getItem('access_token');

    // Listen for storage events (token changes in other tabs)
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', (event) => {
        if (event.key === 'access_token') {
          this.currentToken = event.newValue;
          this.notifyListeners('storage_update', event.newValue);
        }
      });
    }
  }

  /**
   * Update JWT token and notify all listeners
   * @param {string} token - New JWT token
   * @param {string} source - Source of the token update
   */
  updateToken(token, source = 'unknown') {
    if (!token) {
      console.warn('Attempted to update with empty token');
      return;
    }

    // Update internal state
    this.currentToken = token;

    // Update localStorage
    localStorage.setItem('access_token', token);

    // Notify all listeners
    this.notifyListeners('token_updated', token, source);

    console.log(`🔄 JWT token updated from ${source}`);
  }

  /**
   * Get current JWT token
   * @returns {string|null} Current JWT token
   */
  getToken() {
    return this.currentToken || localStorage.getItem('access_token');
  }

  /**
   * Clear JWT token
   */
  clearToken() {
    this.currentToken = null;
    localStorage.removeItem('access_token');
    this.notifyListeners('token_cleared', null);
  }

  /**
   * Add token update listener
   * @param {Function} callback - Listener callback
   * @returns {Function} Unsubscribe function
   */
  addListener(callback) {
    this.listeners.add(callback);
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * Notify all listeners of token changes
   * @param {string} event - Event type
   * @param {string} token - Token value
   * @param {string} source - Update source
   */
  notifyListeners(event, token, source) {
    this.listeners.forEach(callback => {
      try {
        callback({ event, token, source });
      } catch (error) {
        console.error('Error in token listener:', error);
      }
    });
  }

  /**
   * Check if current token is expired (basic check)
   * @returns {boolean} True if token appears expired
   */
  isTokenExpired() {
    const token = this.getToken();
    if (!token) return true;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 < Date.now();
    } catch (error) {
      console.warn('Failed to parse token expiration:', error);
      return true;
    }
  }
}

// Export singleton instance
export const tokenManager = new TokenManager();
export default tokenManager;
