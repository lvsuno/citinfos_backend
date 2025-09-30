/**
 * Communities API Service
 * Handles all community-related API operations
 * Uses actual backend endpoints from communities app
 */

import BaseAPIService from './baseAPI';

class CommunitiesAPI extends BaseAPIService {
  constructor() {
    super();
  }

  // Get all communities with optional filters
  async getCommunities(filters = {}) {
    const endpoint = this.buildEndpoint('/communities/', {
      search: filters.search,
      privacy_level: filters.privacy_level,
      category: filters.category,
      filter: filters.filter, // member, public, etc.
      ordering: filters.ordering || '-created_at',
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Get community by ID
  async getCommunityById(communityId) {
    return this.get(`/communities/${communityId}/`);
  }

  // Get community by slug
  async getCommunityBySlug(slug) {
    return this.get(`/communities/${slug}/`);
  }

  // Create new community
  async createCommunity(communityData) {
    return this.post('/communities/', communityData);
  }

  // Update community
  async updateCommunity(communityId, communityData) {
    return this.patch(`/communities/${communityId}/`, communityData);
  }

  // Delete community
  async deleteCommunity(communityId) {
    return this.delete(`/communities/${communityId}/`);
  }

  // Join community (create membership)
  async joinCommunity(communitySlug) {
    return this.post(`/communities/${communitySlug}/join/`);
  }

  // Leave community (delete membership)
  async leaveCommunity(communityId) {
    // Find the membership and delete it
    const memberships = await this.get(`/community-memberships/?community=${communityId}`);
    if (memberships.results && memberships.results.length > 0) {
      const membership = memberships.results.find(m => m.community === communityId);
      if (membership) {
        return this.delete(`/community-memberships/${membership.id}/`);
      }
    }
    return { success: true };
  }

  // Get community memberships
  async getCommunityMemberships(communityId, filters = {}) {
    const endpoint = this.buildEndpoint('/community-memberships/', {
      community: communityId,
      status: filters.status,
      role: filters.role,
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Get user's communities
  async getUserCommunities(userId = null) {
    const endpoint = this.buildEndpoint('/community-memberships/', {
      user: userId,
      status: 'active'
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Get community statistics (calculated from memberships)
  async getCommunityStats(communityId) {
    const response = await this.get(`/community-memberships/?community=${communityId}`);
    const memberships = response.results || [];
    console.log('Community stats - raw response:', response);
    console.log('Community stats - memberships array:', memberships);

    return {
      member_count: memberships.length || 0,
      active_members: memberships.filter(m => m.status === 'active').length || 0,
      moderators: memberships.filter(m => m.role === 'moderator' || m.role?.includes('Moderator')).length || 0,
      admins: memberships.filter(m => m.role === 'admin' || m.role?.includes('Admin')).length || 0,
    };
  }

  // Get community posts (would need to be implemented in content app)
  async getCommunityPosts(communityId, filters = {}) {
    const endpoint = this.buildEndpoint('/posts/', {
      community: communityId,
      ordering: filters.ordering || '-created_at',
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Create community post
  async createCommunityPost(communityId, postData) {
    return this.post('/posts/', {
      ...postData,
      community: communityId
    });
  }

  // Get community roles
  async getCommunityRoles(communityId) {
    const response = await this.get(`/community-roles/?community=${communityId}`);
    return response.results || response;
  }

  // Get countries (supports optional search)
  async getCountries(search = '', filters = {}) {
    const endpoint = this.buildEndpoint('/countries/', {
      search,
      limit: filters.limit || 50,
    });
    const response = await this.get(endpoint);
    if (!response) return [];
    if (response.countries) return response.countries;
    if (response.results) return response.results;
    return response;
  }

  // Get cities (supports optional search and filtering by country)
  async getCities(search = '', filters = {}) {
    const endpoint = this.buildEndpoint('/cities/', {
      search,
      country: filters.country || undefined,
      limit: filters.limit || 50,
    });
    const response = await this.get(endpoint);
    // backend returns { cities: [...] } for autocomplete
    if (!response) return [];
    if (response.cities) return response.cities;
    return response;
  }


    // Get cities (supports optional search and filtering by country)
  async getTimezones(search = '', filters = {}) {
    const endpoint = this.buildEndpoint('/timezones/', {
      search,
  page: filters.page || 1,
  limit: filters.limit || 20,
    });
    const response = await this.get(endpoint);
  if (!response) return [];
  if (response.results) return response.results;
  if (response.timezones) return response.timezones;
  return response;
  }

  // Create community role
  async createCommunityRole(roleData) {
    return this.post('/community-roles/', roleData);
  }

  // Update community role
  async updateCommunityRole(roleId, roleData) {
    return this.patch(`/community-roles/${roleId}/`, roleData);
  }

  // Delete community role
  async deleteCommunityRole(roleId) {
    return this.delete(`/community-roles/${roleId}/`);
  }

  // Update member role
  async updateMemberRole(membershipId, roleId) {
    return this.patch(`/community-memberships/${membershipId}/`, {
      role: roleId
    });
  }

  // Remove member from community
  async removeMember(membershipId) {
    return this.delete(`/community-memberships/${membershipId}/`);
  }

  // Get community invitations
  async getCommunityInvitations(communityId, filters = {}) {
    const endpoint = this.buildEndpoint('/community-invitations/', {
      community: communityId,
      status: filters.status,
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Send community invitation
  async sendInvitation(invitationData) {
    return this.post('/community-invitations/', invitationData);
  }

  // Respond to invitation (accept/decline)
  async respondToInvitation(invitationId, response) {
    return this.patch(`/community-invitations/${invitationId}/`, {
      status: response // 'accepted' or 'declined'
    });
  }

  // Get community moderation actions
  async getModerationActions(communityId, filters = {}) {
    const endpoint = this.buildEndpoint('/community-moderation/', {
      community: communityId,
      action_type: filters.actionType,
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Create moderation action
  async createModerationAction(actionData) {
    return this.post('/community-moderation/', actionData);
  }

  // Search communities
  async searchCommunities(searchTerm, filters = {}) {
    return this.getCommunities({
      ...filters,
      search: searchTerm
    });
  }

  // Get featured communities
  async getFeaturedCommunities(limit = 10) {
    return this.getCommunities({
      featured: true,
      limit
    });
  }

  // Get popular communities (by member count)
  async getPopularCommunities(limit = 10) {
    return this.getCommunities({
      ordering: '-member_count',
      limit
    });
  }

  // Get recently active communities
  async getRecentlyActiveCommunities(limit = 10) {
    return this.getCommunities({
      ordering: '-last_activity',
      limit
    });
  }

  // Community Announcements
  // Get community announcements
  async getCommunityAnnouncements(communityId, filters = {}) {
    const endpoint = this.buildEndpoint('/community-announcements/', {
      community: communityId,
      is_welcome_message: filters.isWelcomeMessage,
      is_active: filters.isActive,
      ordering: filters.ordering || '-created_at',
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Create community announcement
  async createCommunityAnnouncement(announcementData) {
    return this.post('/community-announcements/', announcementData);
  }

  // Update community announcement
  async updateCommunityAnnouncement(announcementId, announcementData) {
    return this.patch(`/community-announcements/${announcementId}/`, announcementData);
  }

  // Delete community announcement
  async deleteCommunityAnnouncement(announcementId) {
    return this.delete(`/community-announcements/${announcementId}/`);
  }

  // Get specific community announcement
  async getCommunityAnnouncementById(announcementId) {
    return this.get(`/community-announcements/${announcementId}/`);
  }

  // Moderator Nomination Management
  // Get membership by ID (for moderator nomination details)
  async getMembershipById(membershipId) {
    return this.get(`/community-memberships/${membershipId}/`);
  }

  // Process moderator nomination (accept/decline)
  async processModeratorNomination(nominationData) {
    return this.post('/community-roles/process-moderator-nomination/', nominationData);
  }
}

export const communitiesAPI = new CommunitiesAPI();
export default communitiesAPI;
