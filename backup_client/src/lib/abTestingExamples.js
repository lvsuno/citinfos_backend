// A/B Testing Configuration and Usage Examples (Clean JS)
// Shows how to integrate the mock A/B testing system

import { abTestingClient } from '../lib/abTestingMock';

// Configuration options for the mock system
export const ABTestingConfig = {
  enabled: true,
  algorithms: {
    collaborative_filtering: {
      name: 'Collaborative Filtering',
      description: 'Recommends based on user behavior patterns',
      responseTime: 120,
      accuracy: 0.78,
    },
    content_based: {
      name: 'Content-Based Filtering',
      description: 'Recommends based on content similarity',
      responseTime: 95,
      accuracy: 0.72,
    },
    jaccard_similarity: {
      name: 'Jaccard Similarity',
      description: 'Measures similarity using Jaccard coefficient',
      responseTime: 80,
      accuracy: 0.68,
    },
    hybrid: {
      name: 'Hybrid Approach',
      description: 'Combines multiple algorithms',
      responseTime: 150,
      accuracy: 0.82,
    },
  },
  trafficSplits: [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
  metrics: ['click', 'view', 'like', 'follow', 'share', 'comment', 'profile_view', 'message_sent'],
};

// Example 1: Get similar users with A/B testing
export async function getSimilarUsersWithABTesting(userId) {
  try {
    const result = await abTestingClient.getSimilarUsers(userId);
    return result;
  } catch (error) {
    console.error('A/B testing error:', error);
    return { users: [], algorithm_used: 'collaborative_filtering' };
  }
}

// Example 2: Track a user interaction
export async function trackUserInteraction(action, targetUserId, metadata = {}) {
  try {
    await abTestingClient.recordInteraction(action, targetUserId, 1);
  } catch (error) {
    console.error('Failed to track interaction:', error);
  }
}

// Example 3: Get user's current experiment status
export async function getCurrentUserExperimentStatus() {
  try {
    const assignments = await abTestingClient.getUserAssignment();
    const experiments = await abTestingClient.getExperiments();
    return assignments.map((assignment) => {
      const experiment = experiments.find((exp) => exp.id === assignment.experiment);
      return {
        experimentName: experiment?.name || 'Unknown',
        group: assignment.group,
        algorithm: assignment.group === 'control' ? experiment?.control_algorithm : experiment?.test_algorithm,
        assignedAt: assignment.assigned_at,
      };
    });
  } catch (error) {
    console.error('Failed to get experiment status:', error);
    return [];
  }
}

// Example 4: Initialize A/B Testing for a User Session
export async function initializeABTestingSession(userId) {
  try {
    const assignments = await abTestingClient.getUserAssignment();
    const dashboard = await abTestingClient.getDashboard();
    return { userId, assignments, activeExperiments: dashboard.dashboard.summary.active_experiments };
  } catch (error) {
    console.error('Failed to initialize A/B testing session:', error);
    return null;
  }
}

// Example 5: Custom Hook-like helpers for metrics and performance
export function createABTestingMetricsHelpers() {
  const trackMetric = async (metricType, value = 1) => {
    try {
      await abTestingClient.recordInteraction(metricType, 'system', value);
    } catch (error) {
      console.error('Failed to track metric:', error);
    }
  };

  const getPerformanceData = async () => {
    try {
      const metrics = await abTestingClient.getMetrics();
      return metrics.reduce((acc, metric) => {
        const key = metric.algorithm_used;
        if (!acc[key]) {
          acc[key] = { count: 0, totalValue: 0, avgValue: 0 };
        }
        acc[key].count += 1;
        acc[key].totalValue += metric.value;
        acc[key].avgValue = acc[key].totalValue / acc[key].count;
        return acc;
      }, {});
    } catch (error) {
      console.error('Failed to get performance data:', error);
      return {};
    }
  };

  return { trackMetric, getPerformanceData };
}

// Example 6: A/B Testing Middleware for API calls
export function createABTestingMiddleware() {
  return {
    similarityMiddleware: async (originalFunction, ...args) => {
      const startTime = Date.now();
      try {
        const result = await originalFunction(...args);
        const endTime = Date.now();
        await abTestingClient.recordInteraction('api_call', 'similarity', endTime - startTime);
        return result;
      } catch (error) {
        await abTestingClient.recordInteraction('api_error', 'similarity', 1);
        throw error;
      }
    },
    pageViewMiddleware: async (page) => {
      await abTestingClient.recordInteraction('page_view', page, 1);
    },
    clickMiddleware: async (element, targetId) => {
      await abTestingClient.recordInteraction('click', targetId || element, 1);
    },
  };
}

// Example 7: Export experiment data for analysis
export async function exportExperimentData() {
  try {
    const data = abTestingClient.exportExperimentData();
    return data;
  } catch (error) {
    console.error('Failed to export experiment data:', error);
    return null;
  }
}

// Example 8: Real-time A/B testing dashboard data
export function createRealTimeDashboard() {
  const updateInterval = 30000;
  return {
    start: (callback) => {
      const interval = setInterval(async () => {
        try {
          const dashboard = await abTestingClient.getDashboard();
          const metrics = await abTestingClient.getMetrics();
          callback({
            dashboard,
            recentMetrics: metrics.filter((m) => new Date(m.recorded_at) > new Date(Date.now() - updateInterval)),
            timestamp: new Date().toISOString(),
          });
        } catch (error) {
          console.error('Failed to update dashboard data:', error);
        }
      }, updateInterval);
      return () => clearInterval(interval);
    },
  };
}

export default {
  config: ABTestingConfig,
  client: abTestingClient,
  examples: {
    getSimilarUsersWithABTesting,
    trackUserInteraction,
    getCurrentUserExperimentStatus,
    initializeABTestingSession,
    exportExperimentData,
  },
  middleware: createABTestingMiddleware(),
  realTimeDashboard: createRealTimeDashboard(),
};
