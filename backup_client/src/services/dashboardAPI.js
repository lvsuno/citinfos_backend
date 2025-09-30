/**
 * Dashboard API Service
 * Handles dashboard-specific data aggregation and statistics
 * Uses available backend endpoints for dashboard functionality
 */

import BaseAPIService from './baseAPI';

class DashboardAPI extends BaseAPIService {
  constructor() {
    super();
  }

  // Get comprehensive dashboard statistics from various sources
  async getDashboardStats() {
    try {
      // Combine data from multiple endpoints to create dashboard stats
      const [equipmentStats, pollStats, communityStats, userAnalytics] = await Promise.allSettled([
        this.get('/equipment/'),
        this.get('/polls/'),
        this.get('/communities/'),
        this.get('/user-analytics/')
      ]);

      // Process the results and create dashboard stats
      const pollsData = pollStats.status === 'fulfilled' ? (pollStats.value?.results || pollStats.value || []) : [];
      const equipmentData = equipmentStats.status === 'fulfilled' ? (equipmentStats.value?.results || equipmentStats.value || []) : [];
      const communityData = communityStats.status === 'fulfilled' ? (communityStats.value?.results || communityStats.value || []) : [];
      const analyticsData = userAnalytics.status === 'fulfilled' ? userAnalytics.value : null;

      return {
        polls_created: pollsData.length || 0,
        votes_cast: analyticsData?.votes_cast || 0,
        communities_joined: communityData.length || 0,
        equipment_total: equipmentData.length || 0,
        equipment_operational: equipmentData.filter(e => e.status === 'operational')?.length || 0,
        equipment_maintenance: equipmentData.filter(e => e.status === 'maintenance')?.length || 0,
        equipment_broken: equipmentData.filter(e => e.status === 'broken')?.length || 0,
        ai_conversations: analyticsData?.ai_conversations || 0,
        ai_messages_today: analyticsData?.ai_messages_today || 0,
        ai_cost_today: analyticsData?.ai_cost_today || 0,
        ai_cost_month: analyticsData?.ai_cost_month || 0,
        // Additional analytics data
        user_activity: analyticsData?.user_activity || [],
        login_count: analyticsData?.login_count || 0,
        page_views: analyticsData?.page_views || 0,
        time_spent: analyticsData?.time_spent || 0
      };
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      return this.getDefaultStats();
    }
  }

  // Get user analytics for specific time period
  async getUserAnalytics(days = 30) {
    try {
      const response = await this.get(`/user-analytics/?days=${days}`);
      return response;
    } catch (error) {
      console.error('Error fetching user analytics:', error);
      return {
        user_activity: [],
        login_count: 0,
        page_views: 0,
        time_spent: 0
      };
    }
  }

  // Get trending content from content recommendations
  async getTrendingContent(limit = 10) {
    return this.get(`/content/recommendations/?limit=${limit}&type=trending`);
  }

  // Get recommended content for user (same as trending for now)
  async getRecommendedContent(limit = 10) {
    return this.get(`/content/recommendations/?limit=${limit}`);
  }

  // Get user's recent communities activity
  async getRecentCommunitiesActivity() {
    return this.get('/community-memberships/?recent=true');
  }

  // Get equipment status overview
  async getEquipmentOverview() {
    return this.get('/equipment/?summary=true');
  }

  // Get AI usage statistics
  async getAIUsageStats() {
    return this.get('/ai/analytics/');
  }

  // Get notification summary (placeholder - notifications not implemented)
  async getNotificationSummary() {
    return { unread_count: 0, recent: [] };
  }

  // Get user engagement metrics from analytics
  async getEngagementMetrics(period = 'week') {
    return this.get(`/metrics/?period=${period}&type=engagement`);
  }

  // Get quick actions data (derived from user permissions and recent activity)
  async getQuickActions() {
    return {
      can_create_poll: true,
      can_join_community: true,
      can_add_equipment: true,
      recent_actions: []
    };
  }

  // Get personalized feed from content API
  async getPersonalizedFeed(limit = 20, offset = 0) {
    const endpoint = this.buildEndpoint('/content/posts/feed/', {
      limit,
      offset,
      ordering: '-created_at'
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Get user progress and achievements (from user badges)
  async getUserProgress() {
    return this.get('/user-badges/');
  }

  // Mark dashboard item as seen (placeholder - would need implementation)
  async markItemAsSeen(itemType, itemId) {
    return this.post('/events/', {
      event_type: 'item_viewed',
      item_type: itemType,
      item_id: itemId,
    });
  }

  // Get dashboard widgets configuration (from user settings)
  async getWidgetsConfig() {
    return this.get('/settings/?section=dashboard');
  }

  // Update dashboard widgets configuration
  async updateWidgetsConfig(config) {
    return this.patch('/settings/', { dashboard_widgets: config });
  }

  // Debug: Get IP location information
  async getIPLocationDebug() {
    try {
      const response = await this.get('/debug/ip-location/');
      return response;
    } catch (error) {
      console.error('Error fetching IP location debug info:', error);
      return {
        success: false,
        error: error.message,
        client_ip: null,
        location_data: {}
      };
    }
  }

  // Debug: Get custom IP location information
  async getCustomIPLocationDebug(ipAddress) {
    try {
      const response = await this.post('/debug/custom-ip-location/', {
        ip: ipAddress
      });
      return response;
    } catch (error) {
      console.error('Error fetching custom IP location debug info:', error);
      return {
        success: false,
        error: error.message,
        provided_ip: ipAddress,
        location_data: {}
      };
    }
  }

  // Helper method to provide default stats when API calls fail
  getDefaultStats() {
    return {
      polls_created: 0,
      votes_cast: 0,
      communities_joined: 0,
      equipment_total: 0,
      equipment_operational: 0,
      equipment_maintenance: 0,
      equipment_broken: 0,
      ai_conversations: 0,
      ai_messages_today: 0,
      ai_cost_today: 0,
      ai_cost_month: 0
    };
  }
}

export const dashboardAPI = new DashboardAPI();
export default dashboardAPI;
