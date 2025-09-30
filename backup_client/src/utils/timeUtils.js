/**
 * Time utility functions for formatting timestamps
 */

/**
 * Format a timestamp to show relative time (e.g., "2m", "3h", "1d")
 * @param {Date|string} timestamp - The timestamp to format
 * @returns {string} - Formatted time string
 */
export const formatTimeAgo = (timestamp) => {
  if (!timestamp) return '';

  // Ensure we're parsing the timestamp correctly
  // Django sends ISO format strings like "2025-08-16T04:24:58.331200+00:00"
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);

  // Check if the date is valid
  if (isNaN(date.getTime())) {
    console.warn('Invalid timestamp:', timestamp);
    return '';
  }

  const now = new Date();
  const diffInMinutes = Math.floor((now - date) / (1000 * 60));

  if (diffInMinutes < 1) return 'now';
  if (diffInMinutes < 60) return `${diffInMinutes}m`;
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h`;
  if (diffInMinutes < 43200) return `${Math.floor(diffInMinutes / 1440)}d`;

  // For older posts, show the actual date
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};/**
 * Format a timestamp with more details (includes year for old posts)
 * @param {Date|string} timestamp - The timestamp to format
 * @returns {string} - Formatted time string
 */
export const formatTimeDetailed = (timestamp) => {
  if (!timestamp) return '';

  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  const now = new Date();
  const diffInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

  if (diffInDays < 7) {
    return formatTimeAgo(timestamp);
  } else if (diffInDays < 365) {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }
};

/**
 * Get full date and time for tooltip or detailed display
 * @param {Date|string} timestamp - The timestamp to format
 * @returns {string} - Full formatted date and time
 */
export const formatFullDateTime = (timestamp) => {
  if (!timestamp) return '';

  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });
};
