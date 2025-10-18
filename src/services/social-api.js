// Posts, Comments, and Mentions API service
// Updated to use new standardized /api/content/ URL structure
import BaseAPIService from './baseAPI';

class SocialAPI extends BaseAPIService {
  constructor() {
    super();
    // Cache content type IDs to avoid repeated API calls
    this.contentTypes = null;
  }

  // Get content type IDs from backend
  async getContentTypes() {
    if (!this.contentTypes) {
      try {
        // For now, we'll use hardcoded values that we got from the shell
        // TODO: Create API endpoint to fetch these dynamically
        this.contentTypes = {
          post: 28,  // From backend: Post ContentType ID
          comment: 22  // From backend: Comment ContentType ID
        };
      } catch (error) {        this.contentTypes = {
          post: 28,
          comment: 22
        };
      }
    }
    return this.contentTypes;
  }

  posts = {
    // Use new standardized /api/content/ endpoints
    list: async (filters = {}) => {
      const endpoint = this.buildEndpoint('/content/posts/', {
        context_type: filters.context_type !== 'all' ? filters.context_type : undefined,
        community_id: filters.community_id,
        thread_id: filters.thread_id,
        division_id: filters.division_id,
        author: filters.author,
        post_type: filters.post_type,
        visibility: filters.visibility,
      });
      const response = await this.get(endpoint);
      const posts = response.results || response;

      return posts;
    },

    // Get combined feed of posts and reposts
    feed: async (page = 1, pageSize = 20) => {
      const endpoint = this.buildEndpoint('/content/posts/feed/', {
        page,
        page_size: pageSize,
      });
      const response = await this.get(endpoint);
      return response;
    },
    communityPosts: async (communityId) => {
      const endpoint = this.buildEndpoint('/content/posts/', {
        community_id: communityId,
        context_type: communityId ? undefined : 'community',
      });
      const response = await this.get(endpoint);
      return response.results || response;
    },
    generalPosts: async () => {
      const response = await this.get('/content/posts/?context_type=general');
      return response.results || response;
    },
    get: async (id) => this.get(`/content/posts/${id}/`),

    // Get posts by a specific user
    getUserPosts: async (userId, filters = {}) => {
      try {
        // Try the new authenticated user_posts endpoint first
        const endpoint = this.buildEndpoint('/content/posts/user_posts/', {
          author: userId,
          page: filters.page || 1,
          page_size: filters.pageSize || 20,
        });
        const response = await this.get(endpoint);
        return response;
      } catch (error) {
        // If authentication fails, try public endpoint
        if (error.response?.status === 401 || error.response?.status === 403) {
          try {
            const response = await this.get(`/public/users/${userId}/posts/`);
            return response;
          } catch (publicError) {
            // If public endpoint also fails, throw original error
            throw error;
          }
        }
        throw error;
      }
    },

    // ====================================================================
    // UNIFIED ATTACHMENT SYSTEM - NEW API ENDPOINTS
    // ====================================================================
    create: async (postData = {}) => {
      // Use new standardized /api/content/ endpoints
      const apiEndpoint = '/content/posts/';

      // Handle file uploads with FormData for unified system
      if (postData.attachments && postData.attachments.length > 0) {
        // For file uploads, we need to create the post first, then add attachments
        // This is because Django REST Framework's nested serializers don't handle
        // FormData with files in a straightforward way

        // First, create the post without attachments
        const postPayload = {
          content: postData.content || '',
          post_type: postData.post_type || 'text',
          visibility: postData.visibility || 'public',
        };

        // If we have attachments but no content, ensure we pass validation
        // by either having content or setting appropriate post_type
        if (postData.attachments && postData.attachments.length > 0) {
          const firstAttachment = postData.attachments[0];
          if (firstAttachment.type) {
            postPayload.post_type = firstAttachment.type;
          }
          // Ensure we have some content to pass validation
          if (!postPayload.content.trim()) {
            postPayload.content = ' '; // Minimal content to pass validation
          }
        }

        if (postData.community_id) {
          postPayload.community = postData.community_id;
        }

        if (postData.thread_id) {
          postPayload.thread = postData.thread_id;
        }

        // Add polls if present, but don't override post_type if attachments are present
        if (postData.polls && postData.polls.length > 0) {
          // Only set post_type to 'poll' if there are no attachments
          if (!postData.attachments || postData.attachments.length === 0) {
            postPayload.post_type = 'poll';
          }
          postPayload.polls = postData.polls.map((poll, index) => ({
            question: poll.question,
            multiple_choice: poll.allows_multiple_votes || false,
            order: index + 1,
            options: poll.options?.map((option, optionIndex) => ({
              text: option.text,
              order: optionIndex + 1
            })) || []
          }));
        }

        // Create the post first
        try {
          const postResponse = await this.post(apiEndpoint, postPayload);
          const postId = postResponse.id;

          if (!postId) {
            throw new Error('Post creation failed - no ID returned');
          }

          // Then add each attachment individually
          const attachmentPromises = postData.attachments.map(async (attachment, index) => {
            const formData = new FormData();
            formData.append('file', attachment.file);
            formData.append('media_type', attachment.type);
            formData.append('order', index + 1);

            try {
              // Use the JWT API instance but temporarily override Content-Type for FormData
              // Save original Content-Type from instance defaults
              const originalContentType = this.api.defaults.headers['Content-Type'];

              // Temporarily remove Content-Type to let browser set multipart/form-data
              delete this.api.defaults.headers['Content-Type'];

              const response = await this.api.post(`/content/posts/${postId}/add-attachment/`, formData);

              // Restore original Content-Type
              if (originalContentType) {
                this.api.defaults.headers['Content-Type'] = originalContentType;
              }

              return response.data;
            } catch (error) {
              throw error;
            }
          });

          // Wait for all attachments to be uploaded
          const attachments = await Promise.all(attachmentPromises);

          // Return the post with attachments
          return {
            ...postResponse,
            attachments: attachments
          };
        } catch (error) {          throw error;
        }
      }

      // Handle polls-only posts (no file attachments)
      if (postData.polls && postData.polls.length > 0) {
        const pollPayload = {
          content: postData.content,
          community: postData.community_id,
          visibility: postData.visibility,
          post_type: 'poll',
          polls: postData.polls.map((poll, index) => ({
            question: poll.question,
            multiple_choice: poll.allows_multiple_votes || false,
            order: index + 1,
            options: poll.options?.map((option, optionIndex) => ({
              text: option.text,
              order: optionIndex + 1
            })) || []
          }))
        };

        if (postData.thread_id) {
          pollPayload.thread = postData.thread_id;
        }

        return this.post(apiEndpoint, pollPayload);
      }

      // Regular JSON payload for simple posts
      const payload = {
        content: postData.content || '',
        post_type: postData.post_type || 'text',
        visibility: postData.visibility || 'public',
      };

      // Only include community if it's provided
      if (postData.community_id) {
        payload.community = postData.community_id;
      }

      // Only include thread if it's provided
      if (postData.thread_id) {
        payload.thread = postData.thread_id;
      }

      // Only include link_url if it's provided
      if (postData.link_url) {
        payload.link_url = postData.link_url;
      }

      return this.post(apiEndpoint, payload);
    },

    // Attachment management methods
    getAttachments: async (postId) => {
      return this.get(`/content/posts/${postId}/attachments/`);
    },

    addAttachment: async (postId, attachmentData) => {
      const formData = new FormData();
      formData.append('media_type', attachmentData.type);
      formData.append('file', attachmentData.file);
      if (attachmentData.order) formData.append('order', attachmentData.order);

      const response = await this.api.post(`/content/posts/${postId}/add-attachment/`, formData);
      return response.data;
    },

    removeAttachment: async (postId, attachmentId) => {
      return this.delete(`/content/posts/${postId}/remove-attachment/`, {
        attachment_id: attachmentId
      });
    },

    // Poll management methods
    getPolls: async (postId) => {
      return this.get(`/content/posts/${postId}/polls/`);
    },

    addPoll: async (postId, pollData) => {
      return this.post(`/content/posts/${postId}/add-poll/`, {
        question: pollData.question,
        multiple_choice: pollData.allows_multiple_votes || false,
        options: pollData.options?.map((option, index) => ({
          text: option.text,
          order: index + 1
        })) || []
      });
    },

    deletePoll: async (pollId) => {
      try {
        return await this.delete(`/polls/${pollId}/`);
      } catch (error) {
        throw error;
      }
    },

    // Migration and status methods
    migrateLegacyMedia: async (postId) => {
      return this.post(`/content/posts/${postId}/migrate-legacy-media/`);
    },

    getMigrationStatus: async () => {
      return this.get('/content/posts/migration-status/');
    },

    // Bulk operations
    bulkCreateWithAttachments: async (postsData) => {
      return this.post('/content/posts/bulk-create/', {
        posts: postsData
      });
    },
    update: async (id, postData = {}) => this.patch(`/content/posts/${id}/`, postData),
    delete: async (id) => {
      try {
        return await this.delete(`/content/posts/${id}/`);
      } catch (error) {
        throw error;
      }
    },
    // Removed old like/unlike/share methods - now using dedicated API endpoints
  };

  comments = {
    list: async (filters = {}) => {
      const endpoint = this.buildEndpoint('/content/comments/', {
        context_type: filters.context_type !== 'all' ? filters.context_type : undefined,
        community_id: filters.community_id,
        post: filters.post,
        author: filters.author,
      });
      const response = await this.get(endpoint);
      return response.results || response;
    },
    communityComments: async (communityId) => {
      const endpoint = this.buildEndpoint('/content/comments/', {
        community_id: communityId,
        context_type: communityId ? undefined : 'community',
      });
      const response = await this.get(endpoint);
      return response.results || response;
    },
    generalComments: async () => {
      const response = await this.get('/content/comments/?context_type=general');
      return response.results || response;
    },
    forPost: async (postId) => {
      const response = await this.get(`/comments/?post=${postId}`);
      return response.results || response;
    },
    get: async (id) => this.get(`/comments/${id}/`),
    create: async (commentData = {}) => this.post('/content/comments/', commentData),
    update: async (id, commentData = {}) => this.patch(`/comments/${id}/`, commentData),
    delete: async (id) => this.delete(`/comments/${id}/`),
    // Removed old like/unlike methods - now using dedicated API endpoints
  };

  // Helper function to resolve username to UserProfile ID
  resolveUsername = async (username, communityId = null) => {
    try {
      let url = `/profiles/search_by_username/?username=${username}`;
      if (communityId) {
        url += `&community_id=${communityId}`;
      }
      const response = await this.get(url);
      return response.id; // Return the UserProfile ID
    } catch (error) {
      if (error.response?.status === 403) {      } else {      }
      return null;
    }
  };

  // Search for mentionable users based on partial username
  searchMentionableUsers = async (query, communityId = null, postId = null) => {
    try {
      let url = `/profiles/search_mentionable/?q=${encodeURIComponent(query)}`;
      if (communityId) {
        url += `&community_id=${communityId}`;
      }
      if (postId) {
        url += `&post_id=${postId}`;
      }
      const response = await this.get(url);
      return response.results || response;
    } catch (error) {      return [];
    }
  };

  searchHashtags = async (query, limit = 20) => {
    try {
      let url = `/content/posts/hashtags/?search=${encodeURIComponent(query)}&limit=${limit}`;
      const response = await this.get(url);
      // Convert the response format to match what we need
      const results = response.results || [];
      return results.map(hashtag => ({
        name: hashtag.name,
        posts_count: hashtag.posts_count,
        is_trending: hashtag.is_trending,
      }));
    } catch (error) {      return [];
    }
  };

  mentions = {
    list: async (filters = {}) => {
      const endpoint = this.buildEndpoint('/content/mentions/', {
        context_type: filters.context_type !== 'all' ? filters.context_type : undefined,
        community_id: filters.community_id,
        mentioned_user: filters.mentioned_user,
        mentioning_user: filters.mentioning_user,
      });
      const response = await this.get(endpoint);
      return response.results || response;
    },
    generalMentions: async () => {
      const response = await this.get('/content/mentions/?context_type=general');
      return response.results || response;
    },
    forUser: async (userId) => {
      const response = await this.get(`/mentions/?mentioned_user=${userId}`);
      return response.results || response;
    },
    received: async () => {
      const response = await this.get('/content/mentions/received/');
      return response.results || response;
    },
    sent: async () => {
      const response = await this.get('/content/mentions/sent/');
      return response.results || response;
    },
    get: async (id) => this.get(`/mentions/${id}/`),
    create: async (mentionData = {}) => this.post('/content/mentions/', mentionData),
    update: async (id, mentionData = {}) => this.patch(`/mentions/${id}/`, mentionData),
    delete: async (id) => this.delete(`/mentions/${id}/`),
    markAsRead: async (id) => this.post(`/mentions/${id}/mark_read/`),
  };

  // ====================================================================
  // COMMUNITIES AND THREADS API
  // ====================================================================

  communities = {
    // List communities with optional division filter
    list: async (divisionId = null) => {
      const endpoint = divisionId
        ? `/communities/?division_id=${divisionId}`
        : '/communities/';
      const response = await this.get(endpoint);
      return response.results || response;
    },

    // Get specific community by slug
    get: async (slug) => {
      return this.get(`/communities/${slug}/`);
    },

    // Create a new community
    create: async (communityData) => {
      return this.post('/communities/', communityData);
    },

    // Update community
    update: async (slug, communityData) => {
      return this.patch(`/communities/${slug}/`, communityData);
    },

    // Delete community
    delete: async (slug) => {
      return this.delete(`/communities/${slug}/`);
    },

    // Get or create default community for a division
    getOrCreateForDivision: async (divisionId) => {
      try {
        // First try to get existing community
        const communities = await this.list(divisionId);
        if (communities && communities.length > 0) {
          return communities[0]; // Return first/default community
        }

        // If no community exists, the backend will auto-create one via signal
        // So we try again after a brief delay
        await new Promise(resolve => setTimeout(resolve, 500));
        const retriedCommunities = await this.list(divisionId);
        return retriedCommunities && retriedCommunities.length > 0
          ? retriedCommunities[0]
          : null;
      } catch (error) {        throw error;
      }
    }
  };

  threads = {
    // List threads with optional community filter
    list: async (communityId = null, communitySlug = null) => {
      let endpoint = '/threads/';
      const params = [];

      if (communityId) {
        params.push(`community_id=${communityId}`);
      } else if (communitySlug) {
        params.push(`community_slug=${communitySlug}`);
      }

      if (params.length > 0) {
        endpoint += '?' + params.join('&');
      }

      const response = await this.get(endpoint);
      return response.results || response;
    },

    // Get specific thread by slug
    get: async (slug) => {
      return this.get(`/threads/${slug}/`);
    },

    // Create a new thread with optional first post
    create: async (threadData) => {
      // Validate required fields
      if (!threadData.community_id) {
        throw new Error('Community ID is required to create a thread');
      }
      if (!threadData.rubrique_template_id) {
        throw new Error('Rubrique template ID is required to create a thread');
      }

      return this.post('/threads/', {
        community: threadData.community_id,
        rubrique_template: threadData.rubrique_template_id,
        title: threadData.title,
        body: threadData.body || '',
        first_post_content: threadData.first_post_content,
        first_post_type: threadData.first_post_type || 'text'
      });
    },

    // Update thread
    update: async (slug, threadData) => {
      return this.patch(`/threads/${slug}/`, threadData);
    },

    // Delete thread
    delete: async (slug) => {
      return this.delete(`/threads/${slug}/`);
    },

    // Get posts in a thread
    posts: async (threadSlug) => {
      return this.get(`/threads/${threadSlug}/posts/`);
    }
  };

  // RUBRIQUE TEMPLATES API
  rubriqueTemplates = {
    // List all rubrique templates
    list: async () => {
      return this.get('/rubrique-templates/');
    },

    // Get rubrique template by template_type (slug)
    getByType: async (templateType) => {
      const templates = await this.list();
      return templates.find(t => t.template_type === templateType);
    }
  };

  // ====================================================================
  // SOCIAL INTERACTIONS API - LIKES, DISLIKES (V2 ENDPOINTS ONLY)
  // ====================================================================

  likes = {
    // Like/unlike a post using v2 endpoint (mutual exclusive with dislikes)
    likePost: async (postId) => {
      return this.post(`/content/posts/${postId}/like/`);
    },

    // Unlike is the same as like (toggles)
    unlikePost: async (postId) => {
      return this.post(`/content/posts/${postId}/like/`);
    },

    // Like/unlike a comment using v2 endpoint (mutual exclusive with dislikes)
    likeComment: async (commentId) => {
      return this.post(`/content/posts/comments/${commentId}/like/`);
    },

    unlikeComment: async (commentId) => {
      return this.post(`/content/posts/comments/${commentId}/like/`);
    }
  };

  dislikes = {
    // Dislike/undislike a post using v2 endpoint (mutual exclusive with likes)
    dislikePost: async (postId) => {
      return this.post(`/content/posts/${postId}/dislike/`);
    },

    // Undislike is the same as dislike (toggles)
    undislikePost: async (postId) => {
      return this.post(`/content/posts/${postId}/dislike/`);
    },

    // Dislike/undislike a comment using v2 endpoint (mutual exclusive with likes)
    dislikeComment: async (commentId) => {
      return this.post(`/content/posts/comments/${commentId}/dislike/`);
    },

    undislikeComment: async (commentId) => {
      return this.post(`/content/posts/comments/${commentId}/dislike/`);
    }
  };

  // Emoji reactions API (22 reaction types)
  reactions = {
    // React to a post with an emoji reaction
    reactPost: async (postId, reactionType) => {
      return this.post(`/content/posts/${postId}/react/`, {
        reaction_type: reactionType
      });
    },

    // Remove reaction from a post
    unreactPost: async (postId) => {
      return this.post(`/content/posts/${postId}/unreact/`);
    },

    // React to a comment with an emoji reaction
    reactComment: async (commentId, reactionType) => {
      return this.post(`/content/posts/comments/${commentId}/react/`, {
        reaction_type: reactionType
      });
    },

    // Remove reaction from a comment
    unreactComment: async (commentId) => {
      return this.post(`/content/posts/comments/${commentId}/unreact/`);
    }
  };

  reposts = {
    // List all reposts - using content posts with type filter
    list: async (filters = {}) => {
      const endpoint = this.buildEndpoint('/content/posts/', {
        ...filters,
        post_type: 'repost'
      });
      const response = await this.get(endpoint);
      return response.results || response;
    },

    // Get specific repost
    get: async (id) => this.get(`/content/posts/${id}/`),

    // Create a repost using the post action endpoint
    create: async (postId, data = {}) => {
      // If data is a string, treat it as a simple comment repost
      if (typeof data === 'string') {
        return this.post(`/content/posts/${postId}/repost/`, {
          comment: data
        });
      }

      // For complex reposts with attachments, we need a different approach
      // First create the repost via the repost endpoint, then add attachments
      try {
        // Create the repost first using the repost endpoint
        const repostResponse = await this.post(`/content/posts/${postId}/repost/`, {
          comment: data.content || '',
          visibility: data.visibility || 'public'
        });

        // Handle the response structure from the backend
        // Backend returns: { message, action, post, repost?: {...} }
        let repostPostId;
        if (repostResponse.repost && repostResponse.repost.id) {
          repostPostId = repostResponse.repost.id;
        } else if (repostResponse.id) {
          repostPostId = repostResponse.id;
        } else {
          throw new Error('Repost creation failed - no ID returned');
        }

        // Handle file uploads if any
        if (data.attachments && data.attachments.length > 0) {
          // Determine the post_type based on attachments
          const hasImages = data.attachments.some(att => att.type === 'image');
          const hasVideos = data.attachments.some(att => att.type === 'video');
          const hasAudio = data.attachments.some(att => att.type === 'audio');
          const hasFiles = data.attachments.some(att => att.type === 'file');

          // Count different types
          const typeCount = [hasImages, hasVideos, hasAudio, hasFiles].filter(Boolean).length;
          const finalPostType = typeCount > 1 ? 'mixed' : data.attachments[0].type;

          // Update the repost with correct post_type
          await this.patch(`/content/posts/${repostPostId}/`, {
            post_type: finalPostType
          });

          // Then add each attachment individually
          const attachmentPromises = data.attachments.map(async (attachment, index) => {
            const formData = new FormData();
            formData.append('file', attachment.file);
            formData.append('media_type', attachment.type);
            formData.append('order', index + 1);

            try {
              // Save original Content-Type from instance defaults
              const originalContentType = this.api.defaults.headers['Content-Type'];

              // Temporarily remove Content-Type to let browser set multipart/form-data
              delete this.api.defaults.headers['Content-Type'];

              const response = await this.api.post(`/content/posts/${repostPostId}/add-attachment/`, formData);

              // Restore original Content-Type
              if (originalContentType) {
                this.api.defaults.headers['Content-Type'] = originalContentType;
              }

              return response.data;
            } catch (error) {
              throw error;
            }
          });

          // Wait for all attachments to be uploaded
          const attachments = await Promise.all(attachmentPromises);

          // Return the repost with attachments - ensure we return the repost data
          const repostData = repostResponse.repost || { id: repostPostId };
          return {
            ...repostData,
            attachments: attachments
          };
        }

        // Return the repost data - extract from the response structure
        return repostResponse.repost || repostResponse;

      } catch (error) {        throw error;
      }
    },

    // Update repost comment - update the repost post itself
    update: async (id, comment) => {
      return this.patch(`/content/posts/${id}/`, {
        comment: comment
      });
    },

    // Delete a repost - delete the repost post
    delete: async (id) => {
      return this.delete(`/content/posts/${id}/`);
    },

    // Check if user has reposted a specific post
    hasReposted: async (postId) => {
      try {
        const reposts = await this.get(`/content/posts/?original_post=${postId}&post_type=repost`);
        return (reposts.results || reposts).length > 0;
      } catch (error) {        return false;
      }
    }
  };

  directShares = {
    // List all direct shares sent by user
    list: async (filters = {}) => {
      const endpoint = this.buildEndpoint('/direct-shares/', filters);
      const response = await this.get(endpoint);
      return response.results || response;
    },

    // Get specific direct share
    get: async (id) => this.get(`/direct-shares/${id}/`),

    // Create a direct share (private share to specific users)
    create: async (postId, recipientIds, note = '') => {
      return this.post('/direct-shares/', {
        post: postId,
        recipient_ids: recipientIds, // Array of user profile IDs
        note: note
      });
    },

    // Update direct share note
    update: async (id, note) => {
      return this.patch(`/direct-shares/${id}/`, {
        note: note
      });
    },

    // Delete a direct share
    delete: async (id) => {
      return this.delete(`/direct-shares/${id}/`);
    },

    // Mark direct share as read (for recipients)
    markAsRead: async (shareId) => {
      return this.post(`/direct-shares/${shareId}/mark_read/`);
    },

    // Get shares received by current user
    received: async () => {
      const response = await this.get('/direct-share-deliveries/');
      return response.results || response;
    },

    // Get unread shares count
    unreadCount: async () => {
      try {
        const deliveries = await this.get('/direct-share-deliveries/?is_read=false');
        return (deliveries.results || deliveries).length;
      } catch (error) {        return 0;
      }
    }
  };

  utils = {
    extractMentions: (content) => {
      const mentionRegex = /@(\w+)/g;
      const mentions = [];
      let match;
      while ((match = mentionRegex.exec(content)) !== null) {
        mentions.push(match[1]);
      }
      return mentions;
    },

    extractHashtags: (content) => {
      const hashtagRegex = /#(\w+)/g;
      const hashtags = [];
      let match;
      while ((match = hashtagRegex.exec(content)) !== null) {
        hashtags.push(match[1]);
      }
      return hashtags;
    },

    // Process mentions in content and create mention records
    processContentMentions: async (content, postId = null, commentId = null, communityId = null) => {
      const mentions = [];
      const usernames = socialAPI.utils.extractMentions(content);

      for (const username of usernames) {
        try {
          // Resolve username to UserProfile ID with community context
          const profileId = await socialAPI.resolveUsername(username, communityId);
          if (!profileId) {            continue;
          }

          const mentionData = {
            mentioned_user: profileId, // Now using UserProfile ID instead of username
            ...(postId && { post: postId }),
            ...(commentId && { comment: commentId })
          };

          const mention = await socialAPI.mentions.create(mentionData);
          mentions.push(mention);
        } catch (err) {        }
      }
      return mentions;
    },

    // Combined social action handler
    handleSocialAction: async (action, targetType, targetId, data = {}) => {
      switch (action) {
        case 'like':
          return await socialAPI.likes.create(targetType, targetId);

        case 'unlike':
          if (targetType === 'post') {
            return await socialAPI.likes.unlikePost(targetId);
          } else {
            return await socialAPI.likes.unlikeComment(targetId);
          }

        case 'dislike':
          return await socialAPI.dislikes.create(targetType, targetId);

        case 'undislike':
          if (targetType === 'post') {
            return await socialAPI.dislikes.undislikePost(targetId);
          } else {
            return await socialAPI.dislikes.undislikeComment(targetId);
          }

        case 'repost':
          if (targetType !== 'post') {
            throw new Error('Can only repost posts, not comments');
          }
          return await socialAPI.reposts.create(targetId, data.comment || '');

        case 'share':
          if (targetType !== 'post') {
            throw new Error('Can only share posts, not comments');
          }
          return await socialAPI.directShares.create(
            targetId,
            data.recipientIds || [],
            data.note || ''
          );

        case 'mention':
          return await socialAPI.mentions.create({
            mentioned_user: data.mentionedUserId,
            post: targetType === 'post' ? targetId : null,
            comment: targetType === 'comment' ? targetId : null
          });

        default:
          throw new Error(`Unknown social action: ${action}`);
      }
    },

    // Batch operation for multiple social actions
    handleBatchSocialActions: async (actions) => {
      const results = [];
      for (const action of actions) {
        try {
          const result = await this.handleSocialAction(
            action.action,
            action.targetType,
            action.targetId,
            action.data
          );
          results.push({ success: true, result, action });
        } catch (error) {
          results.push({ success: false, error: error.message, action });
        }
      }
      return results;
    }
  };
}

export const socialAPI = new SocialAPI();
export default socialAPI;
