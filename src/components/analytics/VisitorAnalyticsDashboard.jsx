/**
 * Visitor Analytics Dashboard Component
 *
 * Main dashboard for visitor analytics
 * Combines all analytics components into a comprehensive view
 */

import React, { useState, useEffect } from 'react';
import VisitorStatsCard from './VisitorStatsCard';
import VisitorTrendsChart from './VisitorTrendsChart';
import DivisionBreakdown from './DivisionBreakdown';
import RealtimeVisitorCounter from './RealtimeVisitorCounter';
import visitorAnalyticsAPI from '../../services/visitorAnalyticsAPI';
import './VisitorAnalyticsDashboard.css';

const VisitorAnalyticsDashboard = ({ communityId = null }) => {
    const [loading, setLoading] = useState(true);
    const [dateRange, setDateRange] = useState('week'); // 'today', 'week', 'month'
    const [stats, setStats] = useState(null);
    const [trends, setTrends] = useState(null);
    const [divisions, setDivisions] = useState(null);
    const [conversions, setConversions] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadAnalytics();
    }, [dateRange, communityId]);

    const loadAnalytics = async () => {
        try {
            setLoading(true);
            setError(null);

            // Determine date range
            const endDate = new Date();
            const startDate = new Date();
            let interval = 'day';

            if (dateRange === 'today') {
                startDate.setHours(0, 0, 0, 0);
                interval = 'hour';
            } else if (dateRange === 'week') {
                startDate.setDate(endDate.getDate() - 7);
                interval = 'day';
            } else if (dateRange === 'month') {
                startDate.setDate(endDate.getDate() - 30);
                interval = 'day';
            }

            const params = {
                start_date: formatDate(startDate),
                end_date: formatDate(endDate),
                community_id: communityId,
            };

            // Load data in parallel
            const [statsData, trendsData, divisionsData, conversionsData] = await Promise.all([
                loadStats(),
                visitorAnalyticsAPI.getTrends({ ...params, interval }),
                visitorAnalyticsAPI.getDivisionBreakdown(params),
                visitorAnalyticsAPI.getConversions(params),
            ]);

            setStats(statsData);
            setTrends(trendsData);
            setDivisions(divisionsData);
            setConversions(conversionsData);
        } catch (err) {
            console.error('Error loading analytics:', err);
            setError(err.message || 'Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    };

    const loadStats = async () => {
        if (dateRange === 'today') {
            return await visitorAnalyticsAPI.getTodayStats(communityId);
        } else if (dateRange === 'week') {
            return await visitorAnalyticsAPI.getWeeklyStats(communityId);
        } else if (dateRange === 'month') {
            return await visitorAnalyticsAPI.getMonthlyStats(communityId);
        }
    };

    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    const formatTrendsData = (trendsData) => {
        if (!trendsData || !Array.isArray(trendsData)) return null;

        return {
            labels: trendsData.map(item => item.label || item.date),
            total: trendsData.map(item => item.total_visitors || 0),
            authenticated: trendsData.map(item => item.authenticated_visitors || 0),
            anonymous: trendsData.map(item => item.anonymous_visitors || 0),
        };
    };

    const formatDivisionsData = (divisionsData) => {
        if (!divisionsData || !divisionsData.divisions) return [];
        return divisionsData.divisions.slice(0, 10); // Top 10
    };

    const handleDateRangeChange = (range) => {
        setDateRange(range);
    };

    const handleExport = async () => {
        try {
            const endDate = new Date();
            const startDate = new Date();

            if (dateRange === 'week') {
                startDate.setDate(endDate.getDate() - 7);
            } else if (dateRange === 'month') {
                startDate.setDate(endDate.getDate() - 30);
            }

            const params = {
                start_date: formatDate(startDate),
                end_date: formatDate(endDate),
                community_id: communityId,
            };

            const blob = await visitorAnalyticsAPI.exportCSV(params);

            // Download the file
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `visitor-analytics-${dateRange}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            console.error('Error exporting data:', err);
        }
    };

    if (error) {
        return (
            <div className="visitor-analytics-dashboard error">
                <div className="error-message">
                    <span className="error-icon">⚠️</span>
                    <p>{error}</p>
                    <button onClick={loadAnalytics} className="retry-button">
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="visitor-analytics-dashboard">
            <div className="dashboard-header">
                <h2 className="dashboard-title">Visitor Analytics</h2>
                <div className="dashboard-controls">
                    <div className="date-range-selector">
                        <button
                            className={`range-button ${dateRange === 'today' ? 'active' : ''}`}
                            onClick={() => handleDateRangeChange('today')}
                        >
                            Today
                        </button>
                        <button
                            className={`range-button ${dateRange === 'week' ? 'active' : ''}`}
                            onClick={() => handleDateRangeChange('week')}
                        >
                            7 Days
                        </button>
                        <button
                            className={`range-button ${dateRange === 'month' ? 'active' : ''}`}
                            onClick={() => handleDateRangeChange('month')}
                        >
                            30 Days
                        </button>
                    </div>
                    <button onClick={handleExport} className="export-button">
                        📥 Export CSV
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="stats-grid">
                <VisitorStatsCard
                    title="Total Visitors"
                    value={stats?.total_unique_visitors}
                    change={stats?.change_percentage}
                    changeType="increase"
                    icon="👥"
                    subtitle={`vs previous ${dateRange}`}
                    loading={loading}
                />
                <VisitorStatsCard
                    title="Authenticated"
                    value={stats?.authenticated_visitors}
                    change={stats?.authenticated_change}
                    changeType="increase"
                    icon="✓"
                    subtitle="Logged in users"
                    loading={loading}
                />
                <VisitorStatsCard
                    title="Anonymous"
                    value={stats?.anonymous_visitors}
                    change={stats?.anonymous_change}
                    changeType="neutral"
                    icon="👤"
                    subtitle="Guest visitors"
                    loading={loading}
                />
                <VisitorStatsCard
                    title="Conversion Rate"
                    value={conversions?.conversion_rate
                        ? `${conversions.conversion_rate.toFixed(1)}%`
                        : '0%'}
                    change={conversions?.rate_change}
                    changeType="increase"
                    icon="📈"
                    subtitle="Anonymous → Auth"
                    loading={loading}
                />
            </div>

            {/* Main Grid */}
            <div className="analytics-grid">
                {/* Trends Chart */}
                <div className="grid-item full-width">
                    <VisitorTrendsChart
                        data={formatTrendsData(trends)}
                        type="line"
                        title={`Visitor Trends (${dateRange === 'today' ? 'Hourly' : 'Daily'})`}
                        loading={loading}
                    />
                </div>

                {/* Division Breakdown */}
                <div className="grid-item">
                    <DivisionBreakdown
                        data={formatDivisionsData(divisions)}
                        loading={loading}
                    />
                </div>

                {/* Real-time Counter */}
                <div className="grid-item">
                    <RealtimeVisitorCounter communityId={communityId} />
                </div>
            </div>
        </div>
    );
};

export default VisitorAnalyticsDashboard;
