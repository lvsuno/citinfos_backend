// Enhanced API service for community context features
import BaseAPIService from './baseAPI';

class CommunityContextAPI extends BaseAPIService {
  constructor() {
    super();
  }

  posts = {
    list: async (filters = {}) => {
      const endpoint = this.buildEndpoint('/posts/', {
        context_type: filters.context_type !== 'all' ? filters.context_type : undefined,
        community_id: filters.community_id,
      });
      return this.get(endpoint);
    },
    communityPosts: async (communityId) => {
      const endpoint = this.buildEndpoint('/posts/community_posts/', {
        community_id: communityId,
      });
      return this.get(endpoint);
    },
    generalPosts: async () => this.get('/posts/general_posts/'),
    get: async (id) => this.get(`/posts/${id}/`),
    create: async (postData = {}) => this.post('/posts/', postData),
  };

  comments = {
    list: async (filters = {}) => {
      const endpoint = this.buildEndpoint('/comments/', {
        context_type: filters.context_type !== 'all' ? filters.context_type : undefined,
        community_id: filters.community_id,
      });
      return this.get(endpoint);
    },
    communityComments: async (communityId) => {
      const endpoint = this.buildEndpoint('/comments/community_comments/', {
        community_id: communityId,
      });
      return this.get(endpoint);
    },
    generalComments: async () => this.get('/comments/general_comments/'),
    forPost: async (postId) => this.get(`/comments/?post=${postId}`),
    create: async (commentData = {}) => this.post('/comments/', commentData),
  };

  mentions = {
    list: async (filters = {}) => {
      const endpoint = this.buildEndpoint('/mentions/', {
        context_type: filters.context_type !== 'all' ? filters.context_type : undefined,
        community_id: filters.community_id,
      });
      return this.get(endpoint);
    },
    communityMentions: async (communityId) => {
      const endpoint = this.buildEndpoint('/mentions/community_mentions/', {
        community_id: communityId,
      });
      return this.get(endpoint);
    },
    generalMentions: async () => this.get('/mentions/general_mentions/'),
    forUser: async (userId) => this.get(`/mentions/?mentioned_user=${userId}`),
  };

  statistics = {
    getActivityStats: async () => {
      const [communityPosts, generalPosts, communityComments, generalComments] = await Promise.all([
        this.posts.communityPosts(),
        this.posts.generalPosts(),
        this.comments.communityComments(),
        this.comments.generalComments(),
      ]);

      return {
        community: { posts: communityPosts.length, comments: communityComments.length },
        general: { posts: generalPosts.length, comments: generalComments.length },
      };
    },
    getCommunityStats: async (communityId) => {
      const [posts, comments, mentions] = await Promise.all([
        this.posts.communityPosts(communityId),
        this.comments.communityComments(communityId),
        this.mentions.communityMentions(communityId),
      ]);
      return { posts, comments, mentions, totalActivity: posts.length + comments.length + mentions.length };
    },
  };
}

export const communityContextAPI = new CommunityContextAPI();
export const { posts, comments, mentions, statistics } = communityContextAPI;
export default communityContextAPI;
