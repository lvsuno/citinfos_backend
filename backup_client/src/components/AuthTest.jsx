import React, { useState } from 'react';
import { useJWTAuth } from '../hooks/useJWTAuth';

/**
 * Authentication Test Component
 *
 * This component provides a simple interface to test the JWT authentication system.
 * It displays the current user state and provides buttons to test various auth functions.
 */
const AuthTest = () => {
  const { user, isLoading, isAuthenticated, refreshUser, api } = useJWTAuth();
  const [testResult, setTestResult] = useState('');
  const [testLoading, setTestLoading] = useState(false);

  const runAPITest = async () => {
    setTestLoading(true);
    setTestResult('');
    try {
      // Test authenticated API call
      const response = await api.get('/auth/user-info/');
      setTestResult(`✅ API Test Successful! User: ${response.data.username}`);
    } catch (error) {
      setTestResult(`❌ API Test Failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setTestLoading(false);
    }
  };

  const runRefreshTest = async () => {
    setTestLoading(true);
    setTestResult('');
    try {
      await refreshUser();
      setTestResult('✅ User refresh successful!');
    } catch (error) {
      setTestResult(`❌ User refresh failed: ${error.message}`);
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">JWT Authentication Test</h2>

      {/* Current Auth State */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-3 text-gray-700">Current Authentication State</h3>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="font-medium">Loading:</span>
            <span className={`px-2 py-1 rounded text-sm ${isLoading ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
              {isLoading ? 'Yes' : 'No'}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="font-medium">Authenticated:</span>
            <span className={`px-2 py-1 rounded text-sm ${isAuthenticated ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {isAuthenticated ? 'Yes' : 'No'}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="font-medium">User:</span>
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
              {user ? `${user.username} (${user.email})` : 'None'}
            </span>
          </div>
        </div>
      </div>

      {/* User Details */}
      {user && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-3 text-gray-700">User Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div><span className="font-medium">ID:</span> {user.id}</div>
            <div><span className="font-medium">Username:</span> {user.username}</div>
            <div><span className="font-medium">Email:</span> {user.email}</div>
            <div><span className="font-medium">First Name:</span> {user.first_name}</div>
            <div><span className="font-medium">Last Name:</span> {user.last_name}</div>
            <div><span className="font-medium">Role:</span> {user.profile?.role || 'N/A'}</div>
            <div><span className="font-medium">Verified:</span> {user.profile?.is_verified ? '✅' : '❌'}</div>
            <div><span className="font-medium">Staff:</span> {user.is_staff ? '✅' : '❌'}</div>
          </div>
        </div>
      )}

      {/* Test Buttons */}
      <div className="mb-6 space-y-3">
        <h3 className="text-lg font-semibold text-gray-700">Authentication Tests</h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={runAPITest}
            disabled={testLoading || !isAuthenticated}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Test API Call
          </button>
          <button
            onClick={runRefreshTest}
            disabled={testLoading || !isAuthenticated}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Test User Refresh
          </button>
        </div>
      </div>

      {/* Test Results */}
      {testResult && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-3 text-gray-700">Test Result</h3>
          <div className="text-sm font-mono bg-white p-3 rounded border">
            {testResult}
          </div>
        </div>
      )}

      {/* Token Status */}
      <div className="mb-6 p-4 bg-yellow-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-3 text-gray-700">Token Status</h3>
        <div className="space-y-2 text-sm">
          <div>
            <span className="font-medium">Access Token:</span>
            <span className="ml-2 font-mono text-xs">
              {localStorage.getItem('access_token') ? '✅ Present' : '❌ Missing'}
            </span>
          </div>
          <div>
            <span className="font-medium">Refresh Token:</span>
            <span className="ml-2 font-mono text-xs">
              {localStorage.getItem('refresh_token') ? '✅ Present' : '❌ Missing'}
            </span>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="p-4 bg-green-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-3 text-green-800">Authentication Instructions</h3>
        <ul className="text-sm text-green-700 space-y-1">
          <li>• <strong>Registration:</strong> Does not require authentication - public endpoint</li>
          <li>• <strong>Login:</strong> Does not require authentication - public endpoint</li>
          <li>• <strong>Email Verification:</strong> Does not require authentication - public endpoint</li>
          <li>• <strong>All other actions:</strong> Require JWT authentication</li>
          <li>• <strong>Token Auto-renewal:</strong> Handled automatically by middleware</li>
          <li>• <strong>Session Management:</strong> Hybrid JWT + server session system</li>
        </ul>
      </div>
    </div>
  );
};

export default AuthTest;
