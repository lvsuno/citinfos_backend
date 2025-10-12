import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

/**
 * ClickableAuthorName - Renders clickable author names in posts
 *
 * For current user: Shows "You" and links to /profile
 * For other users: Shows username and links to /users/:userId
 *
 * @param {Object} author - Author object with id/username
 * @param {string} authorUsername - Fallback username if author is just UUID
 * @param {string} className - Additional CSS classes
 */
const ClickableAuthorName = ({
  author,
  authorUsername,
  className = "text-sm font-semibold text-gray-900 hover:text-blue-600 transition-colors"
}) => {
  const { user: currentUser } = useAuth();

  // Helper function to get display name
  const getDisplayName = () => {
    // Check if this is the current user
    const getCurrentUserProfileId = () => currentUser?.profile?.id;
    const isCurrentUser = getCurrentUserProfileId() === (
      typeof author === 'string' ? author : author?.id
    );

    if (isCurrentUser) return 'You';

    // Use provided username or extract from author object
    if (authorUsername) return authorUsername;
    if (typeof author === 'object' && author?.username) return author.username;

    return 'Unknown User';
  };

  // Helper function to get profile link
  const getProfileLink = () => {
    // Check if this is the current user
    const getCurrentUserProfileId = () => currentUser?.profile?.id;
    const authorId = typeof author === 'string' ? author : author?.id;
    const isCurrentUser = getCurrentUserProfileId() === authorId;

    if (isCurrentUser) return '/profile';
    if (authorId) return `/users/${authorId}`;

    return null; // No link for unknown users
  };

  const displayName = getDisplayName();
  const profileLink = getProfileLink();

  // If no valid link, render as plain text
  if (!profileLink) {
    return <span className={className}>{displayName}</span>;
  }

  // Render as clickable link
  return (
    <Link to={profileLink} className={className}>
      {displayName}
    </Link>
  );
};

export default ClickableAuthorName;
