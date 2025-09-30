import React, { useState } from 'react';
import { SimilarUsersComponent, ABTestingDashboard, AlgorithmPerformance } from '../components/ABTestingComponents';

const ABTesting = () => {
  const [activeTab, setActiveTab] = useState('users'); // 'users' | 'dashboard' | 'performance'

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4">
            <h1 className="text-3xl font-bold text-gray-900">A/B Testing System</h1>
            <p className="mt-2 text-gray-600">
              Test different similarity algorithms to improve user recommendations
            </p>
          </div>

          {/* Navigation Tabs */}
          <div className="border-t border-gray-200">
            <nav className="px-6">
              <div className="flex space-x-8">
                <button
                  onClick={() => setActiveTab('users')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'users'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Similar Users
                </button>
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'dashboard'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Experiments Dashboard
                </button>
                <button
                  onClick={() => setActiveTab('performance')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'performance'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Algorithm Performance
                </button>
              </div>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'users' && (
            <div>
              <div className="bg-white shadow rounded-lg p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Similar Users Recommendation
                </h2>
                <p className="text-gray-600 mb-4">
                  This section shows users similar to you based on different algorithms.
                  The system automatically assigns you to different experiment groups to test
                  which algorithm works best.
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-blue-800">A/B Testing Active</h3>
                      <div className="mt-2 text-sm text-blue-700">
                        <p>
                          Your interactions help us understand which algorithm provides better recommendations.
                          Click on users you find interesting or like their profiles to provide feedback.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <SimilarUsersComponent />
            </div>
          )}

          {activeTab === 'dashboard' && (
            <div>
              <div className="bg-white shadow rounded-lg p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Experiments Dashboard
                </h2>
                <p className="text-gray-600">
                  Monitor active A/B tests, user assignments, and experiment performance.
                </p>
              </div>
              <ABTestingDashboard />
            </div>
          )}

            {activeTab === 'performance' && (
            <div>
              <div className="bg-white shadow rounded-lg p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Algorithm Performance
                </h2>
                <p className="text-gray-600">
                  Compare how different similarity algorithms perform across various metrics.
                </p>
              </div>
              <AlgorithmPerformance />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-12 bg-white shadow rounded-lg p-6">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">🧪 Mock A/B Testing System</h3>
            <p className="text-gray-600">
              This is a client-side mock implementation for testing and development. In production, this would connect to your backend A/B testing infrastructure.
            </p>
            <div className="mt-4 text-sm text-gray-500">Refresh the page to see different experiment assignments and algorithm variations</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ABTesting;
