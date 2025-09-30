import React, { useMemo } from 'react';
import PostCard from './social/PostCard';
import RepostCard from './social/RepostCard';

/**
 * PostRenderer - Centralized post rendering component
 *
 * This component provides a unified way to render posts across the application,
 * ensuring consistent data transformation and rendering logic everywhere.
 *
 * Features:
 * - Automatic post data transformation from backend to frontend format
 * - Support for both regular posts and reposts
 * - Consistent poll data mapping
 * - Centralized attachment handling
 * - Proper key generation for React rendering
 */

// Helper function to extract filename from URL
const extractFilename = (url) => {
  if (!url) return 'Untitled';
  const parts = url.split('/');
  return parts[parts.length - 1] || 'Untitled';
};

/**
 * Transform server post data to match frontend expectations
 */
const transformServerPost = (post) => {
  let transformedPost = { ...post, type: 'post' };

  // Transform server post attachments to match frontend expectations
  if (post.attachments && Array.isArray(post.attachments)) {
    const transformedAttachments = post.attachments.map(serverAtt => ({
      id: serverAtt.id,
      type: serverAtt.media_type, // Map media_type to type
      preview: serverAtt.file_url || serverAtt.file, // Use file_url or file for preview
      name: extractFilename(serverAtt.file_url || serverAtt.file || ''),
      size: serverAtt.file_size,
      order: serverAtt.order
    }));

    transformedPost.attachments = transformedAttachments;
  }

  // Transform server post polls to match frontend expectations
  if (post.polls && Array.isArray(post.polls)) {
    const transformedPolls = post.polls.map(serverPoll => {
      // Transform poll options to include user voting state
      const transformedOptions = (serverPoll.options || []).map(option => ({
        id: option.id,
        text: option.text,
        order: option.order,
        vote_count: option.votes_count || option.vote_count || 0,
        percentage: option.vote_percentage || option.percentage || 0,
        user_has_voted: option.user_has_voted || false
      }));

      return {
        ...serverPoll,
        // Map backend fields to frontend expectations
        user_vote: serverPoll.user_votes || [], // user_votes -> user_vote
        user_voted: serverPoll.user_has_voted || false, // user_has_voted -> user_voted
        allows_multiple_votes: serverPoll.multiple_choice || false, // multiple_choice -> allows_multiple_votes
        vote_count: serverPoll.total_votes || 0, // total_votes -> vote_count
        voter_count: serverPoll.voters_count || 0, // voters_count -> voter_count
        options: transformedOptions
      };
    });

    transformedPost.polls = transformedPolls;
  }

  return transformedPost;
};

/**
 * Transform repost data to match frontend expectations
 */
const transformRepostData = (item) => {
  return {
    id: `repost-${item.repost_id || item.id}`,
    type: 'repost',
    created_at: item.created_at,
    ...item
  };
};

/**
 * Generate a unique key for React rendering
 */
const generatePostKey = (item, index, forceUpdate) => {
  if (item.type === 'repost') {
    return `repost-${item.repost_id || item.id}-${item.created_at}`;
  } else {
    return `post-${item.id}-${item._lastUpdated || item.updated_at || index}-${forceUpdate || ''}`;
  }
};

/**
 * PostRenderer Component Props
 */
const PostRenderer = ({
  posts = [],
  post, // Single post prop for backward compatibility
  onDelete,
  onUpdate,
  onVote,
  onPostUpdate, // For reposts
  onPostDelete, // For reposts
  context = 'feed',
  showBorder = true,
  compact = false,
  readOnly = false,
  hideActions = false,
  forceUpdate, // Optional prop to force re-render when data changes
  className = '',
  emptyMessage = 'No posts to display.',
  emptyIcon: EmptyIcon,
  loading = false,
  loadingComponent: LoadingComponent
}) => {
  // Handle both single post and array of posts
  const postsToRender = useMemo(() => {
    if (post) {
      // Single post mode
      return [post];
    }
    return posts || [];
  }, [posts, post]);

  // Transform and memoize posts for consistent rendering
  const transformedPosts = useMemo(() => {
    if (!Array.isArray(postsToRender)) return [];

    return postsToRender.map((item, index) => {
      if (item.type === 'repost') {
        return transformRepostData(item);
      } else {
        const post = item.data || item;
        return transformServerPost(post);
      }
    });
  }, [postsToRender, forceUpdate]);

  // Loading state
  if (loading) {
    if (LoadingComponent) {
      return <LoadingComponent />;
    }
    return (
      <div className={`space-y-4 ${className}`}>
        {[...Array(3)].map((_, i) => (
          <div key={`loading-${i}`} className="bg-white rounded-lg shadow p-4 animate-pulse">
            <div className="flex items-start gap-3">
              <div className="h-9 w-9 rounded-full bg-gray-200" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-1/4" />
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-4 bg-gray-200 rounded w-1/2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Empty state
  if (transformedPosts.length === 0) {
    return (
      <div className={`text-center py-12 ${className}`}>
        {EmptyIcon && (
          <EmptyIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        )}
        <p className="text-gray-500">{emptyMessage}</p>
      </div>
    );
  }

  // Render posts
  return (
    <div className={`space-y-4 ${className}`}>
      {transformedPosts.map((item, index) => {
        const uniqueKey = generatePostKey(item, index, forceUpdate);

        if (item.type === 'repost') {
          return (
            <RepostCard
              key={uniqueKey}
              repostData={item}
              onPostUpdate={onPostUpdate || onUpdate}
              onPostDelete={onPostDelete || onDelete}
              readOnly={readOnly}
              hideActions={hideActions}
            />
          );
        } else {
          return (
            <PostCard
              key={uniqueKey}
              post={item}
              onDelete={onDelete}
              onUpdate={onUpdate}
              onVote={onVote}
              context={context}
              showBorder={showBorder}
              compact={compact}
              readOnly={readOnly}
              hideActions={hideActions}
            />
          );
        }
      })}
    </div>
  );
};

export default PostRenderer;
