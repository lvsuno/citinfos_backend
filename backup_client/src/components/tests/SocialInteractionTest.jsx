import React, { useState, useEffect } from 'react';
import { socialAPI } from '../../services/social-api';
import { useJWTAuth } from '../../hooks/useJWTAuth';
import usePostInteractions from '../social/usePostInteractions';

/**
 * SocialInteractionTest - Test component to verify all social interactions
 * are properly connected to the backend and storing data in the database.
 */
const SocialInteractionTest = () => {
  const { user, isAuthenticated } = useJWTAuth();
  const [testResults, setTestResults] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [testPost, setTestPost] = useState(null);
  const [testComment, setTestComment] = useState(null);

  // Mock post for testing
  const mockPost = {
    id: 'test-post-123',
    content: 'This is a test post for social interactions',
    author: { username: 'testuser' },
    likes_count: 0,
    dislikes_count: 0,
    comments_count: 0,
    shares_count: 0,
    reposts_count: 0,
    is_liked: false,
    is_disliked: false,
    is_reposted: false,
    comments: []
  };

  const {
    postState,
    toggleReaction,
    addComment,
    repost,
    directShare,
    isLoading,
    error
  } = usePostInteractions(testPost || mockPost);

  const addTestResult = (test, success, data = null, error = null) => {
    setTestResults(prev => [...prev, {
      id: Date.now(),
      test,
      success,
      data,
      error: error?.message || error,
      timestamp: new Date().toLocaleTimeString()
    }]);
  };

  const runSocialInteractionTests = async () => {
    if (!isAuthenticated) {
      addTestResult('Authentication Check', false, null, 'User not authenticated');
      return;
    }

    setIsRunning(true);
    setTestResults([]);
    let createdPost = null;
    let createdComment = null;

    // Test 1: Create a test post
    try {
      const newPost = await socialAPI.posts.create({
        content: 'Test post for social interactions - ' + Date.now(),
        post_type: 'text',
        visibility: 'public'
      });
      createdPost = newPost;
      setTestPost(newPost);
      addTestResult('Create Test Post', true, { id: newPost.id, content: newPost.content });
    } catch (err) {
      addTestResult('Create Test Post', false, null, err);
      setIsRunning(false);
      return;
    }

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Test 2: Like the post
    try {
      await socialAPI.likes.likePost(createdPost.id);
      addTestResult('Like Post', true, { postId: createdPost.id });
    } catch (err) {
      addTestResult('Like Post', false, null, err);
    }

    await new Promise(resolve => setTimeout(resolve, 500));

    // Test 3: Unlike the post
    try {
      await socialAPI.likes.unlikePost(createdPost.id);
      addTestResult('Unlike Post', true, { postId: createdPost.id });
    } catch (err) {
      addTestResult('Unlike Post', false, null, err);
    }

    await new Promise(resolve => setTimeout(resolve, 500));

    // Test 4: Dislike the post
    try {
      await socialAPI.dislikes.dislikePost(createdPost.id);
      addTestResult('Dislike Post', true, { postId: createdPost.id });
    } catch (err) {
      addTestResult('Dislike Post', false, null, err);
    }

    await new Promise(resolve => setTimeout(resolve, 500));

    // Test 5: Remove dislike
    try {
      await socialAPI.dislikes.undislikePost(createdPost.id);
      addTestResult('Remove Dislike', true, { postId: createdPost.id });
    } catch (err) {
      addTestResult('Remove Dislike', false, null, err);
    }

    await new Promise(resolve => setTimeout(resolve, 500));

    // Test 6: Add a comment
    try {
      const comment = await socialAPI.comments.create({
        post: createdPost.id,
        content: 'This is a test comment - ' + Date.now()
      });
      createdComment = comment;
      setTestComment(comment);
      addTestResult('Add Comment', true, { id: comment.id, content: comment.content });
    } catch (err) {
      addTestResult('Add Comment', false, null, err);
    }

    await new Promise(resolve => setTimeout(resolve, 500));

    // Test 7: Like the comment
    if (createdComment) {
      try {
        await socialAPI.likes.likeComment(createdComment.id);
        addTestResult('Like Comment', true, { commentId: createdComment.id });
      } catch (err) {
        addTestResult('Like Comment', false, null, err);
      }
    }

    await new Promise(resolve => setTimeout(resolve, 500));

    // Test 8: Create a repost
    try {
      await socialAPI.reposts.create(createdPost.id, 'This is a test repost!');
      addTestResult('Create Repost', true, { postId: createdPost.id });
    } catch (err) {
      addTestResult('Create Repost', false, null, err);
    }

    await new Promise(resolve => setTimeout(resolve, 500));

    // Test 9: Create a mention (this will likely fail due to user ID requirements)
    try {
      // For mentions, we need a real user profile ID
      // We'll try with the current user's profile ID or skip this test
      const userProfileId = user?.profile_id || user?.id;
      if (userProfileId) {
        await socialAPI.mentions.create({
          post: createdPost.id,
          mentioned_user: userProfileId
        });
        addTestResult('Create Mention', true, { postId: createdPost.id, mentionedUser: userProfileId });
      } else {
        addTestResult('Create Mention', false, null, 'No user profile ID available');
      }
    } catch (err) {
      addTestResult('Create Mention', false, null, err);
    }

    // Test 10: Clean up - delete the test post
    try {
      await socialAPI.posts.delete(createdPost.id);
      addTestResult('Clean Up Test Post', true, { postId: createdPost.id });
    } catch (err) {
      addTestResult('Clean Up Test Post', false, null, err);
    }

    setIsRunning(false);
  };

  const clearResults = () => {
    setTestResults([]);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Social Interaction Database Integration Test
        </h2>
        <p className="text-gray-600">
          This test verifies that social interactions (likes, dislikes, comments, shares, reposts, mentions)
          are properly connected to the backend and storing data in the database.
        </p>
      </div>

      {/* Authentication Status */}
      <div className="mb-6 p-4 rounded-lg border">
        <h3 className="font-semibold mb-2">Authentication Status</h3>
        {isAuthenticated ? (
          <div className="flex items-center gap-2 text-green-600">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Authenticated as: {user?.username || 'Unknown'}</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-red-600">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            <span>Not authenticated - Please log in to run tests</span>
          </div>
        )}
      </div>

      {/* Test Controls */}
      <div className="mb-6 flex gap-4">
        <button
          onClick={runSocialInteractionTests}
          disabled={!isAuthenticated || isRunning}
          className={`px-6 py-2 rounded-lg font-medium ${
            !isAuthenticated || isRunning
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
        >
          {isRunning ? 'Running Tests...' : 'Run Social Interaction Tests'}
        </button>

        <button
          onClick={clearResults}
          disabled={testResults.length === 0}
          className="px-6 py-2 rounded-lg font-medium bg-gray-500 text-white hover:bg-gray-600 disabled:bg-gray-300 disabled:text-gray-500"
        >
          Clear Results
        </button>
      </div>

      {/* Current Hook Status */}
      {(isLoading || error) && (
        <div className="mb-6 p-4 rounded-lg border">
          <h3 className="font-semibold mb-2">Hook Status</h3>
          {isLoading && (
            <div className="flex items-center gap-2 text-blue-600 mb-2">
              <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              <span>Processing social interaction...</span>
            </div>
          )}
          {error && (
            <div className="text-red-600 bg-red-50 p-2 rounded">
              Error: {error}
            </div>
          )}
        </div>
      )}

      {/* Test Results */}
      <div>
        <h3 className="text-lg font-semibold mb-4">
          Test Results ({testResults.length})
        </h3>

        {testResults.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            No tests run yet. Click "Run Social Interaction Tests" to begin.
          </div>
        ) : (
          <div className="space-y-3">
            {testResults.map((result) => (
              <div
                key={result.id}
                className={`p-4 rounded-lg border-l-4 ${
                  result.success
                    ? 'bg-green-50 border-green-500'
                    : 'bg-red-50 border-red-500'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">
                    {result.test}
                  </h4>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500">{result.timestamp}</span>
                    <div
                      className={`w-3 h-3 rounded-full ${
                        result.success ? 'bg-green-500' : 'bg-red-500'
                      }`}
                    ></div>
                  </div>
                </div>

                {result.data && (
                  <div className="mb-2 text-sm">
                    <strong>Data:</strong>
                    <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  </div>
                )}

                {result.error && (
                  <div className="text-sm text-red-600">
                    <strong>Error:</strong> {result.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {testResults.length > 0 && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold mb-2">Summary</h4>
            <div className="flex gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span>{testResults.filter(r => r.success).length} Passed</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span>{testResults.filter(r => !r.success).length} Failed</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SocialInteractionTest;
