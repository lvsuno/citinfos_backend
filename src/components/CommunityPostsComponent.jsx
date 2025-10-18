import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const CommunityPostsComponent = ({
  communityId,
  showContextFilter = true
}) => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    context_type: 'all',
    community_id: communityId
  });

  // Fetch posts based on current filters
  const fetchPosts = async () => {
    try {
      setLoading(true);
      
      // Mock data for now
      const mockPosts = [
        {
          id: 1,
          title: 'Welcome to the Community',
          content: 'This is a sample post to demonstrate the community posts component.',
          author: 'Community Admin',
          created_at: new Date().toISOString(),
          context_type: 'community',
          likes: 5,
          comments: 2
        },
        {
          id: 2,
          title: 'Equipment Discussion',
          content: 'Let\'s discuss the latest equipment recommendations.',
          author: 'Equipment Expert',
          created_at: new Date().toISOString(),
          context_type: 'equipment',
          likes: 12,
          comments: 7
        }
      ];
      
      setPosts(mockPosts);
      setError(null);
    } catch (err) {      setError('Failed to load posts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, [filters, communityId]);

  const handleFilterChange = (newFilter) => {
    setFilters(prev => ({
      ...prev,
      ...newFilter
    }));
  };

  if (loading) {
    return (
      <div className="p-4 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-2 text-gray-600">Loading posts...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-600">
        <p>Error: {error}</p>
        <button 
          onClick={fetchPosts}
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {showContextFilter && (
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold mb-3">Filter Posts</h3>
          <div className="flex flex-wrap gap-2">
            {['all', 'community', 'equipment', 'discussion'].map((type) => (
              <button
                key={type}
                onClick={() => handleFilterChange({ context_type: type })}
                className={`px-3 py-1 rounded text-sm capitalize transition-colors ${
                  filters.context_type === type
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-4">
        {posts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No posts found</p>
            <p className="text-sm">Try adjusting your filters</p>
          </div>
        ) : (
          posts.map((post) => (
            <div key={post.id} className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900">{post.title}</h4>
                  <p className="text-sm text-gray-600">
                    by {post.author} • {new Date(post.created_at).toLocaleDateString()}
                  </p>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  post.context_type === 'community' ? 'bg-blue-100 text-blue-800' :
                  post.context_type === 'equipment' ? 'bg-green-100 text-green-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {post.context_type}
                </span>
              </div>
              
              <p className="text-gray-700 mb-4">{post.content}</p>
              
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <button className="flex items-center space-x-1 hover:text-blue-600">
                  <span>👍</span>
                  <span>{post.likes} likes</span>
                </button>
                <button className="flex items-center space-x-1 hover:text-blue-600">
                  <span>💬</span>
                  <span>{post.comments} comments</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

CommunityPostsComponent.propTypes = {
  communityId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  showContextFilter: PropTypes.bool,
};

export default CommunityPostsComponent;
