/**
 * Polls API Service
 * Handles all poll-related API operations
 * Updated to use actual backend endpoints
 */

import BaseAPIService from './baseAPI';

class PollsAPI extends BaseAPIService {
  constructor() {
    super();
  }

  // Get all polls with optional filters
  async getPolls(filters = {}) {
    const endpoint = this.buildEndpoint('/polls/', {
      search: filters.search,
      status: filters.status,
      community: filters.community,
      creator: filters.creator,
      ordering: filters.ordering || '-created_at',
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Get trending polls
  async getTrendingPolls(limit = 10) {
    const response = await this.get(`/polls/?ordering=-vote_count&limit=${limit}`);
    return response.results || response;
  }

  // Get trending posts that contain polls
  async getTrendingPollPosts(limit = 10) {
    try {
      // Try to get posts that have polls, ordered by poll engagement
      const response = await this.get(`/content/posts/?has_polls=true&ordering=-polls__total_votes&limit=${limit}`);
      return response.results || response;
    } catch (error) {
      // Fallback: get all posts and filter for those with polls
      try {
        const response = await this.get(`/content/posts/?limit=${limit * 3}`);
        const posts = response.results || response;
        const postsWithPolls = posts.filter(post => post.polls && post.polls.length > 0);
        return postsWithPolls.slice(0, limit);
      } catch (fallbackError) {
        console.warn('Failed to fetch trending poll posts:', fallbackError);
        return [];
      }
    }
  }

  // Get a specific poll by ID
  async getPoll(pollId) {
    return this.get(`/polls/${pollId}/`);
  }

  // Create a new poll
  async createPoll(pollData) {
    return this.post('/polls/', {
      question: pollData.question,
      description: pollData.description,
      options: pollData.options,
      allows_multiple_votes: pollData.allowsMultipleVotes,
      is_anonymous: pollData.isAnonymous,
      expires_at: pollData.expiresAt,
      community: pollData.communityId,
      visibility: pollData.visibility || 'public',
    });
  }

  // Update a poll
  async updatePoll(pollId, pollData) {
    return this.patch(`/polls/${pollId}/`, pollData);
  }

  // Delete a poll
  async deletePoll(pollId) {
    return this.delete(`/polls/${pollId}/`);
  }

  // Vote on a poll
  async votePoll(pollId, optionIds) {
    // Use the poll's vote action endpoint
    const votes = Array.isArray(optionIds) ? optionIds : [optionIds];

    try {
      // For multiple choice polls, submit all votes to the poll's vote endpoint
      const votePromises = votes.map(optionId =>
        this.post(`/polls/${pollId}/vote/`, {
          option_id: optionId
        })
      );

      const results = await Promise.all(votePromises);
      return { success: true, votes: results };
    } catch (error) {
      console.error('Error voting on poll:', error);
      throw error;
    }
  }

  // Remove vote from a poll
  async removePollVote(pollId, optionId) {
    try {
      // Use the poll's remove_vote action endpoint
      const result = await this.delete(`/polls/${pollId}/remove_vote/`, {
        option_id: optionId
      });
      return { success: true, result };
    } catch (error) {
      console.error('Error removing vote:', error);
      throw error;
    }
  }

  // Get poll results with aggregated statistics
  async getPollResults(pollId) {
    const [poll, options, votes] = await Promise.all([
      this.getPoll(pollId),
      this.get(`/poll-options/?poll=${pollId}`),
      this.get(`/poll-votes/?poll=${pollId}`)
    ]);

    // Calculate vote statistics
    const optionStats = (options.results || options).map(option => {
      const optionVotes = (votes.results || votes).filter(vote => vote.option === option.id);
      return {
        ...option,
        vote_count: optionVotes.length,
        percentage: (votes.results || votes).length > 0 ?
          (optionVotes.length / (votes.results || votes).length) * 100 : 0
      };
    });

    return {
      ...poll,
      options: optionStats,
      total_votes: (votes.results || votes).length,
      voter_count: new Set((votes.results || votes).map(vote => vote.user)).size
    };
  }

  // Get user's polls
  async getUserPolls(userId, filters = {}) {
    const endpoint = this.buildEndpoint('/polls/', {
      creator: userId,
      ...filters,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Get polls by community
  async getCommunityPolls(communityId, filters = {}) {
    const endpoint = this.buildEndpoint('/polls/', {
      community: communityId,
      ...filters,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Get poll options
  async getPollOptions(pollId) {
    const response = await this.get(`/poll-options/?poll=${pollId}`);
    return response.results || response;
  }

  // Get poll votes
  async getPollVotes(pollId, filters = {}) {
    const endpoint = this.buildEndpoint('/poll-votes/', {
      poll: pollId,
      option: filters.optionId,
      limit: filters.limit || 100,
      offset: filters.offset || 0,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }

  // Get poll voters
  async getPollVoters(pollId, filters = {}) {
    const endpoint = this.buildEndpoint('/poll-voters/', {
      poll: pollId,
      limit: filters.limit || 100,
      offset: filters.offset || 0,
    });
    const response = await this.get(endpoint);
    return response.results || response;
  }
}

export const pollsAPI = new PollsAPI();
export default pollsAPI;
