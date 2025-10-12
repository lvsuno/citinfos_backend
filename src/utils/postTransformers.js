/**
 * Post Data Transformers
 *
 * Transform post data between modal format (frontend UI) and API format (backend).
 *
 * Architecture:
 * - Article posts: content = HTML string, can have embedded attachments
 * - Poll posts: content = optional text, must have polls array attached
 * - Media posts: content = optional description, must have attachments array
 *
 * Each tab creates a SEPARATE post type, never mixed together.
 */

/**
 * Transform article post data to API format
 * @param {Object} modalData - Data from PostCreationModal
 * @returns {Object} API-ready post data
 */
export const transformArticlePostForAPI = (modalData) => {
  return {
    content: modalData.content.article || '',  // HTML string
    post_type: 'text',
    visibility: modalData.visibility,
    // Note: Embedded media will be handled separately via two-phase upload
    // attachments: [] will be added after media upload in phase 2
  };
};

/**
 * Transform poll post data to API format
 * @param {Object} modalData - Data from PostCreationModal
 * @returns {Object} API-ready post data
 */
export const transformPollPostForAPI = (modalData) => {
  const poll = modalData.content.poll;

  if (!poll || !poll.question || !poll.options?.length) {
    throw new Error('Poll must have a question and at least one option');
  }

  // Calculate expiration datetime
  const expiresAt = new Date(
    Date.now() + (poll.expirationHours || 24) * 60 * 60 * 1000
  ).toISOString();

  return {
    content: poll.question,  // Question as content
    post_type: 'poll',
    visibility: modalData.visibility,
    polls: [{
      question: poll.question,
      options: poll.options
        .filter(opt => opt.trim())  // Remove empty options
        .map((text, index) => ({
          text: text.trim(),
          order: index + 1
        })),
      multiple_choice: poll.allowMultiple || false,
      anonymous_voting: poll.anonymousVoting || false,
      expires_at: expiresAt
    }]
  };
};

/**
 * Transform media post data to API format
 * @param {Object} modalData - Data from PostCreationModal
 * @returns {Object} API-ready post data
 */
export const transformMediaPostForAPI = (modalData) => {
  const media = modalData.content.media;

  if (!media || media.length === 0) {
    throw new Error('Media post must have at least one media item');
  }

  // Use global description or first media description as content
  const globalDescription = modalData.content.mediaDescription || '';
  const content = globalDescription || media[0]?.description || '';

  // Determine post_type based on first media item
  const firstMediaType = media[0].type;
  let postType = 'mixed'; // Default fallback

  if (firstMediaType === 'image') postType = 'image';
  else if (firstMediaType === 'video') postType = 'video';
  else if (firstMediaType === 'audio') postType = 'audio';
  else if (firstMediaType === 'file') postType = 'file';

  return {
    content: content,
    post_type: postType,
    visibility: modalData.visibility,
    attachments: media.map((item, index) => ({
      media_type: item.type,
      file: item.file,
      description: item.description || '',
      order: index + 1
    }))
  };
};

/**
 * Main transformer - routes to appropriate type-specific transformer
 * @param {Object} modalData - Data from PostCreationModal
 * @returns {Object} API-ready post data
 */
export const transformPostDataForAPI = (modalData) => {
  if (!modalData.type) {
    throw new Error('Post type is required');
  }

  // Add common fields that apply to all types
  const baseData = {
    visibility: modalData.visibility || 'public',
  };

  // Add community and thread IDs if provided
  if (modalData.community_id) {
    baseData.community_id = modalData.community_id;
  }
  if (modalData.thread_id) {
    baseData.thread_id = modalData.thread_id;
  }

  // Route to appropriate transformer based on post type
  let transformedData;

  switch (modalData.type) {
    case 'article':
      transformedData = transformArticlePostForAPI(modalData);
      break;

    case 'poll':
      transformedData = transformPollPostForAPI(modalData);
      break;

    case 'media':
      transformedData = transformMediaPostForAPI(modalData);
      break;

    default:
      throw new Error(`Unsupported post type: ${modalData.type}`);
  }

  // Merge base data with transformed data
  return {
    ...transformedData,
    ...baseData,
  };
};

/**
 * Transform article update data for Phase 3 (after media upload)
 * Used to update article content with real media URLs after upload
 * @param {string} processedContent - HTML content with server URLs
 * @returns {Object} API-ready update data
 */
export const transformArticleUpdateForAPI = (processedContent) => {
  return {
    content: processedContent  // Simple string, not nested
  };
};

/**
 * Add uploaded media attachments to article post (Phase 2)
 * @param {string} postId - ID of the created post
 * @param {Array} uploadedMedia - Array of uploaded media with URLs
 * @returns {Object} API-ready attachments data
 */
export const createArticleMediaAttachments = (uploadedMedia) => {
  return {
    attachments: uploadedMedia.map((media, index) => ({
      media_type: media.type,
      file: media.url,  // Server URL from upload
      description: media.description || '',
      order: index + 1
    }))
  };
};

/**
 * Validate modal data before transformation
 * @param {Object} modalData - Data from PostCreationModal
 * @returns {Object} Validation result { valid: boolean, errors: string[] }
 */
export const validatePostData = (modalData) => {
  const errors = [];

  if (!modalData.type) {
    errors.push('Post type is required');
  }

  // Type-specific validation
  switch (modalData.type) {
    case 'article':
      if (!modalData.content?.article || modalData.content.article.trim() === '') {
        errors.push('Article content cannot be empty');
      }
      break;

    case 'poll':
      if (!modalData.content?.poll?.question) {
        errors.push('Poll question is required');
      }
      if (!modalData.content?.poll?.options || modalData.content.poll.options.filter(o => o.trim()).length < 2) {
        errors.push('Poll must have at least 2 options');
      }
      break;

    case 'media':
      if (!modalData.content?.media || modalData.content.media.length === 0) {
        errors.push('Media post must have at least one media item');
      }
      break;
  }

  return {
    valid: errors.length === 0,
    errors
  };
};
