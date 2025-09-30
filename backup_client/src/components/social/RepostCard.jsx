import React, { useState, useRef } from 'react';
import { ArrowPathIcon, ClockIcon } from '@heroicons/react/24/outline';
import { ChatBubbleLeftRightIcon, ShareIcon, HandThumbUpIcon as HandThumbUpSolid, HandThumbDownIcon as HandThumbDownSolid } from '@heroicons/react/24/solid';
import { HandThumbUpIcon as HandThumbUpOutline, HandThumbDownIcon as HandThumbDownOutline } from '@heroicons/react/24/outline';
import { ArrowPathRoundedSquareIcon } from '@heroicons/react/24/outline';
import PostCard from './PostCard';
import PostContentRenderer from './PostContentRenderer';
import AttachmentDisplay from './AttachmentDisplay';
import PollDisplay from './PollDisplay';
import PostActionBar from './PostActionBar';
import InlineRepostComposer from './InlineRepostComposer';
import usePostInteractions from './usePostInteractions';
import { useJWTAuth } from '../../hooks/useJWTAuth';
import { useNavigate } from 'react-router-dom';
import ClickableAuthorName from '../ui/ClickableAuthorName';
import { formatTimeAgo, formatFullDateTime } from '../../utils/timeUtils';
import UserBadgeList from '../UserBadgeList';
import TinyBadgeList from '../TinyBadgeList';

/**
 * RepostCard - Reusable component for displaying reposts across the app
 *
 * Displays reposts as independent posts with embedded original content:
 * - Repost acts like a normal post with its own interactions
 * - Original post is displayed read-only for reference
 * - Correct username display for both reposter and original author
 *
 * @param {Object} repostData - The repost data from feed API
 * @param {Object} repostData.reposted_by - User who made the repost
 * @param {string} repostData.repost_comment - Comment added by reposter
 * @param {Object} repostData.data - Original post data
 * @param {string} repostData.created_at - When the repost was created
 * @param {Function} onPostUpdate - Callback for post updates
 * @param {Function} onPostDelete - Callback for post deletion
 */
const RepostCard = ({
  repostData,
  onPostUpdate,
  onPostDelete
}) => {
  const { user, isAuthenticated } = useJWTAuth();
  const navigate = useNavigate();

  if (!repostData || !repostData.data) {
    return null;
  }

  const {
    repost_id,
    reposted_by,
    repost_comment,
    created_at,
    data: originalPost,
    likes_count = 0,
    dislikes_count = 0,
    comments_count = 0,
    shares_count = 0,
    repost_count = 0,
    is_liked = false,
    is_disliked = false,
    visibility = 'public'
  } = repostData;

  const [showComments, setShowComments] = useState(false);
  const [showInlineRepost, setShowInlineRepost] = useState(false);

  // Ref for auto-scrolling to repost composer
  const repostComposerRef = useRef(null);

  // Create a repost post object for interactions
  const repostAsPost = {
    id: repost_id,
    author: reposted_by,
    content: repost_comment || '',
    created_at: created_at,
    likes_count,
    dislikes_count,
    comments_count,
    shares_count,
    repost_count,
    is_liked,
    is_disliked,
    visibility,
    type: 'repost'
  };

  const { postState, toggleReaction, addComment, share, repost, isLoading, error } = usePostInteractions(repostAsPost);

  // Handle repost button click - show inline composer
  const handleRepost = () => {
    setShowInlineRepost(true);

    // Scroll to the repost composer after it renders
    setTimeout(() => {
      if (repostComposerRef.current) {
        repostComposerRef.current.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }
    }, 100);
  };

  // Handle successful repost creation from inline composer
  const handleRepostSuccess = (repostData) => {
    setShowInlineRepost(false);

    // Navigate to the user's profile where they can see and manage their repost
    // Add a slight delay to ensure the repost appears in the feed
    setTimeout(() => {
      if (user?.username) {
        navigate(`/profile/${user.username}`, {
          state: { scrollToPost: repostData.id }
        });
      }
    }, 1000);
  };

  // Handle repost cancel
  const handleRepostCancel = () => {
    setShowInlineRepost(false);
  };

  const repostDate = new Date(created_at);

  const visibilityLabel = visibility === 'public' ? '🌍 Public' :
                         visibility === 'followers' ? '👥 Followers' :
                         visibility === 'custom' ? '🎯 Custom' : '';

  const canEdit = isAuthenticated && user?.profile?.id === reposted_by?.id;
  const canDelete = canEdit;

  // Helper function to display username consistently with PostCard
  const displayUsername = (authorData, authorUsername, isCurrentUser = false) => {
    if (isCurrentUser) return 'You';

    // Use author_username field if available, otherwise fall back to object structure
    if (authorUsername) return authorUsername;

    // Handle different author data structures
    if (typeof authorData === 'string') {
      // If author is just a UUID string, we can't show username
      return 'Unknown User';
    }

    // If author is an object with username
    return authorData?.username || 'Unknown User';
  };

  // Helper function to get author username for avatar
  const getAuthorUsername = (authorData, authorUsername) => {
    // Use author_username field if available
    if (authorUsername) return authorUsername;

    if (typeof authorData === 'string') {
      return 'U'; // Default if only UUID
    }
    return authorData?.username || 'U';
  };

  // Check if user is current user - need to handle both UUID strings and objects
  const getCurrentUserProfileId = () => user?.profile?.id;

  const isRepostByCurrentUser = getCurrentUserProfileId() === reposted_by?.id;
  const isOriginalByCurrentUser = getCurrentUserProfileId() === (
    typeof originalPost?.author === 'string' ? originalPost?.author : originalPost?.author?.id
  );

  const handleEdit = () => {
    // TODO: Implement repost editing functionality
  };

  const handleDelete = () => {
    if (onPostDelete) {
      onPostDelete(repost_id);
    }
  };

  return (
    <>
      {/* Inline Repost Composer - appears as a new post at the top */}
      {showInlineRepost && (
        <div ref={repostComposerRef} className="mb-4 animate-in fade-in duration-200">
          <InlineRepostComposer
            originalPost={repostAsPost}
            onCancel={handleRepostCancel}
            onRepost={handleRepostSuccess}
          />
        </div>
      )}

      <div className="bg-white rounded-lg shadow border border-gray-100 p-4 relative">
      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-white/70 backdrop-blur-sm rounded-lg flex items-center justify-center z-10">
          <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-full shadow-lg">
            <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            <span className="text-sm text-gray-600">Processing...</span>
          </div>
        </div>
      )}

      {/* Error notification */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500 flex-shrink-0"></div>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Repost Header */}
      <div className="flex items-start gap-3">
        {/* Reposter Avatar - Same style as PostCard */}
        <div className="h-9 w-9 rounded-full bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center text-white text-xs font-semibold">
          {getAuthorUsername(reposted_by, reposted_by?.username).charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <div className="flex items-center gap-2 text-sm">
                <ClickableAuthorName
                  author={reposted_by}
                  authorUsername={reposted_by?.username}
                  className="font-semibold text-gray-900 hover:text-blue-600 transition-colors"
                />
                {visibilityLabel && (
                  <span className="text-[10px] font-normal text-gray-500">{visibilityLabel}</span>
                )}
                <span className="text-gray-400">•</span>
                <span
                  className="text-gray-500 text-sm cursor-help"
                  title={formatFullDateTime(created_at)}
                >
                  {formatTimeAgo(repostDate)}
                </span>
              </div>
              {reposted_by && (
                <TinyBadgeList
                  userId={reposted_by.id || reposted_by}
                  maxVisible={3}
                />
              )}
            </div>

            {/* Edit/Delete buttons for repost owner */}
            <div className="flex items-center gap-2">
              {canEdit && (
                <button
                  onClick={handleEdit}
                  className="text-[10px] px-2 py-0.5 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-600"
                >
                  Edit
                </button>
              )}
              {canDelete && (
                <button
                  onClick={handleDelete}
                  className="text-[10px] px-2 py-0.5 rounded-md bg-red-50 hover:bg-red-100 text-red-600"
                >
                  Delete
                </button>
              )}
            </div>
          </div>

          {/* Repost Comment */}
          {repost_comment && (
            <div className="mt-2">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                <PostContentRenderer text={repost_comment} mentions={repostData?.mentions || {}} />
              </p>
            </div>
          )}

          {/* Original Post - Read-only Display */}
          <div className="mt-4 border border-gray-200 rounded-lg overflow-hidden">
            <div className="p-4">
              {/* Original Post Header */}
              <div className="flex items-start gap-3 mb-3">
                {/* Original Author Avatar - Same style as normal PostCard */}
                <div className="h-9 w-9 rounded-full bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center text-white text-xs font-semibold">
                  {getAuthorUsername(originalPost?.author, originalPost?.author_username).charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex flex-col">
                    <div className="flex items-center gap-2">
                      <ClickableAuthorName
                        author={originalPost?.author}
                        authorUsername={originalPost?.author_username}
                        className="text-sm font-semibold text-gray-900 hover:text-blue-600 transition-colors"
                      />
                      <span className="text-gray-400">•</span>
                      <span
                        className="text-gray-500 text-sm cursor-help"
                        title={formatFullDateTime(originalPost?.created_at)}
                      >
                        {formatTimeAgo(new Date(originalPost?.created_at))}
                      </span>
                    </div>
                    {originalPost?.author && (
                      <TinyBadgeList
                        userId={originalPost.author.id || originalPost.author}
                        maxVisible={3}
                      />
                    )}
                  </div>
                </div>
              </div>

              {/* Original Post Content */}
              {originalPost?.content && (
                <div className="mb-3">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    <PostContentRenderer text={originalPost.content} mentions={originalPost?.mentions || {}} />
                  </p>
                </div>
              )}

              {/* Original Post Attachments */}
              {originalPost?.attachments && originalPost.attachments.length > 0 && (
                <div className="mb-3">
                  <AttachmentDisplay
                    attachments={originalPost.attachments}
                    readonly={true}
                  />
                </div>
              )}

              {/* Original Post Polls */}
              {originalPost?.polls && originalPost.polls.length > 0 && (
                <div className="mb-3">
                  {originalPost.polls.map((poll, index) => (
                    <PollDisplay
                      key={poll.id || index}
                      poll={poll}
                      readonly={true}
                    />
                  ))}
                </div>
              )}

              {/* Original Post Stats - Read-only */}
              <div className="flex items-center gap-4 text-xs text-gray-500 pt-2 border-t border-gray-100">
                <span className="flex items-center gap-1">
                  <HandThumbUpOutline className="h-3 w-3" />
                  {originalPost?.likes_count || 0}
                </span>
                <span className="flex items-center gap-1">
                  <HandThumbDownOutline className="h-3 w-3" />
                  {originalPost?.dislikes_count || 0}
                </span>
                <span className="flex items-center gap-1">
                  <ChatBubbleLeftRightIcon className="h-3 w-3" />
                  {originalPost?.comments_count || 0}
                </span>
                <span className="flex items-center gap-1">
                  <ShareIcon className="h-3 w-3" />
                  {originalPost?.shares_count || 0}
                </span>
                <span className="flex items-center gap-1">
                  <ArrowPathRoundedSquareIcon className="h-3 w-3" />
                  {originalPost?.repost_count || 0}
                </span>
              </div>
            </div>
          </div>

          {/* Repost Action Bar */}
          <div className="mt-4">
            <PostActionBar
              post={postState}
              onToggleReaction={toggleReaction}
              onShare={share}
              onRepost={handleRepost}
              onComment={() => setShowComments(!showComments)}
              showComments={showComments}
              isLoading={isLoading}
            />
          </div>

          {/* Repost Comments */}
          {showComments && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              {/* TODO: Implement comment thread for reposts */}
              <p className="text-sm text-gray-500">Comments for reposts coming soon...</p>
            </div>
          )}
        </div>
      </div>
    </div>
    </>
  );
};

export default RepostCard;

/**
 * Usage Examples:
 *
 * Basic usage in a feed:
 * <RepostCard
 *   repostData={feedItem}
 *   onPostUpdate={handleUpdate}
 *   onPostDelete={handleDelete}
 * />
 *
 * With custom styling:
 * <RepostCard
 *   repostData={feedItem}
 *   className="mb-6"
 *   onPostUpdate={handleUpdate}
 * />
 *
 * Expected repostData structure from API:
 * {
 *   type: "repost",
 *   repost_id: "uuid",
 *   reposted_by: { id, username, display_name },
 *   repost_comment: "optional comment",
 *   created_at: "2025-08-15T12:42:51.233703+00:00",
 *   data: { // original post object
 *     id: "uuid",
 *     content: "original post content",
 *     author: "uuid",
 *     // ... other post fields
 *   }
 * }
 */
