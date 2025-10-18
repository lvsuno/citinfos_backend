/**
 * Example Post Component with PostSee Integration
 * Demonstrates how to use PostViewTracker and withPostViewTracking HOC
 */

import React from 'react';
import PostViewTracker from './analytics/PostViewTracker';
import withPostViewTracking from './analytics/withPostViewTracking';

// Basic Post Component
const BasicPost = ({ title, content, author, timestamp, postId }) => {
  return (
    <article className="post">
      <header className="post-header">
        <h2 className="post-title">{title}</h2>
        <div className="post-meta">
          <span className="author">By {author}</span>
          <span className="timestamp">{new Date(timestamp).toLocaleDateString()}</span>
        </div>
      </header>

      <div className="post-content">
        <p>{content}</p>

        {/* Example media content */}
        <img
          src="/api/placeholder/400/200"
          alt="Post illustration"
          className="post-image"
        />

        {/* Example links */}
        <a href="https://example.com" target="_blank" rel="noopener noreferrer">
          Learn more about this topic
        </a>
      </div>

      <footer className="post-footer">
        <button className="like-button">❤️ Like</button>
        <button className="comment-button">💬 Comment</button>
        <button className="share-button">🔗 Share</button>
      </footer>
    </article>
  );
};

// Enhanced Post Component with Manual PostViewTracker
const PostWithManualTracking = ({ postId, source = 'feed', ...props }) => {
  const postRef = React.useRef(null);

  const handleViewTracked = (result) => {  };

  const handleEngagement = (type, data) => {  };

  return (
    <div ref={postRef} className="post-container">
      <BasicPost {...props} />

      {/* Manual PostViewTracker integration */}
      <PostViewTracker
        postId={postId}
        postElement={postRef.current}
        source={source}
        onViewTracked={handleViewTracked}
        onEngagement={handleEngagement}
        trackScrollDepth={true}
        trackTimeSpent={true}
        trackClicks={true}
        minViewTime={1000}
        minScrollPercentage={25}
      />
    </div>
  );
};

// Automatically tracked Post Component using HOC
const AutoTrackedPost = withPostViewTracking(BasicPost, {
  trackScrollDepth: true,
  trackTimeSpent: true,
  trackClicks: true,
  minViewTime: 1000,
  minScrollPercentage: 25,
});

// Usage Examples Component
const PostExamples = () => {
  const samplePosts = [
    {
      id: '123e4567-e89b-12d3-a456-426614174001',
      title: 'Understanding PostSee Analytics',
      content: 'This is an example post demonstrating the PostSee tracking system. Scroll down to see how the system tracks your viewing behavior, including time spent, scroll depth, and interactions with links and media. The tracking is non-intrusive and helps us understand user engagement patterns.',
      author: 'Analytics Team',
      timestamp: new Date().toISOString(),
    },
    {
      id: '123e4567-e89b-12d3-a456-426614174002',
      title: 'HOC Integration Example',
      content: 'This post uses the withPostViewTracking Higher-Order Component for automatic tracking. The HOC wraps the post component and automatically adds tracking capabilities without modifying the original component code.',
      author: 'Development Team',
      timestamp: new Date(Date.now() - 86400000).toISOString(), // Yesterday
    },
  ];

  return (
    <div className="post-examples">
      <h1>PostSee Integration Examples</h1>

      <section className="example-section">
        <h2>Manual Integration</h2>
        <p>Post with manually integrated PostViewTracker component:</p>

        <PostWithManualTracking
          postId={samplePosts[0].id}
          title={samplePosts[0].title}
          content={samplePosts[0].content}
          author={samplePosts[0].author}
          timestamp={samplePosts[0].timestamp}
          source="examples"
        />
      </section>

      <section className="example-section">
        <h2>HOC Integration</h2>
        <p>Post with automatic tracking using withPostViewTracking HOC:</p>

        <AutoTrackedPost
          postId={samplePosts[1].id}
          title={samplePosts[1].title}
          content={samplePosts[1].content}
          author={samplePosts[1].author}
          timestamp={samplePosts[1].timestamp}
          source="examples"
        />
      </section>

      <section className="integration-notes">
        <h2>Integration Notes</h2>
        <ul>
          <li>PostViewTracker automatically tracks when posts become visible</li>
          <li>Minimum view time and scroll percentage are configurable</li>
          <li>Link clicks and media interactions are automatically tracked</li>
          <li>All tracking data is sent to the PostSee analytics endpoint</li>
          <li>The HOC approach is recommended for existing components</li>
        </ul>
      </section>
    </div>
  );
};

export default PostExamples;
