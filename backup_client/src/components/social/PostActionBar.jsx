import React from 'react';
import { ChatBubbleLeftRightIcon, ShareIcon, HandThumbUpIcon as HandThumbUpSolid, HandThumbDownIcon as HandThumbDownSolid } from '@heroicons/react/24/solid';
import { HandThumbUpIcon as HandThumbUpOutline, HandThumbDownIcon as HandThumbDownOutline } from '@heroicons/react/24/outline';
import { ArrowPathRoundedSquareIcon } from '@heroicons/react/24/outline';

/*
  PostActionBar
  Reusable action bar replicating PostSimulator logic.
  Props:
    post: { id, is_liked, is_disliked, likes_count, dislikes_count, comments_count, shares_count }
    onToggleReaction(postId, kind)
    onToggleComments(postId)
    onShare(postId)
    compact? (optional style tweak)
*/

export const PostActionBar = ({ post, onToggleReaction, onToggleComments, onShare, onOpenShareMenu, onRepost, compact=false, readOnly=false }) => {
  if (!post) return null;
  const baseBtn = `flex items-center gap-1 text-sm transition-colors ${readOnly ? 'cursor-default' : 'cursor-pointer'}`;
  const isPublished = true;
  return (
    <div className={`flex items-center ${compact ? 'gap-4 text-[12px]' : 'gap-6 text-sm'} text-gray-600`}>
      <button
        onClick={readOnly ? undefined : () => onToggleReaction(post.id,'like')}
        className={`${baseBtn} ${!readOnly ? 'hover:text-blue-600' : ''} ${post.is_liked ? 'text-blue-600' : ''}`}
        disabled={readOnly}
      >
        {post.is_liked ? <HandThumbUpSolid className="h-4 w-4" /> : <HandThumbUpOutline className="h-4 w-4" />}
        {post.likes_count}
      </button>
      <button
        onClick={readOnly ? undefined : () => onToggleReaction(post.id,'dislike')}
        className={`${baseBtn} ${!readOnly ? 'hover:text-red-600' : ''} ${post.is_disliked ? 'text-red-600' : ''}`}
        disabled={readOnly}
      >
        {post.is_disliked ? <HandThumbDownSolid className="h-4 w-4" /> : <HandThumbDownOutline className="h-4 w-4" />}
        {post.dislikes_count}
      </button>
      <button
        onClick={readOnly ? undefined : () => onToggleComments(post.id)}
        className={`${baseBtn} ${!readOnly ? 'hover:text-blue-600' : ''}`}
        disabled={readOnly}
      >
        <ChatBubbleLeftRightIcon className="h-4 w-4" />
        {post.comments_count}
      </button>
      <button
        onClick={readOnly ? undefined : (e) => onOpenShareMenu && onOpenShareMenu(post, e.currentTarget)}
        className={`${baseBtn} ${!readOnly ? 'hover:text-green-600' : ''}`}
        disabled={readOnly}
      >
        <ShareIcon className="h-4 w-4" />
        {post.shares_count}
      </button>
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
  );
};
export default PostActionBar;
