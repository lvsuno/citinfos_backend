import React from 'react';
import SocialFeed from '../components/social/SocialFeed';
import { socialAPI } from '../services/social-api';

/**
 * Example Social Feed Page
 *
 * This demonstrates how to use the new repost system with:
 * - Combined feed of posts and reposts
 * - Proper repost UI display
 * - Repost functionality
 */
const SocialFeedPage = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Social Feed
          </h1>
          <p className="text-gray-600">
            See posts and reposts from people you follow
          </p>
        </div>

        {/* Create Post Button */}
        <div className="mb-6 bg-white rounded-lg p-4 shadow">
          <button className="w-full text-left text-gray-500 bg-gray-50 rounded-lg p-3 hover:bg-gray-100">
            What's on your mind?
          </button>
        </div>

        {/* Social Feed Component */}
        <SocialFeed />
      </div>
    </div>
  );
};

export default SocialFeedPage;
