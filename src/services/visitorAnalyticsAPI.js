/**
 * Visitor Analytics API Service
 *
 * Provides methods to fetch visitor analytics data from the backend.
 * Designed for admin/moderator dashboards.
 */

import { baseAPI } from './baseAPI';

class VisitorAnalyticsAPI {
    constructor() {
        this.baseEndpoint = '/analytics/visitors';
    }

    /**
     * Get visitor statistics for a specific time period
     *
     * @param {Object} params - Query parameters
     * @param {string} params.start_date - Start date (YYYY-MM-DD)
     * @param {string} params.end_date - End date (YYYY-MM-DD)
     * @param {string} params.community_id - Optional: Filter by community
     * @returns {Promise<Object>} Visitor statistics
     */
    async getVisitors(params = {}) {
        const endpoint = this.baseEndpoint + '/';
        return await baseAPI.get(baseAPI.buildEndpoint(endpoint, params));
    }

    /**
     * Get today's visitor statistics
     *
     * @param {string} communityId - Optional: Filter by community
     * @returns {Promise<Object>} Today's statistics
     */
    async getTodayStats(communityId = null) {
        const endpoint = `${this.baseEndpoint}/today/`;
        const params = communityId ? { community_id: communityId } : {};
        return await baseAPI.get(baseAPI.buildEndpoint(endpoint, params));
    }

    /**
     * Get weekly visitor statistics
     *
     * @param {string} communityId - Optional: Filter by community
     * @returns {Promise<Object>} Weekly statistics
     */
    async getWeeklyStats(communityId = null) {
        const endpoint = `${this.baseEndpoint}/weekly/`;
        const params = communityId ? { community_id: communityId } : {};
        return await baseAPI.get(baseAPI.buildEndpoint(endpoint, params));
    }

    /**
     * Get monthly visitor statistics
     *
     * @param {string} communityId - Optional: Filter by community
     * @returns {Promise<Object>} Monthly statistics
     */
    async getMonthlyStats(communityId = null) {
        const endpoint = `${this.baseEndpoint}/monthly/`;
        const params = communityId ? { community_id: communityId } : {};
        return await baseAPI.get(baseAPI.buildEndpoint(endpoint, params));
    }

    /**
     * Get visitor breakdown by division
     *
     * @param {Object} params - Query parameters
     * @param {string} params.start_date - Start date
     * @param {string} params.end_date - End date
     * @param {string} params.community_id - Optional: Filter by community
     * @returns {Promise<Object>} Division breakdown
     */
    async getDivisionBreakdown(params = {}) {
        const endpoint = `${this.baseEndpoint}/division-breakdown/`;
        return await baseAPI.get(baseAPI.buildEndpoint(endpoint, params));
    }

    /**
     * Get visitor trends over time
     *
     * @param {Object} params - Query parameters
     * @param {string} params.start_date - Start date
     * @param {string} params.end_date - End date
     * @param {string} params.interval - 'day', 'week', or 'month'
     * @param {string} params.community_id - Optional: Filter by community
     * @returns {Promise<Array>} Trend data
     */
    async getTrends(params = {}) {
        const endpoint = `${this.baseEndpoint}/trends/`;
        return await baseAPI.get(baseAPI.buildEndpoint(endpoint, params));
    }

    /**
     * Get conversion statistics (anonymous to authenticated)
     *
     * @param {Object} params - Query parameters
     * @param {string} params.start_date - Start date
     * @param {string} params.end_date - End date
     * @returns {Promise<Object>} Conversion statistics
     */
    async getConversions(params = {}) {
        const endpoint = `${this.baseEndpoint}/conversions/`;
        return await baseAPI.get(baseAPI.buildEndpoint(endpoint, params));
    }

    /**
     * Get demographic breakdown
     *
     * @param {Object} params - Query parameters
     * @param {string} params.start_date - Start date
     * @param {string} params.end_date - End date
     * @param {string} params.community_id - Optional: Filter by community
     * @returns {Promise<Object>} Demographic data
     */
    async getDemographics(params = {}) {
        const endpoint = `${this.baseEndpoint}/demographics/`;
        return await baseAPI.get(baseAPI.buildEndpoint(endpoint, params));
    }

    /**
     * Get real-time visitor count
     *
     * @param {string} communityId - Optional: Filter by community
     * @returns {Promise<Object>} Real-time visitor count
     */
    async getRealtime(communityId = null) {
        const endpoint = `${this.baseEndpoint}/realtime/`;
        const params = communityId ? { community_id: communityId } : {};
        return await baseAPI.get(baseAPI.buildEndpoint(endpoint, params));
    }

    /**
     * Get growth statistics
     *
     * @param {Object} params - Query parameters
     * @param {string} params.period - 'week', 'month', or 'year'
     * @param {string} params.community_id - Optional: Filter by community
     * @returns {Promise<Object>} Growth statistics
     */
    async getGrowth(params = {}) {
        const endpoint = `${this.baseEndpoint}/growth/`;
        return await baseAPI.get(baseAPI.buildEndpoint(endpoint, params));
    }

    /**
     * Export visitor data to CSV
     *
     * @param {Object} params - Query parameters
     * @returns {Promise<Blob>} CSV file blob
     */
    async exportCSV(params = {}) {
        const endpoint = `${this.baseEndpoint}/export/`;
        const response = await baseAPI.api.get(baseAPI.buildEndpoint(endpoint, params), {
            responseType: 'blob'
        });
        return response.data;
    }
}

// Export singleton instance
export const visitorAnalyticsAPI = new VisitorAnalyticsAPI();
export default visitorAnalyticsAPI;
