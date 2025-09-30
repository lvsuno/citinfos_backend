import React from 'react';
import {
  StarIcon,
  QueueListIcon,
  ChatBubbleLeftRightIcon,
  UserIcon,
  ClockIcon,
  HeartIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

/**
 * ThreadCard - Component for displaying thread information
 *
 * Features:
 * - Shows thread creator privileges (pin posts, vote best comments)
 * - Displays thread status (pinned, active, etc.)
 * - Shows post counts and recent activity
 * - Handles different user roles (creator, member, moderator)
 */
const ThreadCard = ({
  thread,
  currentUserId,
  userRole = 'member',
  onThreadClick,
  onPinToggle,
  onManageThread
}) => {
  const isCreator = thread.creator?.id === currentUserId;
  const isPinned = thread.is_pinned;
  const canManage = isCreator || ['moderator', 'admin', 'creator'].includes(userRole);

  const getStatusBadges = () => {
    const badges = [];

    if (isPinned) {
      badges.push(
        <span key="pinned" className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full flex items-center space-x-1">
          <StarIconSolid className="h-3 w-3" />
          <span>Pinned</span>
        </span>
      );
    }

    if (isCreator) {
      badges.push(
        <span key="creator" className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
          Your Thread
        </span>
      );
    }

    if (thread.is_active) {
      badges.push(
        <span key="active" className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
          Active
        </span>
      );
    }

    if (thread.is_closed) {
      badges.push(
        <span key="closed" className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full">
          Closed
        </span>
      );
    }

    return badges;
  };

  const formatTimeAgo = (dateString) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    return 'Just now';
  };

  return (
    <div
      className={`bg-white border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-all ${
        isCreator ? 'border-blue-200 bg-blue-50/30' : 'border-gray-200'
      }`}
      onClick={() => onThreadClick?.(thread.id)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Thread Title and Pinned Icon */}
          <div className="flex items-center space-x-2 mb-1">
            <QueueListIcon className={`h-5 w-5 ${isPinned ? 'text-yellow-600' : 'text-gray-400'}`} />
            <h4 className="font-medium text-gray-900 truncate">{thread.title}</h4>
            {isPinned && <StarIcon className="h-4 w-4 text-yellow-500" title="Pinned by creator" />}
          </div>

          {/* Thread Description */}
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
            {thread.description || thread.body}
          </p>

          {/* Thread Statistics */}
          <div className="flex items-center space-x-4 text-xs text-gray-500 mb-2">
            <div className="flex items-center space-x-1">
              <ChatBubbleLeftRightIcon className="h-3 w-3" />
              <span>{thread.posts_count || 0} posts</span>
            </div>
            <div className="flex items-center space-x-1">
              <UserIcon className="h-3 w-3" />
              <span>{thread.contributors_count || 0} contributors</span>
            </div>
            <div className="flex items-center space-x-1">
              <ClockIcon className="h-3 w-3" />
              <span>{formatTimeAgo(thread.updated_at || thread.created_at)}</span>
            </div>
            <span>Created by @{thread.creator?.username || 'unknown'}</span>
          </div>

          {/* Best Comment Indicator */}
          {thread.best_comment && (
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-xs text-purple-600 flex items-center space-x-1">
                <HeartIcon className="h-3 w-3" />
                <span>💎 Best comment by @{thread.best_comment.author_username}</span>
              </span>
              <span className="text-xs text-gray-400">- voted by thread creator</span>
            </div>
          )}

          {/* Creator Privileges Display */}
          {isCreator && (
            <div className="flex items-center space-x-3 text-xs">
              <span className="text-blue-600 font-medium">As creator, you can:</span>
              <span className="text-green-600 flex items-center space-x-1">
                <StarIcon className="h-3 w-3" />
                <span>Pin posts</span>
              </span>
              <span className="text-purple-600 flex items-center space-x-1">
                <HeartIcon className="h-3 w-3" />
                <span>Vote best comments</span>
              </span>
            </div>
          )}
        </div>

        {/* Status Badges and Actions */}
        <div className="flex flex-col items-end space-y-2 ml-4">
          <div className="flex items-center space-x-2">
            {getStatusBadges()}
          </div>

          {/* Management Button for Creators/Moderators */}
          {canManage && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onManageThread?.(thread.id);
              }}
              className="text-blue-600 hover:text-blue-700 text-xs font-medium px-2 py-1 rounded border border-blue-200 hover:bg-blue-50"
            >
              {isCreator ? 'Manage' : 'Moderate'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ThreadCard;
