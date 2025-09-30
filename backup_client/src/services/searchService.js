/**
 * Search Service for the Equipment Database Social Platform
 *
 * This service handles all search-related API calls including:
 * - Global search across all content types
 * - Quick search/autocomplete
 * - Content-specific searches
 *
 * Uses the JWT authentication system for authenticated searches.
 */

import { jwtAuthService } from './jwtAuthService';

class SearchService {
  constructor() {
    this.api = jwtAuthService.api; // Access the axios instance directly
  }

  /**
   * Perform global search across all content types
   * @param {string} query - Search query string
   * @param {object} options - Search options
   * @param {Array} options.contentTypes - Content types to search ['posts', 'users', 'equipment', etc.]
   * @param {number} options.limit - Maximum results per content type (default: 20)
   * @param {number} options.offset - Pagination offset (default: 0)
   * @param {object} options.filters - Additional filters (visibility, date_range, etc.)
   * @returns {Promise} Search results
   */
  async globalSearch(query, options = {}) {
    const {
      contentTypes = ['posts', 'users', 'equipment', 'communities', 'messages', 'polls', 'ai_conversations'],
      limit = 20,
      offset = 0,
      filters = {}
    } = options;

    try {
      const params = new URLSearchParams({
        query: query.trim(),
        limit: limit.toString(),
        offset: offset.toString(),
        ...filters
      });

      // Add content types as comma-separated string
      if (contentTypes.length > 0) {
        params.append('content_types', contentTypes.join(','));
      }

  const response = await this.api.get(`/search/global/?${params}`);
      return this.formatSearchResults(response.data);
    } catch (error) {
      console.error('Global search error:', error);

      // Handle different error scenarios
      if (error.response?.status === 401) {
        throw new Error('Authentication required for search');
      } else if (error.response?.status === 400) {
        throw new Error('Invalid search parameters');
      } else if (error.response?.status === 404) {
        // Search endpoints not found - return empty results
        return this.getEmptyResults(query, contentTypes);
      }

      throw new Error('Search service unavailable');
    }
  }

  /**
   * Perform quick search for autocomplete/suggestions
   * @param {string} query - Search query string
   * @param {number} limit - Maximum results (default: 10)
   * @returns {Promise} Quick search results
   */
  async quickSearch(query, limit = 10) {
    try {
      const params = new URLSearchParams({
        query: query.trim(),
        limit: limit.toString()
      });

  const response = await this.api.get(`/search/quick/?${params}`);
      return response.data;
    } catch (error) {
      console.error('Quick search error:', error);

      if (error.response?.status === 404) {
        // Quick search not available - fallback to global search
        return this.globalSearch(query, { limit });
      }

      throw error;
    }
  }

  /**
   * Search specific content type
   * @param {string} contentType - Type of content to search
   * @param {string} query - Search query
   * @param {object} options - Search options
   * @returns {Promise} Content-specific search results
   */
  async searchByType(contentType, query, options = {}) {
    return this.globalSearch(query, {
      ...options,
      contentTypes: [contentType]
    });
  }

  /**
   * Search posts only
   */
  async searchPosts(query, options = {}) {
    return this.searchByType('posts', query, options);
  }

  /**
   * Search users only
   */
  async searchUsers(query, options = {}) {
    return this.searchByType('users', query, options);
  }

  /**
   * Search equipment only
   */
  async searchEquipment(query, options = {}) {
    return this.searchByType('equipment', query, options);
  }

  /**
   * Search communities only
   */
  async searchCommunities(query, options = {}) {
    return this.searchByType('communities', query, options);
  }

  /**
   * Advanced user search with various filtering options
   * @param {string} query - Search query string
   * @param {object} options - Search options
   * @param {string} options.searchType - Type of search (followers_of, members_of, public, professional, commercial)
   * @param {string} options.targetUserId - User ID for 'followers_of' search type
   * @param {string} options.communityId - Community ID for 'members_of' search type
   * @param {number} options.limit - Maximum results (default: 20, max: 50)
   * @param {number} options.offset - Pagination offset (default: 0)
   * @returns {Promise} User search results
   */
  async searchUsersAdvanced(query = '', options = {}) {
    const {
      searchType = 'public',
      targetUserId = null,
      communityId = null,
      limit = 20,
      offset = 0
    } = options;

    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
        search_type: searchType
      });

      if (query.trim()) {
        params.append('q', query.trim());
      }

      if (targetUserId) {
        params.append('target_user_id', targetUserId);
      }

      if (communityId) {
        params.append('community_id', communityId);
      }

  const response = await this.api.get(`/search/users/?${params}`);
      return this.formatUserSearchResults(response.data);
    } catch (error) {
      console.error('User search error:', error);

      if (error.response?.status === 401) {
        throw new Error('Authentication required for user search');
      } else if (error.response?.status === 400) {
        throw new Error(error.response.data?.error || 'Invalid search parameters');
      } else if (error.response?.status === 404) {
        throw new Error(error.response.data?.error || 'Resource not found');
      }

      throw new Error('User search service unavailable');
    }
  }

  /**
   * Search for followers of a specific user
   * @param {string} targetUserId - ID of user whose followers to search
   * @param {string} query - Optional search query to filter followers
   * @param {object} options - Additional options (limit, offset)
   * @returns {Promise} Followers search results
   */
  async searchUserFollowers(targetUserId, query = '', options = {}) {
    return this.searchUsersAdvanced(query, {
      ...options,
      searchType: 'followers_of',
      targetUserId
    });
  }

  /**
   * Search for members of a specific community
   * @param {string} communityId - ID of community whose members to search
   * @param {string} query - Optional search query to filter members
   * @param {object} options - Additional options (limit, offset)
   * @returns {Promise} Community members search results
   */
  async searchCommunityMembers(communityId, query = '', options = {}) {
    return this.searchUsersAdvanced(query, {
      ...options,
      searchType: 'members_of',
      communityId
    });
  }

  /**
   * Search for public users only
   * @param {string} query - Search query
   * @param {object} options - Additional options (limit, offset)
   * @returns {Promise} Public users search results
   */
  async searchPublicUsers(query, options = {}) {
    return this.searchUsersAdvanced(query, {
      ...options,
      searchType: 'public'
    });
  }

  /**
   * Search for professional users only
   * @param {string} query - Search query
   * @param {object} options - Additional options (limit, offset)
   * @returns {Promise} Professional users search results
   */
  async searchProfessionalUsers(query, options = {}) {
    return this.searchUsersAdvanced(query, {
      ...options,
      searchType: 'professional'
    });
  }

  /**
   * Search for commercial users only
   * @param {string} query - Search query
   * @param {object} options - Additional options (limit, offset)
   * @returns {Promise} Commercial users search results
   */
  async searchCommercialUsers(query, options = {}) {
    return this.searchUsersAdvanced(query, {
      ...options,
      searchType: 'commercial'
    });
  }

  /**
   * Format search results to match frontend expectations
   */
  formatSearchResults(data) {
    const results = data.results || {};

    return {
      query: data.query || '',
      total_count: data.total_count || 0,
      results: {
        posts: this.formatPosts(results.posts || []),
        users: this.formatUsers(results.users || []),
        equipment: this.formatEquipment(results.equipment || []),
        communities: this.formatCommunities(results.communities || []),
        messages: this.formatMessages(results.messages || []),
        polls: this.formatPolls(results.polls || []),
        ai_conversations: this.formatAIConversations(results.ai_conversations || [])
      },
      counts: {
        posts: results.posts?.length || 0,
        users: results.users?.length || 0,
        equipment: results.equipment?.length || 0,
        communities: results.communities?.length || 0,
        messages: results.messages?.length || 0,
        polls: results.polls?.length || 0,
        ai_conversations: results.ai_conversations?.length || 0
      },
      filters: data.filters || {},
      timestamp: data.timestamp
    };
  }

  /**
   * Format post results for frontend display
   */
  formatPosts(posts) {
    return posts.map(post => ({
      id: post.id,
      title: post.title || post.content?.substring(0, 100) + '...',
      snippet: post.content?.substring(0, 200) + '...',
      content: post.content,
      author: post.author?.username || 'Unknown',
      authorDisplayName: post.author?.display_name,
      visibility: post.visibility,
      postType: post.post_type,
      createdAt: post.created_at,
      url: `/posts/${post.id}`,
      engagement: post.engagement || {},
      relevanceScore: post.relevance_score || 0
    }));
  }

  /**
   * Format user results for frontend display
   */
  formatUsers(users) {
    return users.map(user => ({
      id: user.id,
      username: user.username,
      displayName: user.display_name,
      fullName: user.display_name,
      bio: user.bio,
      avatar: user.avatar,
      role: user.role,
      location: user.location,
      isVerified: user.is_verified,
      stats: user.stats || {},
      url: `/profile/${user.username}`,
      relevanceScore: user.relevance_score || 0
    }));
  }

  /**
   * Format advanced user search results for frontend display
   */
  formatUserSearchResults(data) {
    const users = data.results || [];

    return {
      users: users.map(user => ({
        id: user.id,
        username: user.username,
        displayName: user.display_name || user.username,
        fullName: user.full_name || user.display_name || user.username,
        bio: user.bio || '',
        avatar: user.avatar,
        role: user.role,
        isPrivate: user.is_private,
        followerCount: user.follower_count || 0,
        followingCount: user.following_count || 0,
        isVerified: user.is_verified || false,
        isProfessional: user.is_professional || false,
        isCommercial: user.is_commercial || false,
        url: `/profile/${user.username}`
      })),
      pagination: data.pagination || {
        total_count: 0,
        limit: 20,
        offset: 0,
        has_next: false,
        has_previous: false
      },
      searchMeta: data.search_meta || {
        query: '',
        search_type: 'public',
        target_user_id: null,
        community_id: null
      }
    };
  }

  /**
   * Format equipment results for frontend display
   */
  formatEquipment(equipment) {
    return equipment.map(item => ({
      id: item.id,
      name: item.name,
      description: item.description,
      status: item.status,
      location: item.location,
      owner: item.owner,
      serialNumber: item.serial_number,
      url: `/equipment/${item.id}`,
      relevanceScore: item.relevance_score || 0
    }));
  }

  /**
   * Format community results for frontend display
   */
  formatCommunities(communities) {
    return communities.map(community => ({
      id: community.id,
      name: community.name,
      description: community.description,
      slug: community.slug,
      members: community.members_count || 0,
      visibility: community.visibility,
      url: `/c/${community.slug}`,
      relevanceScore: community.relevance_score || 0
    }));
  }

  /**
   * Format message results for frontend display
   */
  formatMessages(messages) {
    return messages.map(message => ({
      id: message.id,
      content: message.content,
      author: message.author,
      chatRoom: message.chat_room,
      createdAt: message.created_at,
      url: `/messages/${message.chat_room}`,
      relevanceScore: message.relevance_score || 0
    }));
  }

  /**
   * Format poll results for frontend display
   */
  formatPolls(polls) {
    return polls.map(poll => ({
      id: poll.id,
      question: poll.question,
      description: poll.description,
      author: poll.author,
      optionsCount: poll.options_count || 0,
      votesCount: poll.votes_count || 0,
      expiresAt: poll.expires_at,
      url: `/polls/${poll.id}`,
      relevanceScore: poll.relevance_score || 0
    }));
  }

  /**
   * Format AI conversation results for frontend display
   */
  formatAIConversations(conversations) {
    return conversations.map(conversation => ({
      id: conversation.id,
      title: conversation.title,
      summary: conversation.summary,
      author: conversation.author,
      messagesCount: conversation.messages_count || 0,
      createdAt: conversation.created_at,
      url: `/ai-conversations/${conversation.id}`,
      relevanceScore: conversation.relevance_score || 0
    }));
  }

  /**
   * Get empty search results structure
   */
  getEmptyResults(query, contentTypes) {
    const emptyResults = {};
    const emptyCounts = {};

    contentTypes.forEach(type => {
      emptyResults[type] = [];
      emptyCounts[type] = 0;
    });

    return {
      query: query || '',
      total_count: 0,
      results: emptyResults,
      counts: emptyCounts,
      filters: {},
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Check if search is available (for graceful degradation)
   */
  async checkSearchAvailability() {
    try {
      await this.api.get('/api/search/');
      return true;
    } catch (error) {
      return false;
    }
  }
}

// Create and export singleton instance
export const searchService = new SearchService();
export default searchService;
