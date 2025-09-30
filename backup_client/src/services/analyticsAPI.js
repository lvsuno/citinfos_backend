/**
 * Analytics API Service
 * Handles all analytics-related API calls including post view tracking
 */

import { baseAPI } from './baseAPI';

class AnalyticsAPI {
  constructor() {
    this.baseURL = '/analytics';
  }

  /**
   * Track a post view with enhanced PostSee integration
   * @param {string} postId - The post ID to track
   * @param {Object} options - Enhanced tracking options
   * @returns {Promise} API response
   */
  async trackPostView(postId, options = {}) {
    try {
      const data = {
        post_id: postId,
        view_duration_seconds: options.viewDuration || 0,
        scroll_percentage: options.scrollPercentage || 0,
        source: options.source || 'feed',
        device_type: this._getDeviceType(),
        session_id: this._getSessionId(),
        clicked_links: options.clickedLinks || [],
        media_viewed: options.mediaViewed || [],
        read_time: options.readTime || 0,
        referrer: options.referrer || document.referrer,
        viewport_width: window.innerWidth,
        viewport_height: window.innerHeight,
        user_agent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        ...options.extraData
      };

      const response = await baseAPI.post('/postsee/track-view/', data);
      return response;
    } catch (error) {
      console.error('Failed to track post view:', error);
      // Don't throw error to avoid breaking user experience
      return null;
    }
  }

  /**
   * Get post view analytics
   * @param {string} postId - Optional specific post ID
   * @param {string} period - Time period (day, week, month, all)
   * @returns {Promise} Analytics data
   */
  async getPostViewAnalytics(postId = null, period = 'week') {
    try {
      const endpoint = postId
        ? `/postsee/analytics/${postId}/`
        : '/postsee/analytics/';

      const response = await baseAPI.get(endpoint, {
        params: { period }
      });
      return response;
    } catch (error) {
      console.error('Failed to get post view analytics:', error);
      throw error;
    }
  }

  /**
   * Get user's view history
   * @param {Object} options - Query options
   * @returns {Promise} User view history
   */
  async getUserViewHistory(options = {}) {
    try {
      const response = await baseAPI.get('/postsee/user/history/', {
        params: {
          limit: options.limit || 50,
          period: options.period || 'month'
        }
      });
      return response;
    } catch (error) {
      console.error('Failed to get user view history:', error);
      throw error;
    }
  }

  /**
   * Get content analytics summary with PostSee integration
   * @param {string} period - Time period
   * @returns {Promise} Content analytics summary
   */
  async getContentAnalyticsSummary(period = 'week') {
    try {
      const response = await baseAPI.get('/postsee/content-summary/', {
        params: { period }
      });
      return response;
    } catch (error) {
      console.error('Failed to get content analytics summary:', error);
      throw error;
    }
  }

  /**
   * Manually sync analytics data
   * @returns {Promise} Sync result
   */
  async syncAnalytics() {
    try {
      const response = await baseAPI.post('/postsee/sync/');
      return response;
    } catch (error) {
      console.error('Failed to sync analytics:', error);
      throw error;
    }
  }

  /**
   * Get session ID for tracking
   * @returns {string} Session identifier
   */
  _getSessionId() {
    let sessionId = sessionStorage.getItem('analytics_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('analytics_session_id', sessionId);
    }
    return sessionId;
  }

  /**
   * Track post engagement (like, comment, share)
   * @param {string} postId - The post ID
   * @param {string} action - The engagement action (like, comment, share)
   * @param {Object} metadata - Additional metadata
   * @returns {Promise} API response
   */
  async trackPostEngagement(postId, action, metadata = {}) {
    try {
      const data = {
        post_id: postId,
        action,
        timestamp: new Date().toISOString(),
        ...metadata
      };

      const response = await baseAPI.post(`${this.baseURL}/track-post-engagement/`, data);
      return response;
    } catch (error) {
      console.error('Failed to track post engagement:', error);
      return null;
    }
  }

  /**
   * Get post analytics data
   * @param {string} postId - The post ID
   * @returns {Promise} Analytics data
   */
  async getPostAnalytics(postId) {
    try {
      const response = await baseAPI.get(`${this.baseURL}/post-analytics/${postId}/`);
      return response;
    } catch (error) {
      console.error('Failed to get post analytics:', error);
      throw error;
    }
  }

  /**
   * Batch track multiple post views
   * @param {Array} views - Array of view data objects
   * @returns {Promise} API response
   */
  async batchTrackPostViews(views) {
    try {
      const response = await baseAPI.post(`${this.baseURL}/batch-track-views/`, {
        views: views.map(view => ({
          ...view,
          device_type: this._getDeviceType(),
          timestamp: new Date().toISOString()
        }))
      });
      return response;
    } catch (error) {
      console.error('Failed to batch track post views:', error);
      return null;
    }
  }

  /**
   * Get user's view history for a post
   * @param {string} postId - The post ID
   * @returns {Promise} View history data
   */
  async getPostViewHistory(postId) {
    try {
      const response = await baseAPI.get(`${this.baseURL}/post-view-history/${postId}/`);
      return response;
    } catch (error) {
      console.error('Failed to get post view history:', error);
      throw error;
    }
  }

  /**
   * Mark post as read
   * @param {string} postId - The post ID
   * @returns {Promise} API response
   */
  async markPostAsRead(postId) {
    try {
      const response = await baseAPI.post(`${this.baseURL}/mark-post-read/`, {
        post_id: postId,
        timestamp: new Date().toISOString()
      });
      return response;
    } catch (error) {
      console.error('Failed to mark post as read:', error);
      return null;
    }
  }

  /**
   * Get reading statistics for user
   * @returns {Promise} Reading stats
   */
  async getReadingStats() {
    try {
      const response = await baseAPI.get(`${this.baseURL}/reading-stats/`);
      return response;
    } catch (error) {
      console.error('Failed to get reading stats:', error);
      throw error;
    }
  }

  // ADMIN ANALYTICS METHODS

  /**
   * Get overview analytics for admin dashboard
   * @returns {Promise} Overview analytics data
   */
  async getOverviewAnalytics() {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/overview/`);
      return response;
    } catch (error) {
      console.error('Failed to get overview analytics:', error);
      throw error;
    }
  }

  /**
   * Get content analytics
   * @param {Object} params - Query parameters
   * @returns {Promise} Content analytics data
   */
  async getContentAnalytics(params = {}) {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/content/`, { params });
      return response;
    } catch (error) {
      console.error('Failed to get content analytics:', error);
      throw error;
    }
  }

  /**
   * Get equipment analytics
   * @param {Object} params - Query parameters
   * @returns {Promise} Equipment analytics data
   */
  async getEquipmentAnalytics(params = {}) {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/equipment/`, { params });
      return response;
    } catch (error) {
      console.error('Failed to get equipment analytics:', error);
      throw error;
    }
  }

  /**
   * Get user analytics
   * @param {Object} params - Query parameters
   * @returns {Promise} User analytics data
   */
  async getUserAnalytics(params = {}) {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/users/`, { params });
      return response;
    } catch (error) {
      console.error('Failed to get user analytics:', error);
      throw error;
    }
  }

  /**
   * Get search analytics
   * @param {Object} params - Query parameters
   * @returns {Promise} Search analytics data
   */
  async getSearchAnalytics(params = {}) {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/search/`, { params });
      return response;
    } catch (error) {
      console.error('Failed to get search analytics:', error);
      throw error;
    }
  }

  /**
   * Get authentication analytics
   * @param {Object} params - Query parameters
   * @returns {Promise} Authentication analytics data
   */
  async getAuthenticationAnalytics(params = {}) {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/authentication/`, { params });
      return response;
    } catch (error) {
      console.error('Failed to get authentication analytics:', error);
      throw error;
    }
  }

  /**
   * Export analytics data
   * @param {string} type - Type of analytics to export
   * @param {string} format - Export format (csv, json)
   * @param {Object} params - Additional parameters
   * @returns {Promise} File blob
   */
  async exportAnalytics(type, format = 'csv', params = {}) {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/export/${type}/`, {
        params: { format, ...params },
        responseType: 'blob'
      });
      return response;
    } catch (error) {
      console.error('Failed to export analytics:', error);
      throw error;
    }
  }

  /**
   * Get real-time analytics data
   * @returns {Promise} Real-time analytics
   */
  async getRealtimeAnalytics() {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/realtime/`);
      return response;
    } catch (error) {
      console.error('Failed to get realtime analytics:', error);
      throw error;
    }
  }

  /**
   * Get top performing content
   * @param {number} limit - Number of items to return
   * @param {string} period - Time period (7d, 30d, etc.)
   * @returns {Promise} Top content data
   */
  async getTopContent(limit = 10, period = '7d') {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/top-content/`, {
        params: { limit, period }
      });
      return response;
    } catch (error) {
      console.error('Failed to get top content:', error);
      throw error;
    }
  }

  /**
   * Get equipment performance metrics
   * @param {string} equipmentId - Optional specific equipment ID
   * @returns {Promise} Equipment metrics
   */
  async getEquipmentMetrics(equipmentId = null) {
    try {
      const url = equipmentId
        ? `${this.baseURL}/admin/equipment-metrics/${equipmentId}/`
        : `${this.baseURL}/admin/equipment-metrics/`;

      const response = await baseAPI.get(url);
      return response;
    } catch (error) {
      console.error('Failed to get equipment metrics:', error);
      throw error;
    }
  }

  /**
   * Get user behavior analytics
   * @param {string} userId - Optional specific user ID
   * @param {string} period - Time period
   * @returns {Promise} User behavior data
   */
  async getUserBehavior(userId = null, period = '30d') {
    try {
      const url = userId
        ? `${this.baseURL}/admin/user-behavior/${userId}/`
        : `${this.baseURL}/admin/user-behavior/`;

      const response = await baseAPI.get(url, { params: { period } });
      return response;
    } catch (error) {
      console.error('Failed to get user behavior:', error);
      throw error;
    }
  }

  /**
   * Get search trends
   * @param {string} period - Time period
   * @returns {Promise} Search trends data
   */
  async getSearchTrends(period = '7d') {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/search-trends/`, {
        params: { period }
      });
      return response;
    } catch (error) {
      console.error('Failed to get search trends:', error);
      throw error;
    }
  }

  /**
   * Get PostSee analytics for dashboard
   * @param {string} period - Time period
   * @returns {Promise} PostSee analytics data
   */
  async getPostSeeAnalytics(period = 'week') {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/postsee/`, {
        params: { period }
      });
      return response;
    } catch (error) {
      console.error('Failed to get PostSee analytics:', error);
      throw error;
    }
  }

  /**
   * Get system performance metrics
   * @returns {Promise} System performance data
   */
  async getSystemPerformance() {
    try {
      const response = await baseAPI.get(`${this.baseURL}/admin/system-performance/`);
      return response;
    } catch (error) {
      console.error('Failed to get system performance:', error);
      throw error;
    }
  }

  /**
   * Private method to detect device type
   * @returns {string} Device type
   */
  _getDeviceType() {
    const userAgent = navigator.userAgent.toLowerCase();
    if (/mobile|android|iphone|ipod|blackberry|iemobile|opera mini/i.test(userAgent)) {
      return 'mobile';
    } else if (/tablet|ipad/i.test(userAgent)) {
      return 'tablet';
    }
    return 'desktop';
  }
}

// Create and export a singleton instance
const analyticsAPI = new AnalyticsAPI();

// Export both as default and named export for flexibility
export default analyticsAPI;
export { analyticsAPI, AnalyticsAPI };
