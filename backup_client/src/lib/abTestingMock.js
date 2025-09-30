// Mock A/B Testing Client Library (Clean JS)
// Provides all A/B testing functionality on the client side

import { useState } from 'react';

class ABTestingMockClient {
  constructor() {
    this.experiments = new Map();
    this.assignments = new Map();
    this.metrics = new Map();
    this.currentUserId = 'mock-user-123';
    this.manualAlgorithm = null;
    this.initializeMockData();
  }

  initializeMockData() {
    const mockExperiments = [
      {
        id: 'exp-001',
        name: 'Collaborative vs Content-Based Filtering',
        description: 'Testing collaborative filtering against content-based similarity',
        control_algorithm: 'collaborative_filtering',
        test_algorithm: 'content_based',
        traffic_split: 0.5,
        status: 'active',
        start_date: '2025-07-01T00:00:00Z',
        end_date: null,
        created_at: '2025-07-01T00:00:00Z',
        updated_at: '2025-07-01T00:00:00Z',
        created_by: 'admin',
        is_active: true,
      },
      {
        id: 'exp-002',
        name: 'Jaccard vs Hybrid Similarity',
        description: 'Comparing Jaccard similarity with hybrid approach',
        control_algorithm: 'jaccard_similarity',
        test_algorithm: 'hybrid',
        traffic_split: 0.6,
        status: 'active',
        start_date: '2025-07-05T00:00:00Z',
        end_date: null,
        created_at: '2025-07-05T00:00:00Z',
        updated_at: '2025-07-05T00:00:00Z',
        created_by: 'admin',
        is_active: true,
      },
    ];

    mockExperiments.forEach((exp) => this.experiments.set(exp.id, exp));
    this.assignUserToExperiments();
  }

  assignUserToExperiments() {
    const user = this.currentUserId;
    Array.from(this.experiments.values()).forEach((experiment) => {
      const id = `${user}-${experiment.id}`;
      const group = Math.random() < experiment.traffic_split ? 'test' : 'control';
      const assignment = {
        id,
        user,
        username: 'mock-user',
        experiment: experiment.id,
        experiment_name: experiment.name,
        group,
        assigned_at: new Date().toISOString(),
      };
      this.assignments.set(id, assignment);
    });
  }

  async getDashboard() {
    const activeExperiments = Array.from(this.experiments.values()).filter((e) => e.status === 'active').length;
    const totalAssignments = this.assignments.size;
    const recentMetrics = Array.from(this.metrics.values())
      .flat()
      .filter((m) => new Date(m.recorded_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)).length;

    return {
      status: 'ok',
      dashboard: {
        summary: {
          active_experiments: activeExperiments,
          total_assignments: totalAssignments,
          recent_metrics: recentMetrics,
        },
        experiments: Array.from(this.experiments.values()).map((exp) => ({
          id: exp.id,
          name: exp.name,
          status: exp.status,
          control_algorithm: exp.control_algorithm,
          test_algorithm: exp.test_algorithm,
          traffic_split: exp.traffic_split,
          control_users: Math.floor(Math.random() * 100) + 50,
          test_users: Math.floor(Math.random() * 100) + 50,
          total_users: Math.floor(Math.random() * 200) + 100,
          created_at: exp.created_at,
          start_date: exp.start_date,
          end_date: exp.end_date,
        })),
      },
    };
  }

  async getSimilarUsers(userId) {
    const targetUserId = userId || this.currentUserId;

    let algorithmUsed = this.manualAlgorithm || 'collaborative_filtering';
    let experimentGroup = 'manual';

    if (!this.manualAlgorithm) {
      experimentGroup = undefined;
      for (const assignment of this.assignments.values()) {
        if (assignment.user === targetUserId) {
          const experiment = this.experiments.get(assignment.experiment);
          if (experiment && experiment.status === 'active') {
            algorithmUsed = assignment.group === 'control' ? experiment.control_algorithm : experiment.test_algorithm;
            experimentGroup = assignment.group;
            break;
          }
        }
      }
    }

    const users = this.generateMockSimilarUsers(algorithmUsed);
    await this.recordMetric('similarity_request', 1, algorithmUsed);

    return {
      users,
      algorithm_used: algorithmUsed,
      experiment_group: experimentGroup,
    };
  }

  generateMockSimilarUsers(algorithm) {
    const algorithms = {
      collaborative_filtering: { baseScore: 0.75, variation: 0.2 },
      content_based: { baseScore: 0.68, variation: 0.18 },
      jaccard_similarity: { baseScore: 0.62, variation: 0.2 },
      hybrid: { baseScore: 0.8, variation: 0.15 },
    };

    const config = algorithms[algorithm] || algorithms.collaborative_filtering;

    return Array.from({ length: 9 }, (_, i) => {
      const score = Math.min(1, Math.max(0, config.baseScore + (Math.random() - 0.5) * config.variation));
      return {
        id: `user-${i + 1}`,
        username: `user${i + 1}`,
        profile_picture: `https://api.dicebear.com/7.x/identicon/svg?seed=${i + 1}`,
        similarity_score: score,
        similarity_type: algorithm,
        common_interests: ['Music', 'Travel', 'Sports', 'Coding', 'Art'].slice(0, Math.floor(Math.random() * 4) + 1),
        mutual_connections: Math.floor(Math.random() * 15) + 1,
      };
    }).sort((a, b) => b.similarity_score - a.similarity_score);
  }

  async recordInteraction(interactionType, targetUser, value = 1) {
    // Determine algorithm used for current user
    let algorithmUsed = 'collaborative_filtering';
    for (const assignment of this.assignments.values()) {
      if (assignment.user === this.currentUserId) {
        const experiment = this.experiments.get(assignment.experiment);
        if (experiment && experiment.status === 'active') {
          algorithmUsed = assignment.group === 'control' ? experiment.control_algorithm : experiment.test_algorithm;
          break;
        }
      }
    }
    await this.recordMetric(interactionType, value, algorithmUsed, { target_user: targetUser });
    return { status: 'ok', value, algorithm: algorithmUsed };
  }

  async recordMetric(metricType, value, algorithm_used, metadata = {}) {
    const experiments = Array.from(this.experiments.values());
    const exp = experiments[0];
    const metric = {
      id: `metric-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      experiment: exp?.id || 'default',
      experiment_name: exp?.name || 'Default Experiment',
      user: this.currentUserId,
      username: 'mock-user',
      metric_type: metricType,
      value,
      count: 1,
      algorithm_used,
      recorded_at: new Date().toISOString(),
      metadata,
    };

    const list = this.metrics.get(metric.experiment) || [];
    list.push(metric);
    this.metrics.set(metric.experiment, list);
  }

  async getExperiments() {
    return Array.from(this.experiments.values());
  }

  async getExperiment(id) {
    return this.experiments.get(id) || null;
  }

  async getUserAssignment() {
    return Array.from(this.assignments.values()).filter((a) => a.user === this.currentUserId);
  }

  async getMetrics(experimentId) {
    if (experimentId) return this.metrics.get(experimentId) || [];
    return Array.from(this.metrics.values()).flat();
  }

  setAlgorithm(algorithm) {
    const available = ['collaborative_filtering', 'content_based', 'jaccard_similarity', 'hybrid'];
    if (!available.includes(algorithm)) throw new Error(`Invalid algorithm: ${algorithm}`);
    this.manualAlgorithm = algorithm;
  }

  clearAlgorithm() {
    this.manualAlgorithm = null;
  }

  getAvailableAlgorithms() {
    return [
      { value: 'collaborative_filtering', label: 'Collaborative Filtering', description: 'Behavior-based' },
      { value: 'content_based', label: 'Content-Based', description: 'Content similarity' },
      { value: 'jaccard_similarity', label: 'Jaccard Similarity', description: 'Set similarity' },
      { value: 'hybrid', label: 'Hybrid', description: 'Best of both' },
    ];
  }

  simulateAlgorithmPerformance(algorithm) {
    const performances = {
      collaborative_filtering: { response_time: 120, accuracy: 0.78, engagement_rate: 0.35 },
      content_based: { response_time: 95, accuracy: 0.72, engagement_rate: 0.3 },
      jaccard_similarity: { response_time: 80, accuracy: 0.68, engagement_rate: 0.28 },
      hybrid: { response_time: 150, accuracy: 0.82, engagement_rate: 0.4 },
    };
    const base = performances[algorithm] || performances.collaborative_filtering;
    return {
      response_time: Math.max(50, Math.round(base.response_time + (Math.random() * 20 - 10))),
      accuracy: Math.min(1, Math.max(0, base.accuracy + (Math.random() * 0.1 - 0.05))),
      engagement_rate: Math.min(1, Math.max(0, base.engagement_rate + (Math.random() * 0.1 - 0.05))),
    };
  }

  exportExperimentData() {
    return {
      experiments: Array.from(this.experiments.values()),
      assignments: Array.from(this.assignments.values()),
      metrics: Array.from(this.metrics.entries()).reduce((acc, [k, v]) => {
        acc[k] = v;
        return acc;
      }, {}),
    };
  }
}

// Singleton instance
export const abTestingClient = new ABTestingMockClient();

// React Hook for A/B Testing
export function useABTesting() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getSimilarUsers = async (userId) => {
    setLoading(true);
    setError(null);
    try {
      return await abTestingClient.getSimilarUsers(userId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const recordInteraction = async (type, targetUser, value) => {
    try {
      return await abTestingClient.recordInteraction(type, targetUser, value);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  const getDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      return await abTestingClient.getDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const setAlgorithm = (algorithm) => {
    try {
      abTestingClient.setAlgorithm(algorithm);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  };

  const clearAlgorithm = () => {
    abTestingClient.clearAlgorithm();
  };

  const getAvailableAlgorithms = () => abTestingClient.getAvailableAlgorithms();

  return {
    getSimilarUsers,
    recordInteraction,
    getDashboard,
    setAlgorithm,
    clearAlgorithm,
    getAvailableAlgorithms,
    loading,
    error,
  };
}

export default abTestingClient;
