import React, { useState } from 'react';
import {
  StarIcon,
  HeartIcon,
  ChatBubbleLeftRightIcon,
  EllipsisHorizontalIcon,
  UserIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import {
  StarIcon as StarIconSolid,
  HeartIcon as HeartIconSolid
} from '@heroicons/react/24/solid';

/**
 * ThreadPostCard - Component for displaying posts within a thread
 *
 * Features:
 * - Shows post content and metadata
 * - Thread creator can pin/unpin posts
 * - Comments with best comment voting by thread creator
 * - Role-based action permissions
 */
const ThreadPostCard = ({
  post,
  thread,
  currentUserId,
  userRole = 'member',
  onPinToggle,
  onMarkBestComment,
  onLike,
  onComment
}) => {
  const [showComments, setShowComments] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const isThreadCreator = thread?.creator?.id === currentUserId;
  const isPostAuthor = post?.author?.id === currentUserId;
  const isPinned = post?.is_pinned;
  const canModerate = ['moderator', 'admin', 'creator'].includes(userRole);

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

  const getPostActions = () => {
    const actions = [];

    // ONLY thread creator can pin/unpin posts in their thread
    if (isThreadCreator) {
      actions.push({
        id: 'pin',
        label: isPinned ? 'Unpin Post' : 'Pin Post',
        icon: isPinned ? StarIconSolid : StarIcon,
        action: () => onPinToggle?.(post.id),
        color: 'text-yellow-600'
      });
    }

    // Moderators and above can delete posts
    if (canModerate || isPostAuthor) {
      actions.push({
        id: 'delete',
        label: 'Delete Post',
        icon: EllipsisHorizontalIcon,
        action: () => console.log('Delete post'),
        color: 'text-red-600'
      });
    }

    return actions;
  };

  const renderComment = (comment, index) => {
    const isBestComment = comment.is_best;
    // ONLY thread creator can mark comments as best in their thread
    const canMarkBest = isThreadCreator && !isBestComment;

    return (
      <div
        key={comment.id || index}
        className={`p-3 rounded-lg border-l-2 ${
          isBestComment
            ? 'border-purple-500 bg-purple-50/50'
            : 'border-gray-200 bg-gray-50'
        }`}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-sm font-medium text-gray-900">
                @{comment.author_username}
              </span>
              {isBestComment && (
                <div className="flex items-center space-x-1">
                  <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full flex items-center space-x-1">
                    <HeartIconSolid className="h-3 w-3" />
                    <span>Best Comment</span>
                  </span>
                  <span className="text-xs text-gray-500">- voted by thread author</span>
                </div>
              )}
              <span className="text-xs text-gray-500">{formatTimeAgo(comment.created_at)}</span>
            </div>
            <p className="text-sm text-gray-700">{comment.content}</p>
            <div className="flex items-center space-x-3 mt-2 text-xs text-gray-500">
              <button className="flex items-center space-x-1 hover:text-blue-600">
                <HeartIcon className="h-3 w-3" />
                <span>{comment.likes_count || 0}</span>
              </button>
              <button className="hover:text-blue-600">Reply</button>
            </div>
          </div>

          {/* ONLY Thread Creator Can Mark Best Comment */}
          {canMarkBest && (
            <button
              onClick={() => onMarkBestComment?.(comment.id)}
              className="text-purple-600 hover:text-purple-700 text-xs font-medium px-2 py-1 rounded border border-purple-200 hover:bg-purple-50"
              title="Mark as best comment (thread author only)"
            >
              💎 Mark Best
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={`bg-white border rounded-lg p-4 ${
      isPinned ? 'border-yellow-300 bg-yellow-50/30' : 'border-gray-200'
    }`}>
      {/* Post Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            <UserIcon className="h-8 w-8 text-gray-400 bg-gray-100 rounded-full p-1" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-medium text-gray-900">@{post.author_username}</span>
              {isPinned && (
                <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full flex items-center space-x-1">
                  <StarIconSolid className="h-3 w-3" />
                  <span>Pinned by creator</span>
                </span>
              )}
              {isThreadCreator && post.author_id === currentUserId && (
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                  Thread Creator
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2 text-xs text-gray-500">
              <ClockIcon className="h-3 w-3" />
              <span>{formatTimeAgo(post.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Post Actions */}
        <div className="relative">
          <button
            onClick={() => setShowActions(!showActions)}
            className="text-gray-400 hover:text-gray-600"
          >
            <EllipsisHorizontalIcon className="h-5 w-5" />
          </button>

          {showActions && (
            <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-10 min-w-[150px]">
              {getPostActions().map((action) => (
                <button
                  key={action.id}
                  onClick={() => {
                    action.action();
                    setShowActions(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center space-x-2 ${action.color}`}
                >
                  <action.icon className="h-4 w-4" />
                  <span>{action.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Post Content */}
      <div className="mb-4">
        <p className="text-gray-800">{post.content}</p>
        {post.media_url && (
          <div className="mt-3">
            <img
              src={post.media_url}
              alt="Post media"
              className="rounded-lg max-w-full h-auto"
            />
          </div>
        )}
      </div>

      {/* Post Engagement */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <button
            onClick={() => onLike?.(post.id)}
            className="flex items-center space-x-1 hover:text-blue-600"
          >
            <HeartIcon className="h-4 w-4" />
            <span>{post.likes_count || 0}</span>
          </button>
          <button
            onClick={() => setShowComments(!showComments)}
            className="flex items-center space-x-1 hover:text-blue-600"
          >
            <ChatBubbleLeftRightIcon className="h-4 w-4" />
            <span>{post.comments_count || 0} comments</span>
          </button>
        </div>

        {/* Thread Author Privileges Notice */}
        {isThreadCreator && (
          <div className="text-xs text-blue-600 font-medium">
            Thread author privileges: Pin posts & vote best comments
          </div>
        )}
      </div>

      {/* Comments Section */}
      {showComments && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="space-y-3">
            {/* Sample Comments */}
            {(post.comments || [
              {
                id: 1,
                author_username: 'user123',
                content: 'Great post! This is very helpful information.',
                likes_count: 5,
                created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
                is_best: false
              },
              {
                id: 2,
                author_username: 'expert_user',
                content: 'I completely agree with this approach. I\'ve been using similar techniques for years and they work really well.',
                likes_count: 12,
                created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
                is_best: true
              }
            ]).map(renderComment)}
          </div>

          {/* Add Comment */}
          <div className="mt-4 pt-3 border-t border-gray-100">
            <div className="flex space-x-3">
              <UserIcon className="h-6 w-6 text-gray-400 bg-gray-100 rounded-full p-1 flex-shrink-0" />
              <div className="flex-1">
                <textarea
                  placeholder="Add a comment..."
                  className="w-full p-2 border border-gray-200 rounded-lg text-sm resize-none"
                  rows={2}
                />
                <div className="flex justify-end mt-2">
                  <button className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                    Comment
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThreadPostCard;
