/**
 * Media URL utilities for handling Django media file URLs
 */

// Get server URL from environment configuration
const getServerUrl = () => {
  return import.meta.env.VITE_SERVER_URL || 'http://localhost:8000';
};

/**
 * Constructs a full media URL from a relative media path
 * Handles cases where the server returns paths like "/media/covers/file.mp4"
 * Simply concatenates SERVER_URL + mediaPath
 *
 * @param {string} mediaPath - The media path from the server (e.g., "/media/covers/file.mp4")
 * @returns {string} - Full URL to the media file
 */
export const getMediaUrl = (mediaPath) => {
  if (!mediaPath) return '';

  // If it's already a full URL (http/https) or blob URL, return as-is
  if (mediaPath.startsWith('http') || mediaPath.startsWith('blob:')) {
    return mediaPath;
  }

  // Get server URL from environment configuration
  const serverUrl = getServerUrl();

  // Server returns paths like "/media/covers/file.mp4"
  // Just concatenate server URL + path (no additional processing needed)
  return `${serverUrl}${mediaPath}`;
};

/**
 * Gets the full URL for a user's profile picture
 *
 * @param {string} profilePicturePath - Profile picture path from user data
 * @returns {string} - Full URL or empty string if no picture
 */
export const getProfilePictureUrl = (profilePicturePath) => {
  return getMediaUrl(profilePicturePath);
};

/**
 * Gets the full URL for a user's cover media
 *
 * @param {string} coverMediaPath - Cover media path from user data
 * @returns {string} - Full URL or empty string if no cover
 */
export const getCoverMediaUrl = (coverMediaPath) => {
  return getMediaUrl(coverMediaPath);
};

/**
 * Checks if a media path represents an image file
 *
 * @param {string} mediaPath - The media file path
 * @returns {boolean} - True if it's an image file
 */
export const isImageFile = (mediaPath) => {
  if (!mediaPath) return false;

  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'];
  const extension = mediaPath.toLowerCase().split('.').pop();
  return imageExtensions.includes(`.${extension}`);
};

/**
 * Checks if a media path represents a video file
 *
 * @param {string} mediaPath - The media file path
 * @returns {boolean} - True if it's a video file
 */
export const isVideoFile = (mediaPath) => {
  if (!mediaPath) return false;

  const videoExtensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'];
  const extension = mediaPath.toLowerCase().split('.').pop();
  return videoExtensions.includes(`.${extension}`);
};

/**
 * Gets the file extension from a media path
 *
 * @param {string} mediaPath - The media file path
 * @returns {string} - File extension (with dot) or empty string
 */
export const getFileExtension = (mediaPath) => {
  if (!mediaPath) return '';

  const parts = mediaPath.split('.');
  return parts.length > 1 ? `.${parts.pop().toLowerCase()}` : '';
};

export default {
  getMediaUrl,
  getProfilePictureUrl,
  getCoverMediaUrl,
  isImageFile,
  isVideoFile,
  getFileExtension
};
