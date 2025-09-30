import React, { useState, useEffect } from 'react';
import PostCard from './PostCard';
import RepostCard from './RepostCard';
import { socialAPI } from '../../services/social-api';

/**
 * SocialFeed - Component for displaying a combined feed of posts and reposts
 *
 * Fetches and displays a chronological feed containing:
 * - Original posts
 * - Reposts with proper repost UI
 */
const SocialFeed = () => {
  const [feedItems, setFeedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Fetch feed data
  const fetchFeed = async (pageNum = 1, replace = false) => {
    try {
      setLoading(true);
      const response = await socialAPI.posts.feed(pageNum, 20);

      if (replace) {
        setFeedItems(response.results);
      } else {
        setFeedItems(prev => [...prev, ...response.results]);
      }

      setHasMore(response.has_next);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch feed:', err);
      setError('Failed to load feed');
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchFeed(1, true);
  }, []);

  // Load more posts
  const loadMore = () => {
    if (!loading && hasMore) {
      setPage(prev => prev + 1);
      fetchFeed(page + 1, false);
    }
  };

  // Refresh feed
  const refreshFeed = () => {
    setPage(1);
    fetchFeed(1, true);
  };

  // Handle post interactions - these will be managed by individual PostCard components
  const handlePostUpdate = (postId, updatedPostData) => {
    setFeedItems(prevItems =>
      prevItems.map(item => {
        if (item.data && item.data.id === postId) {
          return {
            ...item,
            data: { ...item.data, ...updatedPostData }
          };
        }
        return item;
      })
    );
  };

  const handlePostDelete = (postId) => {
    setFeedItems(prevItems =>
      prevItems.filter(item => item.data && item.data.id !== postId)
    );
  };

  if (loading && feedItems.length === 0) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg p-4 shadow animate-pulse">
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-300 rounded w-1/4 mb-1"></div>
                <div className="h-3 bg-gray-300 rounded w-1/6"></div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-300 rounded w-3/4"></div>
              <div className="h-4 bg-gray-300 rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">{error}</p>
        <button
          onClick={refreshFeed}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {feedItems.map((item, index) => {
        if (item.type === 'post') {
          return (
            <PostCard
              key={`post-${item.data.id}-${index}`}
              post={item.data}
              onDelete={handlePostDelete}
              onUpdate={handlePostUpdate}
            />
          );
        } else if (item.type === 'repost') {
          return (
            <RepostCard
              key={`repost-${item.repost_id}-${index}`}
              repostData={item}
              onPostUpdate={handlePostUpdate}
              onPostDelete={handlePostDelete}
            />
          );
        }
        return null;
      })}

      {/* Load More Button */}
      {hasMore && (
        <div className="text-center py-4">
          <button
            onClick={loadMore}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}

      {/* End of feed */}
      {!hasMore && feedItems.length > 0 && (
        <div className="text-center py-4 text-gray-500">
          <p>You're all caught up! 🎉</p>
        </div>
      )}
    </div>
  );
};

export default SocialFeed;
