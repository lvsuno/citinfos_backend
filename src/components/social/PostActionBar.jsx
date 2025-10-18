import React, { useState, useRef } from 'react';
import { ChatBubbleLeftRightIcon, ShareIcon } from '@heroicons/react/24/outline';
import { HandThumbUpIcon as HandThumbUpSolid } from '@heroicons/react/24/solid';
import { HandThumbUpIcon as HandThumbUpOutline } from '@heroicons/react/24/outline';
import { ArrowPathRoundedSquareIcon } from '@heroicons/react/24/outline';
import ReactionPicker, { getReactionEmoji } from './ReactionPicker';

/*
  PostActionBar
  Reusable action bar with emoji reactions support.

  Like button behavior:
  - Click: Shows quick reaction bar (5 reactions + "more" button)
  - Selected reaction shows as emoji instead of thumbs up
  - "More" button opens full grid of 22 reactions

  Props:
    post: { id, user_reaction, likes_count, dislikes_count, comments_count, shares_count }
    onToggleReaction(postId, reactionType)
    onToggleComments(postId)
    onShare(postId)
    compact? (optional style tweak)
*/

export const PostActionBar = ({ post, onToggleReaction, onToggleComments, onShare, onOpenShareMenu, onRepost, compact=false, readOnly=false }) => {
  const [showReactionPicker, setShowReactionPicker] = useState(false);
  const [pickerMode, setPickerMode] = useState('quick'); // 'quick' or 'full'
  const [reactionPickerPosition, setReactionPickerPosition] = useState({ top: 0, left: 0 });
  const reactionButtonRef = useRef(null);

  if (!post) return null;

  const baseBtn = `flex items-center gap-1 text-sm transition-colors ${readOnly ? 'cursor-default' : 'cursor-pointer'}`;
  const isPublished = true;

  // Get current user's reaction
  const currentReaction = post.user_reaction || null;
  const reactionEmoji = currentReaction ? getReactionEmoji(currentReaction) : null;

  // Handle opening reaction picker (quick mode first)
  const handleLikeClick = (e) => {
    if (readOnly) return;

    const rect = e.currentTarget.getBoundingClientRect();
    setReactionPickerPosition({
      top: rect.top - 60 + window.scrollY, // Show above the button
      left: rect.left + window.scrollX
    });
    setPickerMode('quick');
    setShowReactionPicker(true);
  };

  // Handle "more" button click (switch to full grid)
  const handleShowMore = () => {
    setPickerMode('full');
  };

  // Handle reaction selection
  const handleReactionSelect = (reactionType) => {
    onToggleReaction(post.id, reactionType);
  };

  return (
    <>
      <div className={`flex items-center ${compact ? 'gap-4 text-[12px]' : 'gap-6 text-sm'} text-gray-600`}>
        {/* Like/Reaction button */}
        <button
          ref={reactionButtonRef}
          onClick={handleLikeClick}
          className={`${baseBtn} ${!readOnly ? 'hover:text-blue-600' : ''} ${currentReaction ? 'text-blue-600' : ''}`}
          disabled={readOnly}
        >
          <div className="flex items-center gap-1">
            {reactionEmoji ? (
              <span className="text-lg leading-none">{reactionEmoji}</span>
            ) : currentReaction === 'like' ? (
              <HandThumbUpSolid className="h-5 w-5" />
            ) : (
              <HandThumbUpOutline className="h-5 w-5" />
            )}
            <span className="text-sm">{post.likes_count || 0}</span>
          </div>
        </button>

        {/* Comments */}
        <button
          onClick={readOnly ? undefined : () => onToggleComments(post.id)}
          className={`${baseBtn} ${!readOnly ? 'hover:text-blue-600' : ''}`}
          disabled={readOnly}
        >
          <ChatBubbleLeftRightIcon className="h-4 w-4" />
          {post.comments_count}
        </button>

        {/* Share */}
        <button
          onClick={readOnly ? undefined : (e) => onOpenShareMenu && onOpenShareMenu(post, e.currentTarget)}
          className={`${baseBtn} ${!readOnly ? 'hover:text-green-600' : ''}`}
          disabled={readOnly}
        >
          <ShareIcon className="h-4 w-4" />
          {post.shares_count}
        </button>

        {/* Repost */}
        {isPublished && (
          <button
            onClick={readOnly ? undefined : () => onRepost && onRepost(post)}
            className={`${baseBtn} ${!readOnly ? 'hover:text-purple-600' : ''} ${post.is_reposted ? 'text-purple-600' : ''}`}
            disabled={readOnly}
          >
            <ArrowPathRoundedSquareIcon className="h-4 w-4" />
            {post.reposts_count || 0}
          </button>
        )}
      </div>

      {/* Reaction Picker */}
      {showReactionPicker && (
        <ReactionPicker
          onReact={handleReactionSelect}
          onClose={() => setShowReactionPicker(false)}
          currentReaction={currentReaction}
          position={reactionPickerPosition}
          mode={pickerMode}
          onShowMore={handleShowMore}
        />
      )}
    </>
  );
};
export default PostActionBar;
