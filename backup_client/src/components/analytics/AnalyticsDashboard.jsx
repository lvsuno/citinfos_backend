/**
 * AnalyticsDashboard Component
 * Comprehensive admin dashboard for viewing all analytics including PostSee data
 */

import React, { useState, useEffect } from 'react';
import analyticsAPI from '../../services/analyticsAPI';

const AnalyticsDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [postAnalytics, setPostAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('week');
  const [selectedMetric, setSelectedMetric] = useState('overview');

  const periods = [
    { value: 'day', label: 'Last 24 Hours' },
    { value: 'week', label: 'Last Week' },
    { value: 'month', label: 'Last Month' },
    { value: 'quarter', label: 'Last Quarter' },
    { value: 'year', label: 'Last Year' }
  ];

  const metrics = [
    { value: 'overview', label: 'Overview' },
    { value: 'posts', label: 'Post Analytics' },
    { value: 'engagement', label: 'Engagement' },
    { value: 'users', label: 'User Behavior' }
  ];

  useEffect(() => {
    loadAnalytics();
  }, [selectedPeriod]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const [contentAnalytics, postViewAnalytics] = await Promise.all([
        analyticsAPI.getContentAnalyticsSummary(selectedPeriod),
        analyticsAPI.getPostViewAnalytics(null, selectedPeriod)
      ]);

      setAnalytics(contentAnalytics);
      setPostAnalytics(postViewAnalytics);
    } catch (err) {
      setError('Failed to load analytics data');
      console.error('Analytics loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncAnalytics = async () => {
    try {
      setLoading(true);
      await analyticsAPI.syncAnalytics();
      await loadAnalytics();
    } catch (err) {
      setError('Failed to sync analytics');
      console.error('Analytics sync error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num?.toString() || '0';
  };

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  if (loading && !analytics) {
    return (
      <div className="analytics-dashboard loading">
        <div className="loading-spinner">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-dashboard error">
        <div className="error-message">{error}</div>
        <button onClick={loadAnalytics} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h1>Analytics Dashboard</h1>
        <div className="dashboard-controls">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="period-selector"
          >
            {periods.map(period => (
              <option key={period.value} value={period.value}>
                {period.label}
              </option>
            ))}
          </select>

          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="metric-selector"
          >
            {metrics.map(metric => (
              <option key={metric.value} value={metric.value}>
                {metric.label}
              </option>
            ))}
          </select>

          <button
            onClick={handleSyncAnalytics}
            disabled={loading}
            className="sync-button"
          >
            {loading ? 'Syncing...' : 'Sync Data'}
          </button>
        </div>
      </div>

      {selectedMetric === 'overview' && (
        <div className="overview-section">
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Total Views</h3>
              <div className="stat-value">
                {formatNumber(postAnalytics?.total_views || 0)}
              </div>
              <div className="stat-change">
                {postAnalytics?.views_change_percentage && (
                  <span className={postAnalytics.views_change_percentage > 0 ? 'positive' : 'negative'}>
                    {postAnalytics.views_change_percentage > 0 ? '+' : ''}{postAnalytics.views_change_percentage.toFixed(1)}%
                  </span>
                )}
              </div>
            </div>

            <div className="stat-card">
              <h3>Unique Viewers</h3>
              <div className="stat-value">
                {formatNumber(postAnalytics?.unique_viewers || 0)}
              </div>
            </div>

            <div className="stat-card">
              <h3>Avg. View Duration</h3>
              <div className="stat-value">
                {formatDuration(postAnalytics?.avg_view_duration || 0)}
              </div>
            </div>

            <div className="stat-card">
              <h3>Engagement Rate</h3>
              <div className="stat-value">
                {(postAnalytics?.engagement_rate || 0).toFixed(1)}%
              </div>
            </div>
          </div>

          <div className="chart-section">
            <h3>Views Over Time</h3>
            {postAnalytics?.daily_views && (
              <div className="simple-chart">
                {postAnalytics.daily_views.map((day, index) => (
                  <div key={index} className="chart-bar">
                    <div
                      className="bar"
                      style={{ height: `${(day.views / Math.max(...postAnalytics.daily_views.map(d => d.views))) * 100}%` }}
                    ></div>
                    <div className="bar-label">{new Date(day.date).toLocaleDateString()}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {selectedMetric === 'posts' && (
        <div className="posts-section">
          <h3>Top Performing Posts</h3>
          {postAnalytics?.top_posts && (
            <div className="posts-table">
              <table>
                <thead>
                  <tr>
                    <th>Post</th>
                    <th>Views</th>
                    <th>Avg. Duration</th>
                    <th>Engagement</th>
                    <th>Scroll Depth</th>
                  </tr>
                </thead>
                <tbody>
                  {postAnalytics.top_posts.map((post, index) => (
                    <tr key={index}>
                      <td>
                        <div className="post-info">
                          <div className="post-title">{post.title || `Post ${post.post_id}`}</div>
                          <div className="post-meta">{post.author || 'Unknown Author'}</div>
                        </div>
                      </td>
                      <td>{formatNumber(post.views)}</td>
                      <td>{formatDuration(post.avg_duration)}</td>
                      <td>{(post.engagement_rate || 0).toFixed(1)}%</td>
                      <td>{(post.avg_scroll_depth || 0).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {selectedMetric === 'engagement' && (
        <div className="engagement-section">
          <div className="engagement-stats">
            <div className="stat-group">
              <h3>Click Interactions</h3>
              <div className="stat-value">{formatNumber(postAnalytics?.total_clicks || 0)}</div>
            </div>

            <div className="stat-group">
              <h3>Media Interactions</h3>
              <div className="stat-value">{formatNumber(postAnalytics?.total_media_interactions || 0)}</div>
            </div>

            <div className="stat-group">
              <h3>Scroll Engagement</h3>
              <div className="stat-value">{(postAnalytics?.avg_scroll_percentage || 0).toFixed(1)}%</div>
            </div>
          </div>

          {postAnalytics?.engagement_sources && (
            <div className="sources-breakdown">
              <h3>Traffic Sources</h3>
              <div className="sources-list">
                {Object.entries(postAnalytics.engagement_sources).map(([source, count]) => (
                  <div key={source} className="source-item">
                    <span className="source-name">{source}</span>
                    <span className="source-count">{formatNumber(count)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {selectedMetric === 'users' && (
        <div className="users-section">
          <h3>User Behavior Insights</h3>

          {analytics?.device_breakdown && (
            <div className="device-breakdown">
              <h4>Device Types</h4>
              <div className="device-stats">
                {Object.entries(analytics.device_breakdown).map(([device, count]) => (
                  <div key={device} className="device-stat">
                    <span className="device-name">{device}</span>
                    <span className="device-count">{formatNumber(count)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {postAnalytics?.user_retention && (
            <div className="retention-analysis">
              <h4>User Retention</h4>
              <div className="retention-metrics">
                <div className="retention-metric">
                  <span>Return Visitors</span>
                  <span>{(postAnalytics.user_retention.return_rate || 0).toFixed(1)}%</span>
                </div>
                <div className="retention-metric">
                  <span>Avg. Session Duration</span>
                  <span>{formatDuration(postAnalytics.user_retention.avg_session_duration || 0)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
