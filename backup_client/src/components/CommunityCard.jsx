import React from 'react';
import { Link } from 'react-router-dom';
import {
  UserGroupIcon,
  GlobeAltIcon,
  LockClosedIcon,
  ShieldCheckIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  EyeIcon,
  CheckCircleIcon,
  StarIcon,
  ShieldExclamationIcon,
  QueueListIcon
} from '@heroicons/react/24/outline';
import { DEFAULT_COVER_IMAGE, DEFAULT_AVATAR_IMAGE } from '../constants/defaultImages';

/**
 * CommunityCard - A highly customizable component for displaying community information
 *
 * @param {Object} community - Community data object
 * @param {string} community.id - Community ID
 * @param {string} community.name - Community name
 * @param {string} community.slug - Community URL slug
 * @param {string} community.description - Community description
 * @param {string} community.community_type - 'public', 'private', 'restricted'
 * @param {string} community.cover_media - Cover image/video URL
 * @param {string} community.cover_media_type - 'image' or 'video'
 * @param {string} community.avatar - Community avatar URL
 * @param {number} community.membership_count - Number of members
 * @param {number} community.posts_count - Number of posts
 * @param {number} community.threads_count - Number of threads
 * @param {boolean} community.user_is_member - Whether current user is a member
 * @param {string} community.user_role - User's role in community ('member', 'moderator', 'admin', 'creator')
 * @param {Array} community.tags - Community tags
 * @param {string} community.category - Community category
 * @param {boolean} community.is_featured - Whether community is featured
 * @param {string} community.created_at - Creation date
 * @param {Object} options - Display options
 * @param {string} options.variant - 'grid', 'list', 'compact'
 * @param {boolean} options.showStats - Show statistics (default: true)
 * @param {boolean} options.showDescription - Show description (default: true)
 * @param {boolean} options.showTags - Show tags (default: true)
 * @param {boolean} options.showActions - Show action buttons (default: true)
 * @param {boolean} options.showMembershipBadge - Show membership badge (default: true)
 * @param {boolean} options.clickable - Make entire card clickable (default: false)
 * @param {Function} onJoin - Callback when join button is clicked
 * @param {Function} onLeave - Callback when leave button is clicked
 * @param {boolean} isLoading - Whether join/leave is in progress
 * @param {string} className - Additional CSS classes
 */
const CommunityCard = ({
  community,
  options = {},
  onJoin,
  onLeave,
  isLoading = false,
  className = ''
}) => {
  const {
    variant = 'grid',
    showStats = true,
    showDescription = true,
    showTags = true,
    showActions = true,
    showMembershipBadge = true,
    clickable = false
  } = options;

  // Determine if user can see media based on community type and membership
  const canViewMedia = () => {
    if (community.community_type === 'public') return true;
    return community.user_is_member;
  };

  // Default images for when access is restricted
  const getDefaultCover = () => DEFAULT_COVER_IMAGE;
  const getDefaultAvatar = () => DEFAULT_AVATAR_IMAGE;

  // Privacy icons mapping
  const getPrivacyIcon = (type) => {
    const iconClass = "h-4 w-4 text-white";
    switch (type) {
      case 'public':
        return <GlobeAltIcon className={iconClass} />;
      case 'private':
        return <LockClosedIcon className={iconClass} />;
      case 'restricted':
        return <ShieldCheckIcon className={iconClass} />;
      default:
        return <GlobeAltIcon className={iconClass} />;
    }
  };

  // Membership role icons
  const getMembershipIcon = (isMember, role) => {
    if (!isMember) return null;

    const baseClass = "flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium text-white";
    switch (role) {
      case 'creator':
        return (
          <div className={`${baseClass} bg-yellow-500`}>
            <StarIcon className="h-3 w-3" />
            <span>Creator</span>
          </div>
        );
      case 'admin':
        return (
          <div className={`${baseClass} bg-red-500`}>
            <ShieldExclamationIcon className="h-3 w-3" />
            <span>Admin</span>
          </div>
        );
      case 'moderator':
        return (
          <div className={`${baseClass} bg-purple-500`}>
            <ShieldCheckIcon className="h-3 w-3" />
            <span>Moderator</span>
          </div>
        );
      case 'member':
      default:
        return (
          <div className={`${baseClass} bg-green-500`}>
            <CheckCircleIcon className="h-3 w-3" />
          </div>
        );
    }
  };

  // Get cover image style
  const getCommunityHeaderImage = (community) => {
    const canAccess = canViewMedia();

    if (canAccess && community.cover_media && community.cover_media.trim() !== '') {
      return {
        backgroundImage: `url(${community.cover_media})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      };
    }

    // Use default cover when access is restricted or no cover exists
    if (!canAccess) {
      return {
        backgroundImage: `url(${getDefaultCover()})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      };
    }

    // Fallback gradient based on community type
    const gradients = {
      public: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      private: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      restricted: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
    };

    return {
      background: gradients[community.community_type] || gradients.public
    };
  };

  // Handle join/leave actions
  const handleJoinClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (onJoin && !isLoading) {
      onJoin(community.slug);
    }
  };

  const handleLeaveClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (onLeave && !isLoading) {
      onLeave(community.slug);
    }
  };

  // Format numbers
  const formatCount = (count) => {
    if (!count) return '0';
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
    if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
    return count.toLocaleString();
  };

  // Card content based on variant
  const renderCard = () => {
    if (variant === 'compact') {
      return (
        <div className="flex items-center space-x-4 p-4">
          {/* Avatar */}
          <div className="flex-shrink-0">
            {community.avatar ? (
              <img
                src={community.avatar}
                alt={community.name}
                className="h-12 w-12 rounded-full object-cover"
              />
            ) : (
              <div className="h-12 w-12 rounded-full bg-gray-300 flex items-center justify-center">
                <UserGroupIcon className="h-6 w-6 text-gray-600" />
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-semibold text-gray-900 truncate">{community.name}</h3>
              {showMembershipBadge && getMembershipIcon(community.user_is_member, community.user_role)}
              {community.is_featured && <StarIcon className="h-4 w-4 text-yellow-500" />}
            </div>
            {showStats && (
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>{formatCount(community.membership_count)}</span>
                <span>{formatCount(community.posts_count)} posts</span>
              </div>
            )}
          </div>

          {/* Privacy indicator */}
          <div className="flex-shrink-0">
            {getPrivacyIcon(community.community_type)}
          </div>
        </div>
      );
    }

    if (variant === 'list') {
      return (
        <div className="flex items-start space-x-4 p-6">
          {/* Avatar */}
          <div className="flex-shrink-0">
            {canViewMedia() && community.avatar ? (
              <img
                src={community.avatar}
                alt={community.name}
                className="h-16 w-16 rounded-lg object-cover"
                onError={(e) => {
                  e.target.src = getDefaultAvatar();
                }}
              />
            ) : (
              <img
                src={getDefaultAvatar()}
                alt={community.name}
                className="h-16 w-16 rounded-lg object-cover"
                onError={(e) => {
                  // If default avatar fails, show icon fallback
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
            )}
            <div className="h-16 w-16 rounded-lg bg-gray-300 flex items-center justify-center" style={{display: 'none'}}>
              <UserGroupIcon className="h-8 w-8 text-gray-600" />
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-semibold text-gray-900">{community.name}</h3>
                {showMembershipBadge && getMembershipIcon(community.user_is_member, community.user_role)}
                {community.is_featured && <StarIcon className="h-5 w-5 text-yellow-500" />}
                <div className="bg-black bg-opacity-20 rounded-full p-1">
                  {getPrivacyIcon(community.community_type)}
                </div>
              </div>

              {/* Action Buttons - Only show for non-members */}
              {showActions && !community.user_is_member && (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleJoinClick}
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
                    disabled={isLoading}
                  >
                    {isLoading ? 'Joining...' : (community.community_type === 'public' ? 'Join' : 'Request')}
                  </button>
                  <Link
                    to={`/c/${community.slug}`}
                    className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-50 transition-colors"
                  >
                    <EyeIcon className="h-4 w-4" />
                  </Link>
                </div>
              )}
            </div>

            {showDescription && community.description && (
              <p className="text-gray-600 text-sm mt-2 line-clamp-2">{community.description}</p>
            )}

            {showTags && community.tags && community.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {community.tags.slice(0, 3).map((tag, index) => (
                  <span key={index} className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
                    {tag}
                  </span>
                ))}
                {community.tags.length > 3 && (
                  <span className="text-xs text-gray-500">+{community.tags.length - 3} more</span>
                )}
              </div>
            )}

            {showStats && (
              <div className="flex items-center space-x-6 text-sm text-gray-500 mt-3">
                <span className="flex items-center space-x-1">
                  <UserGroupIcon className="h-4 w-4" />
                  <span>{formatCount(community.membership_count)}</span>
                </span>
                <span className="flex items-center space-x-1">
                  <DocumentTextIcon className="h-4 w-4" />
                  <span>{formatCount(community.posts_count)} posts</span>
                </span>
                {community.threads_count !== undefined && (
                  <span className="flex items-center space-x-1">
                    <QueueListIcon className="h-4 w-4" />
                    <span>{formatCount(community.threads_count)} threads</span>
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      );
    }

    // Default grid variant
    return (
      <>
        {/* Community Cover/Header */}
        <div
          className="h-32 relative"
          style={getCommunityHeaderImage(community)}
        >
          {/* Restriction overlay for non-members of private/restricted communities */}
          {!canViewMedia() && (
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
              <div className="text-center text-white">
                <div className="text-lg mb-1">🔒</div>
                <div className="text-xs font-medium">Join to view</div>
              </div>
            </div>
          )}

          {/* Membership Badge Overlay */}
          {showMembershipBadge && community.user_is_member && (
            <div className="absolute top-3 right-3">
              {getMembershipIcon(community.user_is_member, community.user_role)}
            </div>
          )}

          {/* Featured Badge */}
          {community.is_featured && (
            <div className="absolute top-3 left-3 bg-yellow-500 rounded-full p-1">
              <StarIcon className="h-4 w-4 text-white" />
            </div>
          )}

          {/* Privacy Level Badge */}
          <div className="absolute bottom-3 left-3 bg-black bg-opacity-50 rounded-full p-1">
            {getPrivacyIcon(community.community_type)}
          </div>
        </div>

        {/* Community Info */}
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <h3 className="text-lg font-semibold text-gray-900 truncate">{community.name}</h3>
              </div>
              {community.category && (
                <span className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
                  {community.category}
                </span>
              )}
            </div>
          </div>

          {showDescription && community.description && (
            <p className="text-gray-600 text-sm mb-4 line-clamp-3">{community.description}</p>
          )}

          {showTags && community.tags && community.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-4">
              {community.tags.slice(0, 3).map((tag, index) => (
                <span key={index} className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                  {tag}
                </span>
              ))}
              {community.tags.length > 3 && (
                <span className="text-xs text-gray-500">+{community.tags.length - 3}</span>
              )}
            </div>
          )}

          {/* Community Stats */}
          {showStats && (
            <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
              <span className="flex items-center space-x-1">
                <UserGroupIcon className="h-4 w-4" />
                <span>{formatCount(community.membership_count)}</span>
              </span>
              <span className="flex items-center space-x-1">
                <DocumentTextIcon className="h-4 w-4" />
                <span>{formatCount(community.posts_count)} posts</span>
              </span>
              {community.threads_count !== undefined && (
                <span className="flex items-center space-x-1">
                  <QueueListIcon className="h-4 w-4" />
                  <span>{formatCount(community.threads_count)} threads</span>
                </span>
              )}
            </div>
          )}

          {/* Action Buttons - Only show for non-members */}
          {showActions && !community.user_is_member && (
            <div className="flex items-center space-x-2">
              <button
                onClick={handleJoinClick}
                className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
                disabled={isLoading}
              >
                {isLoading ? 'Joining...' : (community.community_type === 'public' ? 'Join' : 'Request to Join')}
              </button>
              <Link
                to={`/c/${community.slug}`}
                className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-50 transition-colors"
              >
                Visit
              </Link>
            </div>
          )}
        </div>
      </>
    );
  };

  // Determine if card should be clickable (only for members)
  const isCardClickable = clickable || community.user_is_member;

  // Wrapper classes based on variant
  const getWrapperClasses = () => {
    const baseClasses = `bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow ${className}`;

    if (isCardClickable) {
      return `${baseClasses} cursor-pointer`;
    }

    return baseClasses;
  };

  const CardWrapper = isCardClickable ?
    ({ children }) => (
      <Link to={`/c/${community.slug}`} className={getWrapperClasses()}>
        {children}
      </Link>
    ) :
    ({ children }) => (
      <div className={getWrapperClasses()}>
        {children}
      </div>
    );

  return (
    <CardWrapper>
      {renderCard()}
    </CardWrapper>
  );
};

export default CommunityCard;
