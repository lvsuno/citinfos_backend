import { useState, useCallback } from 'react';
import { socialAPI } from '../../services/social-api';

/* usePostInteractions
   Standardizes post interaction state & handlers for likes, dislikes, comments, shares.
   Now integrates with backend API to persist all interactions to database.
   Returns { postState, setPostState, toggleReaction, addComment, editComment, deleteComment, toggleCommentReaction, share, repost, directShare }
*/

export const usePostInteractions = (initialPost) => {
  const [postState, setPostState] = useState(() => ({
    ...initialPost,
    likes_count: initialPost.likes_count || 0,
    dislikes_count: initialPost.dislikes_count || 0,
    shares_count: initialPost.shares_count || 0,
    reposts_count: initialPost.reposts_count || 0,
    comments_count: (initialPost.comments || []).length || initialPost.comments_count || 0,
    is_liked: !!initialPost.is_liked,
    is_disliked: !!initialPost.is_disliked,
    is_reposted: !!initialPost.is_reposted,
    comments: initialPost.comments || []
  }));

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Clear error after a delay
  const clearError = useCallback(() => {
    setTimeout(() => setError(null), 5000);
  }, []);

  const toggleReaction = useCallback(async (kind) => {
    if (isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      let response;

      // Make API call to new real-time endpoints
      if (kind === 'like') {
        response = await socialAPI.likes.likePost(postState.id);
      } else if (kind === 'dislike') {
        response = await socialAPI.dislikes.dislikePost(postState.id);
      }

      // Update state with response data (real-time counters from backend)
      if (response && response.post) {
        setPostState(prevState => ({
          ...prevState,
          ...response.post,
          // Map API field names to our state field names
          is_liked: response.post.user_has_liked,
          is_disliked: response.post.user_has_disliked,
          likes_count: response.post.likes_count,
          dislikes_count: response.post.dislikes_count,
          comments_count: response.post.comments_count || prevState.comments_count,
          shares_count: response.post.shares_count || prevState.shares_count
        }));
      }

    } catch (err) {
      console.error('Reaction toggle failed:', err);
      setError(`Failed to ${kind} post: ${err.message}`);
      clearError();
    } finally {
      setIsLoading(false);
    }
  }, [postState.id, isLoading, clearError]);

  const addComment = useCallback(async (text, parent = null) => {
    if (!text.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      // Create comment via API
      const commentData = {
        post: postState.id,
        content: text.trim(),
        parent: parent
      };

      const newComment = await socialAPI.comments.create(commentData);

      // Transform the comment to match the nested structure expected by the UI
      const transformedComment = {
        id: newComment.id,
        author: newComment.author,
        author_username: newComment.author_username,
        author_name: newComment.author_name,
        parent: newComment.parent,
        content: newComment.content,
        is_edited: newComment.is_edited || false,
        likes_count: newComment.likes_count || 0,
        dislikes_count: newComment.dislikes_count || 0,
        replies_count: 0,
        user_has_liked: false,
        user_has_disliked: false,
        replies: [],
        created_at: newComment.created_at,
        updated_at: newComment.updated_at
      };

      // Update local state with transformed comment data
      setPostState(p => {
        let updatedComments;

        if (parent) {
          // This is a reply - add it to the parent comment's replies
          updatedComments = (p.comments || []).map(comment => {
            if (comment.id === parent) {
              return {
                ...comment,
                replies: [...(comment.replies || []), transformedComment],
                replies_count: (comment.replies_count || 0) + 1
              };
            }
            return comment;
          });
        } else {
          // This is a top-level comment
          updatedComments = [...(p.comments || []), transformedComment];
        }

        return {
          ...p,
          comments: updatedComments,
          comments_count: (p.comments_count || 0) + 1
        };
      });

      // Process mentions in the comment
      // Only pass community context if the post being commented on is within a community
      const communityId = postState.community || null;
      await socialAPI.utils.processContentMentions(text, null, newComment.id, communityId);

    } catch (err) {
      console.error('Add comment failed:', err);
      setError(`Failed to add comment: ${err.message}`);
      clearError();
    } finally {
      setIsLoading(false);
    }
  }, [postState.id, postState.community, isLoading, clearError]);

  const editComment = useCallback(async (commentId, newText) => {
    if (!newText.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      // Update comment via API
      const updatedComment = await socialAPI.comments.update(commentId, {
        content: newText.trim()
      });

      // Update local state with nested structure handling
      setPostState(p => {
        const updateCommentInList = (comments) => {
          return comments.map(comment => {
            if (comment.id === commentId) {
              return { ...comment, content: newText.trim(), is_edited: true };
            }

            // Check replies recursively
            if (comment.replies && comment.replies.length > 0) {
              return {
                ...comment,
                replies: updateCommentInList(comment.replies)
              };
            }

            return comment;
          });
        };

        return {
          ...p,
          comments: updateCommentInList(p.comments || [])
        };
      });

    } catch (err) {
      console.error('Edit comment failed:', err);
      setError(`Failed to edit comment: ${err.message}`);
      clearError();
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, clearError]);

  const deleteComment = useCallback(async (commentId) => {
    if (isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      // Delete comment via API
      await socialAPI.comments.delete(commentId);

      // Update local state with nested structure handling
      setPostState(p => {
        let removedCount = 0;

        // Helper function to remove comment and count deletions
        const removeCommentFromList = (comments, targetId) => {
          return comments.filter(comment => {
            if (comment.id === targetId) {
              // Count this comment + all its replies
              removedCount += 1 + (comment.replies || []).length;
              return false;
            }

            // Check if any replies need to be removed
            if (comment.replies && comment.replies.length > 0) {
              const originalRepliesLength = comment.replies.length;
              comment.replies = removeCommentFromList(comment.replies, targetId);
              const repliesRemoved = originalRepliesLength - comment.replies.length;
              comment.replies_count = Math.max(0, (comment.replies_count || 0) - repliesRemoved);
            }

            return true;
          });
        };

        const updatedComments = removeCommentFromList(p.comments || [], commentId);

        return {
          ...p,
          comments: updatedComments,
          comments_count: Math.max(0, (p.comments_count || 0) - removedCount)
        };
      });

    } catch (err) {
      console.error('Delete comment failed:', err);
      setError(`Failed to delete comment: ${err.message}`);
      clearError();
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, clearError]);

  const toggleCommentReaction = useCallback(async (commentId, kind) => {
    if (isLoading) return;

    setIsLoading(true);
    setError(null);

    // Find comment in nested structure
    const findComment = (comments, targetId) => {
      for (const comment of comments) {
        if (comment.id === targetId) return comment;
        if (comment.replies) {
          const found = findComment(comment.replies, targetId);
          if (found) return found;
        }
      }
      return null;
    };

    const comment = findComment(postState.comments || [], commentId);
    if (!comment) {
      setIsLoading(false);
      return;
    }

    // Helper function to update comment reactions in nested structure
    const updateCommentReaction = (comments, targetId, updates) => {
      return comments.map(c => {
        if (c.id === targetId) {
          return { ...c, ...updates };
        }

        if (c.replies && c.replies.length > 0) {
          return {
            ...c,
            replies: updateCommentReaction(c.replies, targetId, updates)
          };
        }

        return c;
      });
    };

    try {
      // Calculate optimistic updates with mutual exclusivity
      let { user_has_liked = false, user_has_disliked = false, likes_count = 0, dislikes_count = 0 } = comment;

      if (kind === 'like') {
        if (user_has_liked) {
          // Unlike
          user_has_liked = false;
          likes_count = Math.max(0, likes_count - 1);
        } else {
          // Like
          user_has_liked = true;
          likes_count += 1;
          // Remove dislike if present (mutual exclusivity)
          if (user_has_disliked) {
            user_has_disliked = false;
            dislikes_count = Math.max(0, dislikes_count - 1);
          }
        }
      } else if (kind === 'dislike') {
        if (user_has_disliked) {
          // Remove dislike
          user_has_disliked = false;
          dislikes_count = Math.max(0, dislikes_count - 1);
        } else {
          // Dislike
          user_has_disliked = true;
          dislikes_count += 1;
          // Remove like if present (mutual exclusivity)
          if (user_has_liked) {
            user_has_liked = false;
            likes_count = Math.max(0, likes_count - 1);
          }
        }
      }

      // Optimistic UI update
      setPostState(p => ({
        ...p,
        comments: updateCommentReaction(p.comments || [], commentId, {
          user_has_liked, user_has_disliked, likes_count, dislikes_count
        })
      }));

      // Make API call - using v2 endpoints for both posts and comments
      if (kind === 'like') {
        if (comment.user_has_liked) {
          await socialAPI.likes.unlikeComment(commentId);
        } else {
          await socialAPI.likes.likeComment(commentId);
        }
      } else if (kind === 'dislike') {
        if (comment.user_has_disliked) {
          await socialAPI.dislikes.undislikeComment(commentId);
        } else {
          await socialAPI.dislikes.dislikeComment(commentId);
        }
      }

    } catch (err) {
      console.error('Comment reaction toggle failed:', err);
      setError(`Failed to ${kind} comment: ${err.message}`);
      clearError();

      // Revert optimistic update on error - use original comment state
      const revertUpdates = {
        user_has_liked: comment.user_has_liked,
        user_has_disliked: comment.user_has_disliked,
        likes_count: comment.likes_count,
        dislikes_count: comment.dislikes_count
      };

      setPostState(p => ({
        ...p,
        comments: updateCommentReaction(p.comments || [], commentId, revertUpdates)
      }));
    } finally {
      setIsLoading(false);
    }
  }, [postState.comments, isLoading, clearError]);

  const repost = useCallback(async (comment = '') => {
    if (isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      // Use the content API repost endpoint - it handles toggle automatically
      const response = await socialAPI.reposts.create(postState.id, comment);

      if (response && response.post) {
        // Update state with response data
        setPostState(p => ({
          ...p,
          is_reposted: response.post.user_has_reposted || false,
          reposts_count: response.post.repost_count || 0
        }));
      } else {
        // Fallback optimistic update
        setPostState(p => ({
          ...p,
          is_reposted: !p.is_reposted,
          reposts_count: p.is_reposted
            ? Math.max(0, (p.reposts_count || 0) - 1)
            : (p.reposts_count || 0) + 1
        }));
      }

    } catch (err) {
      console.error('Repost failed:', err);
      setError(`Failed to repost: ${err.message}`);
      clearError();
    } finally {
      setIsLoading(false);
    }
  }, [postState.id, postState.is_reposted, isLoading, clearError]);

  const directShare = useCallback(async (recipientIds, note = '') => {
    if (isLoading || !recipientIds || recipientIds.length === 0) return;

    setIsLoading(true);
    setError(null);

    try {
      // Create direct share
      await socialAPI.directShares.create(postState.id, recipientIds, note);

      // Update shares count
      setPostState(p => ({
        ...p,
        shares_count: (p.shares_count || 0) + 1
      }));

    } catch (err) {
      console.error('Direct share failed:', err);
      setError(`Failed to share post: ${err.message}`);
      clearError();
    } finally {
      setIsLoading(false);
    }
  }, [postState.id, isLoading, clearError]);

  // Legacy share method for backward compatibility
  const share = useCallback(() => {
    setPostState(p => ({ ...p, shares_count: (p.shares_count || 0) + 1 }));
  }, []);

  return {
    postState,
    setPostState,
    toggleReaction,
    addComment,
    editComment,
    deleteComment,
    toggleCommentReaction,
    share, // Legacy method
    repost,
    directShare,
    isLoading,
    error
  };
};

export default usePostInteractions;
