import React, { useState, useEffect } from 'react';
import { abTestingClient, useABTesting } from '../lib/abTestingMock';

// Similar Users Component with A/B Testing
export const SimilarUsersComponent = ({ userId }) => {
  const { getSimilarUsers, recordInteraction, setAlgorithm, clearAlgorithm, getAvailableAlgorithms, loading, error } = useABTesting();
  const [users, setUsers] = useState([]);
  const [algorithmUsed, setAlgorithmUsed] = useState('');
  const [experimentGroup, setExperimentGroup] = useState('');
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('auto');

  const availableAlgorithms = getAvailableAlgorithms();

  useEffect(() => {
    loadSimilarUsers();
  }, [userId]);

  const loadSimilarUsers = async () => {
    try {
      const result = await getSimilarUsers(userId);
      setUsers(result.users);
      setAlgorithmUsed(result.algorithm_used);
      setExperimentGroup(result.experiment_group || '');
    } catch (err) {
      console.error('Failed to load similar users:', err);
    }
  };

  const handleAlgorithmChange = async (algorithm) => {
    setSelectedAlgorithm(algorithm);

    if (algorithm === 'auto') {
      clearAlgorithm();
    } else {
      setAlgorithm(algorithm);
    }

    await loadSimilarUsers();
  };

  const handleUserClick = async (targetUser) => {
    try {
      await recordInteraction('click', targetUser.id);
    } catch (err) {
      console.error('Failed to record interaction:', err);
    }
  };

  const handleUserLike = async (targetUser) => {
    try {
      await recordInteraction('like', targetUser.id);
    } catch (err) {
      console.error('Failed to record interaction:', err);
    }
  };

  if (loading) {
    return <div className="text-center p-4">Loading similar users...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">Error: {error}</div>;
  }

  return (
    <div className="similar-users-container">
      <div className="mb-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Similar Users</h2>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label htmlFor="algorithm-select" className="text-sm font-medium text-gray-700">
                Algorithm:
              </label>
              <select
                id="algorithm-select"
                value={selectedAlgorithm}
                onChange={(e) => handleAlgorithmChange(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={loading}
              >
                <option value="auto">Auto (A/B Test)</option>
                {availableAlgorithms.map((algo) => (
                  <option key={algo.value} value={algo.value}>
                    {algo.label}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={loadSimilarUsers}
              disabled={loading}
              className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Refreshing...' : 'Refresh Users'}
            </button>
          </div>
        </div>
        <div className="text-sm text-gray-600">
          <span className="mr-4">Algorithm: {algorithmUsed.replace('_', ' ').toUpperCase()}</span>
          {experimentGroup && (
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              experimentGroup === 'manual'
                ? 'bg-purple-100 text-purple-800'
                : experimentGroup === 'test'
                ? 'bg-orange-100 text-orange-800'
                : 'bg-blue-100 text-blue-800'
            }`}>
              {experimentGroup === 'manual' ? 'MANUAL' : `Group: ${experimentGroup.toUpperCase()}`}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {users.map((user) => (
          <div
            key={user.id}
            className="border rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => handleUserClick(user)}
          >
            <div className="flex items-center mb-3">
              <img
                src={user.profile_picture}
                alt={user.username}
                className="w-12 h-12 rounded-full mr-3"
              />
              <div>
                <h3 className="font-semibold">{user.username}</h3>
                <p className="text-sm text-gray-600">
                  {Math.round(user.similarity_score * 100)}% similarity
                </p>
              </div>
            </div>

            <div className="mb-3">
              <p className="text-xs text-gray-500 mb-1">Common interests:</p>
              <div className="flex flex-wrap gap-1">
                {user.common_interests.map((interest, idx) => (
                  <span
                    key={idx}
                    className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs"
                  >
                    {interest}
                  </span>
                ))}
              </div>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">
                {user.mutual_connections} mutual connections
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleUserLike(user);
                }}
                className="bg-blue-500 text-white px-3 py-1 rounded text-xs hover:bg-blue-600"
              >
                Like
              </button>
            </div>

            <div className="mt-2 text-xs text-gray-400">
              {user.similarity_type}
            </div>
          </div>
        ))}
      </div>

      {users.length === 0 && (
        <div className="text-center text-gray-500 p-8">
          No similar users found
        </div>
      )}
    </div>
  );
};

// A/B Testing Dashboard Component
export const ABTestingDashboard = () => {
  const { getDashboard, loading, error } = useABTesting();
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const data = await getDashboard();
      setDashboard(data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    }
  };

  if (loading) {
    return <div className="text-center p-4">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">Error: {error}</div>;
  }

  if (!dashboard) {
    return <div className="text-center p-4">No dashboard data available</div>;
  }

  return (
    <div className="ab-testing-dashboard">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">A/B Testing Dashboard</h1>
        <button
          onClick={loadDashboard}
          disabled={loading}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Refreshing...' : 'Refresh Dashboard'}
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-800">Active Experiments</h3>
          <p className="text-3xl font-bold text-blue-600">
            {dashboard.dashboard.summary.active_experiments}
          </p>
        </div>

        <div className="bg-green-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-green-800">Total Assignments</h3>
          <p className="text-3xl font-bold text-green-600">
            {dashboard.dashboard.summary.total_assignments}
          </p>
        </div>

        <div className="bg-purple-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-purple-800">Recent Metrics</h3>
          <p className="text-3xl font-bold text-purple-600">
            {dashboard.dashboard.summary.recent_metrics}
          </p>
        </div>
      </div>

      {/* Experiments List */}
      <div className="experiments-list">
        <h2 className="text-xl font-bold mb-4">Experiments</h2>
        <div className="space-y-4">
          {dashboard.dashboard.experiments.map((experiment) => (
            <div key={experiment.id} className="border rounded-lg p-4 bg-white shadow">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-lg font-semibold">{experiment.name}</h3>
                  <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                    experiment.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {experiment.status.toUpperCase()}
                  </span>
                </div>
                <div className="text-right text-sm text-gray-600">
                  <div>Traffic Split: {Math.round(experiment.traffic_split * 100)}%</div>
                  <div>Total Users: {experiment.total_users}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-3">
                <div className="bg-blue-50 p-3 rounded">
                  <h4 className="font-semibold text-blue-800 mb-1">Control</h4>
                  <p className="text-sm text-blue-600">{experiment.control_algorithm}</p>
                  <p className="text-lg font-bold text-blue-700">{experiment.control_users} users</p>
                </div>

                <div className="bg-orange-50 p-3 rounded">
                  <h4 className="font-semibold text-orange-800 mb-1">Test</h4>
                  <p className="text-sm text-orange-600">{experiment.test_algorithm}</p>
                  <p className="text-lg font-bold text-orange-700">{experiment.test_users} users</p>
                </div>
              </div>

              <div className="text-xs text-gray-500">
                Created: {new Date(experiment.created_at).toLocaleDateString()}
                {experiment.start_date && (
                  <span className="ml-4">
                    Started: {new Date(experiment.start_date).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Performance Comparison Component
export const AlgorithmPerformance = () => {
  const [performances, setPerformances] = useState({});

  useEffect(() => {
    const algorithms = ['collaborative_filtering', 'content_based', 'jaccard_similarity', 'hybrid'];
    const data = {};

    algorithms.forEach(algorithm => {
      data[algorithm] = abTestingClient.simulateAlgorithmPerformance(algorithm);
    });

    setPerformances(data);
  }, []);

  return (
    <div className="algorithm-performance">
      <h2 className="text-xl font-bold mb-4">Algorithm Performance Comparison</h2>

      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Algorithm
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Response Time (ms)
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Accuracy
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Engagement Rate
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {Object.entries(performances).map(([algorithm, perf]) => (
              <tr key={algorithm} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {algorithm.replace('_', ' ').toUpperCase()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {Math.round(perf.response_time)}ms
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {Math.round(perf.accuracy * 100)}%
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {Math.round(perf.engagement_rate * 100)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Main App Component demonstrating usage
export const ABTestingApp = () => {
  const [activeTab, setActiveTab] = useState('similar');

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">A/B Testing Demo</h1>
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('similar')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'similar'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Similar Users
              </button>
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'dashboard'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab('performance')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'performance'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Performance
              </button>
            </nav>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {activeTab === 'similar' && <SimilarUsersComponent />}
          {activeTab === 'dashboard' && <ABTestingDashboard />}
          {activeTab === 'performance' && <AlgorithmPerformance />}
        </div>
      </div>
    </div>
  );
};

export default ABTestingApp;
