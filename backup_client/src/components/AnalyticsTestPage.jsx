import React, { useState } from 'react';
import { PostViewTracker } from '../components/analytics';
import { usePostViewTracker } from '../hooks/usePostViewTracker';

/**
 * Analytics Test Component for frontend testing
 * This component demonstrates and tests the PostSee analytics system
 */
const AnalyticsTestPage = () => {
  const [testPostId] = useState('test-post-analytics-' + Date.now());
  const [showResults, setShowResults] = useState(false);
  const [testResults, setTestResults] = useState([]);

  // Initialize the analytics tracker
  const tracker = usePostViewTracker(testPostId, {
    threshold: 0.5,
    minViewTime: 1000,
    trackReadTime: true,
    trackScrollDepth: true,
    autoTrack: true,
    onViewTracked: (result) => {
      addTestResult('✅ View tracked automatically', result);
    },
    onEngagement: (action, result) => {
      addTestResult(`🎯 Engagement tracked: ${action}`, result);
    }
  });

  const addTestResult = (message, data = null) => {
    const timestamp = new Date().toLocaleTimeString();
    const result = {
      timestamp,
      message,
      data: data ? JSON.stringify(data, null, 2) : null
    };
    setTestResults(prev => [...prev, result]);
  };

  const handleManualTrack = async () => {
    try {
      const result = await tracker.trackView();
      addTestResult('📊 Manual view tracking', { success: result });
    } catch (error) {
      addTestResult('❌ Manual view tracking failed', { error: error.message });
    }
  };

  const handleEngagementTest = async (action) => {
    try {
      const result = await tracker.trackEngagement(action, {
        timestamp: Date.now(),
        testData: true
      });
      addTestResult(`🎯 ${action} engagement test`, { success: result });
    } catch (error) {
      addTestResult(`❌ ${action} engagement failed`, { error: error.message });
    }
  };

  const handleMarkAsRead = async () => {
    try {
      const result = await tracker.markAsRead();
      addTestResult('✅ Mark as read test', { success: result });
    } catch (error) {
      addTestResult('❌ Mark as read failed', { error: error.message });
    }
  };

  const resetTracking = () => {
    tracker.resetTracking();
    setTestResults([]);
    addTestResult('🔄 Tracking reset');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          🧪 PostSee Analytics Test Page
        </h1>

        {/* Component Status */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">📊 Component Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 bg-green-500 rounded-full"></span>
              <span>PostViewTracker Component</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 bg-green-500 rounded-full"></span>
              <span>usePostViewTracker Hook</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 bg-green-500 rounded-full"></span>
              <span>Analytics API Service</span>
            </div>
          </div>
        </div>

        {/* Real-time Analytics */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">📈 Real-time Analytics Data</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-blue-600">Is Viewing</div>
              <div className="text-xl font-bold text-blue-900">
                {tracker.isViewing ? 'Yes' : 'No'}
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-600">Read Time</div>
              <div className="text-xl font-bold text-green-900">
                {Math.floor(tracker.readTime)}s
              </div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-sm text-purple-600">Scroll Depth</div>
              <div className="text-xl font-bold text-purple-900">
                {Math.floor(tracker.scrollDepth)}%
              </div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-sm text-orange-600">Engagements</div>
              <div className="text-xl font-bold text-orange-900">
                {tracker.engagements.length}
              </div>
            </div>
          </div>
        </div>

        {/* Test Post with Tracker */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">📝 Test Post (Tracked)</h2>
          <PostViewTracker
            ref={tracker.ref}
            postId={testPostId}
            className="bg-gray-50 p-6 rounded-lg min-h-96"
          >
            <h3 className="text-lg font-medium mb-4">Sample Post for Analytics Testing</h3>
            <p className="text-gray-700 mb-4">
              This is a test post to demonstrate the PostSee analytics tracking system.
              The tracking automatically monitors:
            </p>
            <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
              <li>View duration (how long you spend reading)</li>
              <li>Scroll depth (how much of the post you've seen)</li>
              <li>Device type and source information</li>
              <li>User engagement and interactions</li>
            </ul>
            <p className="text-gray-700 mb-6">
              Try scrolling through this content and using the test buttons below
              to see how the analytics system captures different types of interactions.
            </p>

            {/* Interaction buttons */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => handleEngagementTest('like')}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
              >
                <span>👍</span>
                <span>Like</span>
              </button>
              <button
                onClick={() => handleEngagementTest('share')}
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
              >
                <span>📤</span>
                <span>Share</span>
              </button>
              <button
                onClick={() => handleEngagementTest('comment')}
                className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
              >
                <span>💬</span>
                <span>Comment</span>
              </button>
            </div>
          </PostViewTracker>
        </div>

        {/* Manual Testing Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">🔧 Manual Testing Controls</h2>
          <div className="flex flex-wrap gap-3 mb-4">
            <button
              onClick={handleManualTrack}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
            >
              📊 Manual Track View
            </button>
            <button
              onClick={handleMarkAsRead}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg"
            >
              ✅ Mark as Read
            </button>
            <button
              onClick={resetTracking}
              className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
            >
              🔄 Reset Tracking
            </button>
            <button
              onClick={() => setShowResults(!showResults)}
              className="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-lg"
            >
              {showResults ? '👁️ Hide Results' : '👁️ Show Results'}
            </button>
          </div>
        </div>

        {/* Test Results */}
        {showResults && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">📋 Test Results</h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {testResults.length === 0 ? (
                <p className="text-gray-500">No test results yet. Interact with the components above to see results.</p>
              ) : (
                testResults.map((result, index) => (
                  <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{result.message}</span>
                      <span className="text-sm text-gray-500">{result.timestamp}</span>
                    </div>
                    {result.data && (
                      <pre className="text-xs text-gray-600 mt-1 bg-gray-50 p-2 rounded overflow-x-auto">
                        {result.data}
                      </pre>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mt-8">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">📖 Testing Instructions</h3>
          <ul className="text-blue-800 space-y-1">
            <li>• Scroll through the test post to see scroll depth tracking</li>
            <li>• Stay on the page to see read time increase</li>
            <li>• Click the interaction buttons to test engagement tracking</li>
            <li>• Use manual controls to test API endpoints directly</li>
            <li>• Check browser console for detailed logging</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsTestPage;
