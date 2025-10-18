/**
 * Profile API Service
 * Handles all user profile-related API operations
 * Uses actual backend endpoints from accounts app
 */

import BaseAPIService from './baseAPI';

class ProfileAPI extends BaseAPIService {
  constructor() {
    super();
  }

  // Get current user profile
  async getCurrentUserProfile() {
    return this.get('/auth/user-info/');
  }

  // Get user profile by ID
  async getUserProfile(userId) {
    try {
      // Try authenticated profiles endpoint first (for full profile info)
      return await this.get(`/profiles/${userId}/`);
    } catch (error) {
      if (error.response?.status === 401 || error.response?.status === 403) {
        // If authentication fails, try public profile endpoint
        try {
          return await this.get(`/public-profiles/${userId}/`);
        } catch (publicError) {
          // If public endpoint also fails, throw original error
          throw error;
        }
      }
      throw error;
    }
  }

  // Update current user profile
  async updateProfile(profileData) {
    // Handle file uploads (avatar or cover_media) if present
    const hasFileUpload = (profileData.avatar && profileData.avatar instanceof File) ||
                         (profileData.cover_media && profileData.cover_media instanceof File);

    if (hasFileUpload) {
      const formData = new FormData();

      Object.keys(profileData).forEach(key => {
        if (key !== 'avatar' && key !== 'cover_media' && key !== 'cover_media_type') {
          const value = profileData[key];
          if (value !== null && value !== undefined) {
            formData.append(key, value);
          }
        }
      });

      // Append file fields if they exist
      if (profileData.avatar && profileData.avatar instanceof File) {
        formData.append('profile_picture', profileData.avatar); // Use correct field name
      }

      if (profileData.cover_media && profileData.cover_media instanceof File) {
        formData.append('cover_media', profileData.cover_media);
        // Also set cover_media_type based on file type
        const isVideo = profileData.cover_media.type.startsWith('video/');
        formData.append('cover_media_type', isVideo ? 'video' : 'image');
      }

      // Send directly with fetch to avoid any axios content-type issues
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/profiles/me/', {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`
          // Don't set Content-Type - let browser set it with boundary for FormData
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP ${response.status}: ${JSON.stringify(errorData)}`);
      }

      return await response.json();
    } else {
      return this.patch('/profiles/me/', profileData);
    }
  }

  // Get user activity history
  async getUserActivity(userId = null, filters = {}) {
    const endpoint = userId
      ? `/events/?user=${userId}`
      : '/events/';

    const queryParams = this.buildEndpoint(endpoint, {
      event_type: filters.activityType,
      start_date: filters.startDate,
      end_date: filters.endDate,
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });

    const response = await this.get(queryParams);
    return response.results || response;
  }

  // Get user badges
  async getUserBadges(userId = null) {
    const endpoint = userId
      ? `/user-badges/?user=${userId}`
      : '/user-badges/';

    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Get user achievements (same as badges for now)
  async getUserAchievements(userId = null) {
    return this.getUserBadges(userId);
  }

  // Get nearest achievable badge for user
  async getNearestAchievableBadge(userId = null) {
    const endpoint = userId
      ? `/user-badges/nearest_achievable/?user=${userId}`
      : '/user-badges/nearest_achievable/';

    const response = await this.get(endpoint);
    return response;
  }

  // Get user statistics from analytics
  async getUserStats(userId = null) {
    const endpoint = userId
      ? `/user-analytics/?user=${userId}`
      : '/user-analytics/';

    return this.get(endpoint);
  }

  // Get user equipment
  async getUserEquipment(userId = null, filters = {}) {
    const queryParams = this.buildEndpoint('/equipment/', {
      user: userId,
      status: filters.status,
      equipment_type: filters.equipmentType,
      location: filters.location,
      ordering: filters.ordering || '-created_at',
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });

    const response = await this.get(queryParams);
    return response.results || response;
  }

  // Get user communities
  async getUserCommunities(userId = null) {
    const queryParams = this.buildEndpoint('/community-memberships/', {
      user: userId,
    });

    const response = await this.get(queryParams);
    return response.results || response;
  }

  // Get user polls
  async getUserPolls(userId = null, filters = {}) {
    const queryParams = this.buildEndpoint('/polls/', {
      creator: userId,
      status: filters.status,
      ordering: filters.ordering || '-created_at',
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });

    const response = await this.get(queryParams);
    return response.results || response;
  }

  // Get user notifications (placeholder - not implemented in backend)
  async getNotifications(filters = {}) {
    // Return empty array for now since notifications app is not implemented
    return [];
  }

  // Mark notification as read (placeholder)
  async markNotificationRead(notificationId) {
    return { success: true };
  }

  // Mark all notifications as read (placeholder)
  async markAllNotificationsRead() {
    return { success: true };
  }

  // Delete notification (placeholder)
  async deleteNotification(notificationId) {
    return { success: true };
  }

  // Get user preferences from settings
  async getUserPreferences() {
    return this.get('/settings/');
  }

  // Update user preferences
  async updatePreferences(preferences) {
    return this.patch('/settings/', preferences);
  }

  // Get privacy settings (from user settings)
  async getPrivacySettings() {
    return this.get('/settings/?section=privacy');
  }

  // Update privacy settings
  async updatePrivacySettings(privacySettings) {
    return this.patch('/settings/', { privacy: privacySettings });
  }

  // Get notification settings (from user settings)
  async getNotificationSettings() {
    return this.get('/settings/?section=notifications');
  }

  // Update notification settings
  async updateNotificationSettings(notificationSettings) {
    return this.patch('/settings/', { notifications: notificationSettings });
  }

  // Follow user
  async followUser(userId) {
    return this.post('/follows/', { followed: userId });
  }

  // Unfollow user - uses soft deletion (sets is_deleted=True)
  async unfollowUser(userId) {
    try {
      // Find the current user's follow relationship with the target user
      const follows = await this.get(`/follows/?followed=${userId}`);
      if (follows.results && follows.results.length > 0) {
        const followRelation = follows.results[0];
        // Delete the follow relationship (soft delete on backend)
        return this.delete(`/follows/${followRelation.id}/`);
      }
      throw new Error('Follow relationship not found');
    } catch (error) {
      console.error('Error unfollowing user:', error);
      throw error;
    }
  }

  // Toggle follow status - handles both following and unfollowing smartly
  async toggleFollowUser(userId) {
    try {
      // Try the new backend toggle endpoint that handles soft-deleted records
      const result = await this.post('/follows/toggle/', { followed: userId });
      return result;
    } catch (error) {
      // Fallback to original approach if toggle endpoint doesn't exist or fails
      try {
        const result = await this.followUser(userId);
        return result;
      } catch (followError) {
        if (followError.response?.status === 400) {
          // Probably already following, so try to unfollow
          const follows = await this.get(`/follows/?followed=${userId}`);

          if (follows.results && follows.results.length > 0) {
            const followRelation = follows.results[0];
            const result = await this.delete(`/follows/${followRelation.id}/`);
            return result;
          } else {
            throw new Error('No follow relationship found to unfollow');
          }
        }
        throw followError;
      }
    }
  }

  // Check follow status between current user and target user
  async getFollowStatus(userId) {
    try {
      const follows = await this.get(`/follows/?followed=${userId}`);
      if (follows.results && follows.results.length > 0) {
        const follow = follows.results[0];
        return {
          isFollowing: true,
          status: follow.status, // 'pending', 'approved', etc.
          followId: follow.id
        };
      }
      return {
        isFollowing: false,
        status: null,
        followId: null
      };
    } catch (error) {
      console.error('Error checking follow status:', error);
      return {
        isFollowing: false,
        status: null,
        followId: null
      };
    }
  }

  // Get user followers
  async getUserFollowers(userId = null, filters = {}) {
    const queryParams = this.buildEndpoint('/follows/', {
      followed: userId,
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });

    const response = await this.get(queryParams);
    return response.results || response;
  }

  // Get user following
  async getUserFollowing(userId = null, filters = {}) {
    const queryParams = this.buildEndpoint('/follows/', {
      follower: userId,
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });

    const response = await this.get(queryParams);
    return response.results || response;
  }

  // Block user
  async blockUser(userId) {
    return this.post('/blocks/', { blocked_user: userId });
  }

  // Unblock user
  async unblockUser(userId) {
    // Find the block relationship and delete it
    const blocks = await this.get(`/blocks/?blocked_user=${userId}`);
    if (blocks.results && blocks.results.length > 0) {
      return this.delete(`/blocks/${blocks.results[0].id}/`);
    }
    return { success: true };
  }

  // Get blocked users
  async getBlockedUsers() {
    const response = await this.get('/blocks/');
    return response.results || response;
  }

  // Report user (would need to be implemented in backend)
  async reportUser(userId, reason, description = '') {
    return this.post('/content-reports/', {
      reported_user: userId,
      reason: reason,
      description: description,
    });
  }

  // Get user reputation history (placeholder - would need implementation)
  async getReputationHistory(userId = null, filters = {}) {
    return [];
  }

  // Change password (placeholder - needs implementation in backend)
  async changePassword(oldPassword, newPassword) {
    return this.post('/auth/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }

  // Deactivate account (placeholder)
  async deactivateAccount(password) {
    return { success: true, message: 'Account deactivation requested' };
  }

  // Delete account (placeholder)
  async deleteAccount(password) {
    return { success: true, message: 'Account deletion requested' };
  }
}

export const profileAPI = new ProfileAPI();
export default profileAPI;
