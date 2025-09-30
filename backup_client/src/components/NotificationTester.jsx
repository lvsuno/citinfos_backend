import React, { useState } from 'react';
import { useRealTimeNotifications } from '../hooks/useRealTimeNotifications';
import api from '../services/axiosConfig.js'; // Use configured axios instance

const NotificationTester = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState([]);

  const {
    notifications,
    unreadCount,
    isConnected,
    isConnecting,
    connectionFailed,
    connectionStatus
  } = useRealTimeNotifications({
    autoConnect: true,
    enableToasts: true,
    enableSound: false,
    onNotification: (notification) => {
      console.log('🔔 Real-time notification received:', notification);
      addTestResult(`Real-time notification: ${notification.title}`, 'success');
    },
    onConnection: ({ isConnected, connectionFailed }) => {
      if (isConnected) {
        addTestResult('WebSocket connected successfully', 'success');
      } else if (connectionFailed) {
        addTestResult('WebSocket connection failed', 'error');
      }
    }
  });

  const addTestResult = (message, type = 'info') => {
    const result = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, // Unique ID with timestamp + random string
      message,
      type,
      timestamp: new Date().toLocaleTimeString()
    };
    setTestResults(prev => [result, ...prev.slice(0, 9)]); // Keep last 10 results
  };

  const createTestNotification = async () => {
    setIsLoading(true);
    try {
      const response = await api.post('/notifications/test/create/', {
        title: 'Test Notification',
        message: 'This is a test notification from the React frontend!',
        type: 'system',
        priority: 2
      });

      if (response.status === 201) {
        const data = response.data;
        addTestResult(`Created notification: ${data.notification.title}`, 'success');
      }
    } catch (error) {
      console.error('Error creating test notification:', error);
      const errorMessage = error.response?.data?.error || error.message || 'Unknown error';
      addTestResult(`Failed to create notification: ${errorMessage}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const createBulkNotifications = async () => {
    setIsLoading(true);
    try {
      const response = await api.post('/notifications/test/bulk/', {
        count: 5
      });

      if (response.status === 201) {
        const data = response.data;
        addTestResult(`Created ${data.notifications.length} bulk notifications`, 'success');
      }
    } catch (error) {
      console.error('Error creating bulk notifications:', error);
      const errorMessage = error.response?.data?.error || error.message || 'Unknown error';
      addTestResult(`Failed to create bulk notifications: ${errorMessage}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const testWebSocketConnection = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/notifications/test/websocket/');

      if (response.status === 200) {
        const data = response.data;
        addTestResult('WebSocket test notification sent - check if you receive it in real-time!', 'info');
      }
    } catch (error) {
      console.error('Error testing WebSocket:', error);
      const errorMessage = error.response?.data?.error || error.message || 'Unknown error';
      addTestResult(`WebSocket test failed: ${errorMessage}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'text-green-600';
      case 'connecting': return 'text-yellow-600';
      default: return 'text-red-600';
    }
  };

  const getStatusText = () => {
    if (isConnected) return '🟢 Connected';
    if (isConnecting) return '🟡 Connecting...';
    if (connectionFailed) return '🔴 Connection Failed';
    return '⚪ Disconnected';
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Real-Time Notification System Tester
        </h2>

        {/* Connection Status */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-3">Connection Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <span className="text-sm text-gray-600">WebSocket Status:</span>
              <div className={`font-medium ${getStatusColor(connectionStatus)}`}>
                {getStatusText()}
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-600">Unread Notifications:</span>
              <div className="font-medium text-blue-600">
                {unreadCount}
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-600">Total Notifications:</span>
              <div className="font-medium text-purple-600">
                {notifications.length}
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-600">Latest Notification:</span>
              <div className="font-medium text-gray-700 text-sm">
                {notifications[0]?.title || 'None'}
              </div>
            </div>
          </div>
        </div>

        {/* Test Buttons */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Test Actions</h3>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={createTestNotification}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Creating...' : 'Create Test Notification'}
            </button>

            <button
              onClick={createBulkNotifications}
              disabled={isLoading}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Creating...' : 'Create 5 Bulk Notifications'}
            </button>

            <button
              onClick={testWebSocketConnection}
              disabled={isLoading}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Testing...' : 'Test WebSocket Connection'}
            </button>
          </div>
        </div>

        {/* Test Results */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Test Results</h3>
          <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
            {testResults.length === 0 ? (
              <p className="text-gray-500 text-sm">No test results yet. Click a test button above.</p>
            ) : (
              <div className="space-y-2">
                {testResults.map(result => (
                  <div key={result.id} className={`text-sm p-2 rounded ${
                    result.type === 'success' ? 'bg-green-100 text-green-800' :
                    result.type === 'error' ? 'bg-red-100 text-red-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    <span className="text-xs text-gray-600">{result.timestamp}</span>
                    <span className="ml-2">{result.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Notifications */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Recent Notifications (Latest 5)</h3>
          <div className="space-y-2">
            {notifications.slice(0, 5).map(notification => (
              <div key={notification.id} className={`p-3 rounded-lg border ${
                notification.read ? 'bg-gray-50' : 'bg-blue-50 border-blue-200'
              }`}>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{notification.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                      <span className={`px-2 py-1 rounded-full ${
                        notification.type === 'system' ? 'bg-gray-100' :
                        notification.type === 'social' ? 'bg-pink-100' :
                        notification.type === 'message' ? 'bg-blue-100' :
                        'bg-purple-100'
                      }`}>
                        {notification.type}
                      </span>
                      <span>{new Date(notification.timestamp).toLocaleString()}</span>
                      {!notification.read && <span className="text-blue-600 font-medium">UNREAD</span>}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {notifications.length === 0 && (
              <p className="text-gray-500 text-sm py-4">No notifications yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationTester;
