/**
 * Content API Service
 * Handles all content-related API calls with standardized URLs
 *
 * URL Structure:
 * - /api/content/ - Main content endpoints
 * - /api/v2/ - Unified attachment system
 */

import BaseAPIService from './baseAPI';

class ContentAPIService extends BaseAPIService {
  constructor() {
    super();
    this.contentBaseURL = '/content';
    this.v2BaseURL = '/v2';
  }

  // ========================================
  // POSTS API (/api/content/posts/)
  // ========================================

  async getPosts(params = {}) {
    const queryString = this.buildQueryString(params);
    return this.get(`${this.contentBaseURL}/posts/${queryString}`);
  }

  async getPost(id) {
    return this.get(`${this.contentBaseURL}/posts/${id}/`);
  }

  async createPost(postData) {
    return this.post(`${this.contentBaseURL}/posts/`, postData);
  }

  async updatePost(id, postData) {
    return this.patch(`${this.contentBaseURL}/posts/${id}/`, postData);
  }

  async deletePost(id) {
    return this.delete(`${this.contentBaseURL}/posts/${id}/`);
  }

  // Post Feed
  async getFeed(params = {}) {
    const queryString = this.buildQueryString(params);
    return this.get(`${this.contentBaseURL}/posts/feed/${queryString}`);
  }

  // ========================================
  // SOCIAL INTERACTIONS (/api/content/posts/{id}/)
  // ========================================

  async likePost(postId) {
    return this.post(`${this.contentBaseURL}/posts/${postId}/like/`);
  }

  async dislikePost(postId) {
    return this.post(`${this.contentBaseURL}/posts/${postId}/dislike/`);
  }

  async repost(postId, content = '') {
    return this.post(`${this.contentBaseURL}/posts/${postId}/repost/`, { content });
  }

  async getPostComments(postId, params = {}) {
    const queryString = this.buildQueryString(params);
    return this.get(`${this.contentBaseURL}/posts/${postId}/comments/${queryString}`);
  }

  // ========================================
  // COMMENTS API (/api/content/comments/)
  // ========================================

  async getComments(params = {}) {
    const queryString = this.buildQueryString(params);
    return this.get(`${this.contentBaseURL}/comments/${queryString}`);
  }

  async createComment(commentData) {
    return this.post(`${this.contentBaseURL}/comments/`, commentData);
  }

  async updateComment(id, commentData) {
    return this.patch(`${this.contentBaseURL}/comments/${id}/`, commentData);
  }

  async deleteComment(id) {
    return this.delete(`${this.contentBaseURL}/comments/${id}/`);
  }

  async likeComment(commentId) {
    return this.post(`${this.contentBaseURL}/comments/${commentId}/like/`);
  }

  async dislikeComment(commentId) {
    return this.post(`${this.contentBaseURL}/comments/${commentId}/dislike/`);
  }

  // ========================================
  // UNIFIED ATTACHMENT SYSTEM (API V2)
  // ========================================

  // V2 Posts with attachments
  async createPostWithAttachments(postData) {
    return this.post(`${this.v2BaseURL}/posts/`, postData);
  }

  async getPostAttachments(postId) {
    return this.get(`${this.v2BaseURL}/posts/${postId}/attachments/`);
  }

  async addPostAttachment(postId, attachmentData) {
    return this.post(`${this.v2BaseURL}/posts/${postId}/add-attachment/`, attachmentData);
  }

  async removePostAttachment(postId, attachmentData) {
    return this.delete(`${this.v2BaseURL}/posts/${postId}/remove-attachment/`, attachmentData);
  }

  // V2 Polls
  async getPostPolls(postId) {
    return this.get(`${this.v2BaseURL}/posts/${postId}/polls/`);
  }

  async addPostPoll(postId, pollData) {
    return this.post(`${this.v2BaseURL}/posts/${postId}/add-poll/`, pollData);
  }

  // V2 Bulk operations
  async bulkCreatePosts(postsData) {
    return this.post(`${this.v2BaseURL}/posts/bulk-create/`, postsData);
  }

  // V2 Social interactions
  async likePostV2(postId) {
    return this.post(`${this.v2BaseURL}/posts/${postId}/like/`);
  }

  async dislikePostV2(postId) {
    return this.post(`${this.v2BaseURL}/posts/${postId}/dislike/`);
  }

  async repostV2(postId, content = '') {
    return this.post(`${this.v2BaseURL}/posts/${postId}/repost/`, { content });
  }

  // ========================================
  // DIRECT SHARES (/api/content/direct-shares/)
  // ========================================

  async getDirectShares(params = {}) {
    const queryString = this.buildQueryString(params);
    return this.get(`${this.contentBaseURL}/direct-shares/${queryString}`);
  }

  async createDirectShare(shareData) {
    return this.post(`${this.contentBaseURL}/direct-shares/`, shareData);
  }

  // ========================================
  // MODERATION (/api/content/)
  // ========================================

  async getReports(params = {}) {
    const queryString = this.buildQueryString(params);
    return this.get(`${this.contentBaseURL}/reports/${queryString}`);
  }

  async createReport(reportData) {
    return this.post(`${this.contentBaseURL}/reports/`, reportData);
  }

  async getModerationQueue(params = {}) {
    const queryString = this.buildQueryString(params);
    return this.get(`${this.contentBaseURL}/moderation-queue/${queryString}`);
  }

  // ========================================
  // RECOMMENDATIONS (/api/content/recommendations/)
  // ========================================

  async getRecommendations(params = {}) {
    const queryString = this.buildQueryString(params);
    return this.get(`${this.contentBaseURL}/recommendations/${queryString}`);
  }

  async getUserPreferences() {
    return this.get(`${this.contentBaseURL}/user-preferences/`);
  }

  async updateUserPreferences(preferences) {
    return this.patch(`${this.contentBaseURL}/user-preferences/`, preferences);
  }

  async submitRecommendationFeedback(feedbackData) {
    return this.post(`${this.contentBaseURL}/recommendation-feedback/`, feedbackData);
  }

  // ========================================
  // A/B TESTING (/api/content/experiments/)
  // ========================================

  async getExperiments(params = {}) {
    const queryString = this.buildQueryString(params);
    return this.get(`${this.contentBaseURL}/experiments/${queryString}`);
  }

  async startExperiment(experimentId) {
    return this.post(`${this.contentBaseURL}/experiments/${experimentId}/start/`);
  }

  async stopExperiment(experimentId) {
    return this.post(`${this.contentBaseURL}/experiments/${experimentId}/stop/`);
  }

  async getExperimentStats(experimentId) {
    return this.get(`${this.contentBaseURL}/experiments/${experimentId}/stats/`);
  }

  async recordInteraction(interactionData) {
    return this.post(`${this.contentBaseURL}/interactions/record/`, interactionData);
  }

  async getExperimentDashboard() {
    return this.get(`${this.contentBaseURL}/experiments/dashboard/`);
  }

  // ========================================
  // UTILITY METHODS
  // ========================================

  buildQueryString(params) {
    if (!params || Object.keys(params).length === 0) {
      return '';
    }
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        searchParams.append(key, value);
      }
    });
    return `?${searchParams.toString()}`;
  }

  // Legacy method compatibility - maps old API calls to new structure
  async list() {
    return this.getPosts();
  }

  async create(postData) {
    return this.createPost(postData);
  }

  async retrieve(id) {
    return this.getPost(id);
  }

  async update(id, postData) {
    return this.updatePost(id, postData);
  }

  async destroy(id) {
    return this.deletePost(id);
  }
}

// Create and export singleton instance
export const contentAPI = new ContentAPIService();
export default contentAPI;

// Export organized methods for easy importing
export const {
  // Posts
  getPosts,
  getPost,
  createPost,
  updatePost,
  deletePost,
  getFeed,

  // Social interactions
  likePost,
  dislikePost,
  repost,
  getPostComments,

  // Comments
  getComments,
  createComment,
  updateComment,
  deleteComment,
  likeComment,
  dislikeComment,

  // V2 API
  createPostWithAttachments,
  getPostAttachments,
  addPostAttachment,
  removePostAttachment,
  bulkCreatePosts,

  // Moderation
  getReports,
  createReport,
  getModerationQueue,

  // Recommendations
  getRecommendations,
  getUserPreferences,
  updateUserPreferences,
  submitRecommendationFeedback,

  // A/B Testing
  getExperiments,
  startExperiment,
  stopExperiment,
  recordInteraction
} = contentAPI;
