import apiService from './apiService';

class NotificationWebSocket {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectBaseDelay = 1000;
    this.pingInterval = null;
    this.pingIntervalTime = 30000; // 30 seconds
    this.listeners = new Set();
    this.token = null;
    this.reconnectTimeoutId = null;
    this.connectionTimeoutId = null;
    this.authFailureCount = 0;
    this.maxAuthFailures = 3;
    this.messageQueue = []; // Queue for messages sent when not connected
  }

  /**
   * Reconnect WebSocket with new JWT token (called when token is refreshed)
   */
  reconnectWithNewToken() {
    console.log('🔄 Reconnecting WebSocket with new JWT token...');
    this.authFailureCount = 0; // Reset failure count

    // Disconnect current connection if exists
    if (this.ws) {
      this.ws.close(1000, 'Reconnecting with new token');
    }

    // Reconnect with new token
    this.scheduleReconnect();
  }

  /**
   * Check if user has valid authentication credentials
   * @returns {boolean} True if user has valid token
   */
  hasValidAuthentication() {
    const token = apiService.getAccessToken();

    // Check if we have a token
    if (!token) {
      console.log('No authentication token found');
      return false;
    }

    // Check if token is expired (basic check)
    if (this.isTokenExpired(token)) {
      console.log('Authentication token is expired');
      return false;
    }

    return true;
  }

  /**
   * Check if JWT token is expired
   * @param {string} token - JWT token
   * @returns {boolean} True if token is expired
   */
  isTokenExpired(token) {
    if (!token) return true;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expirationTime = payload.exp * 1000; // Convert to milliseconds
      return Date.now() >= expirationTime;
    } catch (error) {
      console.error('Error checking token expiration:', error);
      return true;
    }
  }

  /**
   * Redirect user to login page when authentication fails
   */
  redirectToLogin() {
    console.log('Redirecting to login due to authentication failure');

    // Clear any stored tokens
    apiService.clearTokens();

    // Store current page for redirect after login if not already on login/register
    const currentPath = window.location.pathname + window.location.search + window.location.hash;
    if (!['/login', '/register', '/verify'].includes(window.location.pathname)) {
      localStorage.setItem('redirectAfterLogin', currentPath);
    }

    // Redirect to login page
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }

  /**
   * Connect to the WebSocket with authentication validation
   * @param {Function} onNotification - Callback for notifications
   */
  connect(onNotification) {
    if (this.isConnected) {
      console.warn('WebSocket already connected');
      return;
    }

    // Check authentication before attempting connection
    if (!this.hasValidAuthentication()) {
      console.error('Cannot connect WebSocket: Invalid or missing authentication');
      this.redirectToLogin();
      return;
    }

    const token = apiService.getAccessToken();
    this.token = token;
    this.isConnecting = true;

    // Extract session ID from JWT token
    const sessionId = this.extractSessionIdFromToken(token);

    // Build WebSocket URL with authentication parameters
    let wsUrl = `ws://127.0.0.1:8000/ws/notifications/`;
    if (token && sessionId) {
      wsUrl += `?token=${token}&session_id=${sessionId}`;
    } else if (token) {
      wsUrl += `?token=${token}`;
    }

    console.log('Connecting to notifications WebSocket with universal authentication...');

    // Set connection timeout
    this.connectionTimeoutId = setTimeout(() => {
      if (this.isConnecting) {
        console.error('WebSocket connection timeout');
        this.isConnecting = false;
        if (this.ws) {
          this.ws.close();
        }
        this.handleConnectionFailure();
      }
    }, 10000); // 10 second timeout

    this.ws = new WebSocket(wsUrl);

    // WebSocket event handlers
    this.ws.onopen = (event) => {
      console.log('WebSocket connected:', event);
      this.isConnected = true;
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.authFailureCount = 0; // Reset auth failure count on successful connection

      // Clear connection timeout
      if (this.connectionTimeoutId) {
        clearTimeout(this.connectionTimeoutId);
        this.connectionTimeoutId = null;
      }

      this.startPingInterval();

      // Process any queued messages
      this.processMessageQueue();

      // Notify listeners of connection
      this.notifyListeners({
        type: 'connection_opened',
        message: 'WebSocket connected successfully'
      });

      // Store notification callback
      if (onNotification && typeof onNotification === 'function') {
        this.addListener(onNotification);
      } else if (onNotification) {
        console.error('connect() expects a function callback, got:', typeof onNotification);
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);

        // Handle different message types
        if (data.type === 'notification') {
          this.notifyListeners(data);
        } else if (data.type === 'pong') {
          console.log('Pong received');
        } else if (data.type === 'error') {
          console.error('WebSocket error message:', data.message);

          // Check if it's an authentication error
          if (data.message && data.message.includes('authentication')) {
            this.handleAuthenticationFailure();
          }
        } else {
          // Forward all other message types to listeners
          this.notifyListeners(data);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.isConnected = false;
      this.isConnecting = false;
      this.stopPingInterval();

      // Clear connection timeout
      if (this.connectionTimeoutId) {
        clearTimeout(this.connectionTimeoutId);
        this.connectionTimeoutId = null;
      }

      // Notify listeners of disconnection
      this.notifyListeners({
        type: 'connection_closed',
        code: event.code,
        reason: event.reason
      });

      // Handle different close codes
      if (event.code === 4001) {
        // Authentication failed
        this.handleAuthenticationFailure();
      } else if (event.code === 4002) {
        // Token expired
        console.log('WebSocket closed: Token expired');
        this.handleTokenExpiration();
      } else if (this.shouldAttemptReconnect(event.code)) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.isConnecting = false;

      // Clear connection timeout
      if (this.connectionTimeoutId) {
        clearTimeout(this.connectionTimeoutId);
        this.connectionTimeoutId = null;
      }

      this.notifyListeners({
        type: 'connection_error',
        error: error
      });
    };
  }

  /**
   * Handle connection failures
   */
  handleConnectionFailure() {
    // Check if we should redirect to login
    if (!this.hasValidAuthentication()) {
      this.redirectToLogin();
      return;
    }

    // Otherwise try to reconnect
    this.scheduleReconnect();
  }

  /**
   * Handle authentication failures
   */
  handleAuthenticationFailure() {
    this.authFailureCount++;
    console.error(`WebSocket authentication failure #${this.authFailureCount}`);

    if (this.authFailureCount >= this.maxAuthFailures) {
      console.log('Max authentication failures reached, waiting for JWT renewal from HTTP requests');
      this.stopReconnectionAttempts();
      // Don't redirect to login - just wait for JWT renewal from HTTP middleware
      // When new JWT is set, reconnectWithNewToken() will be called automatically
      return;
    }

    // For fewer failures, still try direct token refresh
    this.attemptTokenRefreshAndReconnect();
  }

  /**
   * Handle token expiration
   */
  handleTokenExpiration() {
    console.log('Handling token expiration...');
    this.attemptTokenRefreshAndReconnect();
  }

  /**
   * Attempt to refresh token and reconnect
   * Note: apiService handles token refresh automatically via interceptors,
   * so we just try to reconnect with the current token
   */
  async attemptTokenRefreshAndReconnect() {
    try {
      console.log('Checking for token refresh...');

      // Check if we have a valid token after automatic refresh
      if (this.hasValidAuthentication()) {
        console.log('Token is valid, reconnecting...');
        this.scheduleReconnect();
      } else {
        console.error('No valid token available, redirecting to login');
        this.redirectToLogin();
      }
    } catch (error) {
      console.error('Error checking token:', error);
      this.redirectToLogin();
    }
  }

  /**
   * Determine if reconnection should be attempted based on close code
   * @param {number} closeCode - WebSocket close code
   * @returns {boolean} Whether to attempt reconnection
   */
  shouldAttemptReconnect(closeCode) {
    // Don't reconnect on authentication failures or client-initiated closes
    const noReconnectCodes = [1000, 4001, 4002, 4003]; // Normal, auth failed, token expired, forbidden
    return !noReconnectCodes.includes(closeCode) && this.reconnectAttempts < this.maxReconnectAttempts;
  }

  /**
   * Stop all reconnection attempts
   */
  stopReconnectionAttempts() {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    this.notifyListeners({
      type: 'reconnection_stopped',
      message: 'Reconnection attempts stopped due to authentication failure'
    });
  }

  /**
   * Schedule automatic reconnection with token validation
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      this.notifyListeners({
        type: 'connection_failed',
        message: 'Max reconnection attempts reached'
      });
      return;
    }

    // Check authentication before scheduling reconnect
    if (!this.hasValidAuthentication()) {
      console.log('Cannot schedule reconnect: Invalid authentication');
      this.redirectToLogin();
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectBaseDelay * Math.pow(2, this.reconnectAttempts - 1),
      30000 // Max 30 seconds
    );

    console.log(`Scheduling WebSocket reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

    this.notifyListeners({
      type: 'reconnection_scheduled',
      attempt: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts,
      delay: delay
    });

    this.reconnectTimeoutId = setTimeout(() => {
      // Validate authentication again before reconnecting
      if (!this.hasValidAuthentication()) {
        console.log('Authentication invalid during reconnection attempt');
        this.redirectToLogin();
        return;
      }

      console.log(`Reconnecting WebSocket (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

      // Get fresh token for reconnection
      this.token = apiService.getAccessToken();
      if (this.token) {
        this.connect();
      } else {
        console.log('Token no longer available during reconnection attempt');
        this.redirectToLogin();
      }
    }, delay);
  }

  /**
   * Add event listener
   * @param {Function} callback - Event handler function
   * @returns {Function} Unsubscribe function
   */
  addListener(callback) {
    if (typeof callback !== 'function') {
      console.error('addListener expects a function, got:', typeof callback);
      return () => {}; // Return empty unsubscribe function
    }

    this.listeners.add(callback);
    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * Remove event listener
   * @param {Function} callback - Event handler function to remove
   */
  removeListener(callback) {
    this.listeners.delete(callback);
  }

  /**
   * Notify all listeners of an event
   * @param {Object} data - Event data
   */
  notifyListeners(data) {
    this.listeners.forEach(callback => {
      if (typeof callback !== 'function') {
        console.error('Invalid listener detected (not a function):', typeof callback);
        this.listeners.delete(callback); // Remove invalid listener
        return;
      }

      try {
        callback(data);
      } catch (error) {
        console.error('Error in notification listener:', error);
      }
    });
  }

  /**
   * Start ping interval to keep connection alive
   */
  startPingInterval() {
    this.pingInterval = setInterval(() => {
      if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
        console.log('Ping sent');
      }
    }, this.pingIntervalTime);
  }

  /**
   * Stop ping interval
   */
  stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Request notification history from the server
   * @param {number} page - Page number (default: 1)
   * @param {number} limit - Number of notifications per page (default: 20)
   */
  requestHistory(page = 1, limit = 20) {
    console.log(`Requesting notification history - page: ${page}, limit: ${limit}`);

    // Queue the message if not connected, it will be sent when connection is established
    this.send({
      type: 'get_notification_history',
      page: page,
      limit: limit
    }, true); // true = queue if disconnected
  }

  /**
   * Send a message through the WebSocket
   * @param {Object} message - Message to send
   * @param {boolean} queueIfDisconnected - Whether to queue message if not connected (default: false)
   */
  send(message, queueIfDisconnected = false) {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else if (queueIfDisconnected) {
      console.log('Queueing message until WebSocket connects:', message.type);
      this.messageQueue.push(message);
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  }

  /**
   * Process queued messages when connection is established
   */
  processMessageQueue() {
    if (this.messageQueue.length > 0) {
      console.log(`Processing ${this.messageQueue.length} queued messages`);
      while (this.messageQueue.length > 0) {
        const message = this.messageQueue.shift();
        this.send(message);
      }
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    if (this.connectionTimeoutId) {
      clearTimeout(this.connectionTimeoutId);
      this.connectionTimeoutId = null;
    }

    this.stopPingInterval();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }

    this.isConnected = false;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.authFailureCount = 0;
    this.token = null;
    this.messageQueue = []; // Clear any queued messages
    this.listeners.clear();
  }

  /**
   * Extract session ID from JWT token
   * @param {string} token - JWT token
   * @returns {string|null} Session ID or null if not found
   */
  extractSessionIdFromToken(token) {
    if (!token) return null;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.sid || payload.session_id || null; // Check both 'sid' and 'session_id'
    } catch (error) {
      console.error('Error extracting session ID from token:', error);
      return null;
    }
  }

  /**
   * Get connection status
   * @returns {Object} Connection status information
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts,
      hasToken: !!this.token,
      hasValidAuth: this.hasValidAuthentication(),
      authFailureCount: this.authFailureCount
    };
  }
}

// Create and export singleton instance
const notificationWebSocket = new NotificationWebSocket();

// Export both as default and named export for compatibility
export { notificationWebSocket };
export default notificationWebSocket;
