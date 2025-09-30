import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Card, CardHeader, CardContent } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Users, Eye, Activity, Server, Search, Zap, Clock, Globe, Shield, CheckCircle, XCircle } from 'lucide-react';
import analyticsAPI from '../../services/analyticsAPI';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

// Memoized chart components to prevent unnecessary re-renders
// Chart components without memo
const SimpleBarChart = ({ data, xKey, yKey, title, color = "#8884d8" }) => {
  if (!data || data.length === 0) {
    return <div className="text-center text-gray-500">No data available for {title}</div>;
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Bar dataKey={yKey} fill={color} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

const SimplePieChart = ({ data, title, colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300'] }) => {
  if (!data || data.length === 0) {
    return <div className="text-center text-gray-500">No data available for {title}</div>;
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
            label
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

const SimplePieChartAlt = ({ data, dataKey, nameKey, title }) => (
  <ResponsiveContainer width="100%" height="100%">
    <PieChart>
      <Pie
        data={data}
        cx="50%"
        cy="50%"
        labelLine={false}
        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
        outerRadius={80}
        fill="#8884d8"
        dataKey={dataKey}
      >
        {data.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
        ))}
      </Pie>
      <Tooltip />
    </PieChart>
  </ResponsiveContainer>
);

const ComprehensiveAnalyticsDashboard = () => {
  console.log('🔄 ComprehensiveAnalyticsDashboard component starting...');

  // Test error to see if error boundary catches it
  // throw new Error('Test error - ComprehensiveAnalyticsDashboard intentional failure');

  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [analytics, setAnalytics] = useState({
    overview: null,
    content: null,
    users: null,
    equipment: null,
    search: null,
    authentication: null,
    realtime: null,
    topContent: null,
    systemPerformance: null,
    userBehavior: null,
    searchTrends: null,
    postSeeAnalytics: null,
    contentSummary: null
  });
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [refreshCount, setRefreshCount] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshDebounce, setRefreshDebounce] = useState(false);
  const mountedRef = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const loadAllAnalytics = useCallback(async (silentRefresh = false) => {
    // Don't proceed if component is unmounted
    if (!mountedRef.current) return;

    try {
      console.log('🔄 loadAllAnalytics called', { silentRefresh, timestamp: new Date().toISOString() });
      // Only show loading spinner on initial load, not on refresh
      if (!silentRefresh) {
        setLoading(true);
      } else {
        setIsRefreshing(true);
      }
      setError(null);

      const [
        overview,
        content,
        users,
        equipment,
        search,
        authentication,
        realtime,
        topContent,
        systemPerformance,
        userBehavior,
        searchTrends,
        postSeeAnalytics
      ] = await Promise.all([
        analyticsAPI.getOverviewAnalytics(),
        analyticsAPI.getContentAnalytics(),
        analyticsAPI.getUserAnalytics(),
        analyticsAPI.getEquipmentAnalytics(),
        analyticsAPI.getSearchAnalytics(),
        analyticsAPI.getAuthenticationAnalytics(),
        analyticsAPI.getRealtimeAnalytics(),
        analyticsAPI.getTopContent(),
        analyticsAPI.getSystemPerformance(),
        analyticsAPI.getUserBehavior(),
        analyticsAPI.getSearchTrends(),
        analyticsAPI.getPostSeeAnalytics()
      ]);

      // Set analytics data - this should complete even if component is unmounting
      console.log('📊 Setting analytics data, mounted:', mountedRef.current);
      setAnalytics({
        overview,
        content,
        users,
        equipment,
        search,
        authentication,
        realtime,
        topContent,
        systemPerformance,
        userBehavior,
        searchTrends,
        postSeeAnalytics,
        contentSummary: overview
      });

      setLastRefresh(new Date());
      setRefreshCount(prev => prev + 1);

    } catch (error) {
      // Always set error state, even if component unmounted, to prevent stuck loading
      setError(`Failed to load analytics: ${error.message}`);
      console.error('Analytics loading error:', error);

      if (!mountedRef.current) {
        console.warn('⚠️ Component unmounted during error handling, but error state was set');
      }
    } finally {
      console.log('🔍 Finally block:', { mounted: mountedRef.current });

      // Always clear loading states to prevent stuck loading, even if unmounted
      console.log('🔧 Setting loading to false');
      setLoading(false);
      setIsRefreshing(false);

      if (!mountedRef.current) {
        console.warn('⚠️ Component unmounted during data loading, but cleared loading states');
      }
    }
  }, []);

  useEffect(() => {
    loadAllAnalytics();
  }, []); // Remove loadAllAnalytics dependency to prevent double execution

  // Auto-refresh functionality for pseudo real-time updates
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadAllAnalytics(true); // Pass true for silent refresh
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, loadAllAnalytics]);

  const StatCard = ({ title, value, icon: Icon, color = "blue", trend = null }) => {
    const colorClasses = {
      blue: "text-blue-500",
      green: "text-green-500",
      yellow: "text-yellow-500",
      red: "text-red-500",
      purple: "text-purple-500",
      indigo: "text-indigo-500",
    };

    return (
      <Card className="p-4 transition-all duration-300 ease-in-out">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold transition-all duration-500 ease-in-out">{value || 'N/A'}</p>
            {trend && (
              <p className={`text-sm transition-all duration-500 ease-in-out ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {trend > 0 ? '+' : ''}{trend}%
              </p>
            )}
          </div>
          <Icon className={`h-8 w-8 ${colorClasses[color] || colorClasses.blue} transition-all duration-300 ease-in-out`} />
        </div>
      </Card>
    );
  };

  const OverviewDashboard = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Users"
          value={analytics.overview?.total_users || analytics.users?.total_users}
          icon={Users}
          color="blue"
        />
        <StatCard
          title="Active Today"
          value={analytics.overview?.active_users_today || analytics.overview?.active_today || analytics.realtime?.active_users}
          icon={Activity}
          color="green"
        />
        <StatCard
          title="Total Views"
          value={analytics.postSeeAnalytics?.summary?.total_views || analytics.content?.total_views}
          icon={Eye}
          color="purple"
        />
        <StatCard
          title="System Load"
          value={analytics.overview?.system_load !== undefined ? `${(analytics.overview.system_load * 100).toFixed(1)}%` : (analytics.systemPerformance?.cpu_usage ? `${analytics.systemPerformance.cpu_usage}%` : 'N/A')}
          icon={Server}
          color="orange"
        />
      </div>

      {/* PostSee Analytics - Views Trend */}
      {analytics.overview?.postsee_trend && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Eye className="h-5 w-5" />
              PostSee Views Trend (Last 7 Days)
            </h3>
          </CardHeader>
          <CardContent>
            <div className="h-40 transition-all duration-500 ease-in-out">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={analytics.overview.postsee_trend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '6px',
                      fontSize: '12px'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="views"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={{ fill: '#3B82F6', strokeWidth: 2, r: 3 }}
                    activeDot={{ r: 5, fill: '#1D4ED8' }}
                    name="Views"
                    animationDuration={800}
                    animationEasing="ease-in-out"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 flex justify-between text-xs text-gray-600 transition-all duration-500 ease-in-out">
              <span>Total Views: {analytics.overview.postsee_trend?.reduce((sum, day) => sum + (day.views || 0), 0) || 0}</span>
              <span>Peak Day: {(() => {
                const viewsArray = analytics.overview.postsee_trend?.map(d => d.views || 0) || [0];
                return viewsArray.length > 0 ? Math.max(...viewsArray.slice(0, 100)) : 0;
              })()} views</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Community Analytics */}
      {analytics.overview?.top_communities && analytics.overview.top_communities.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Users className="h-5 w-5" />
              Top Active Communities
            </h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(() => {
                // Remove duplicates from communities
                const uniqueCommunities = analytics.overview.top_communities.filter((community, index, self) =>
                  index === self.findIndex(c => c.name === community.name)
                );
                return uniqueCommunities.slice(0, 5).map((community, index) => (
                  <div key={community.name || index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                      <p className="font-medium">{community.name || `Community ${index + 1}`}</p>
                      <p className="text-sm text-gray-600 transition-all duration-500 ease-in-out">
                        {community.daily_active_members || 0} active members •
                        {community.total_threads_today || 0} threads •
                        {community.total_posts_today || 0} posts •
                        {community.total_comments_today || 0} comments today
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-blue-600 transition-all duration-500 ease-in-out">{community.daily_active_members || 0}</p>
                      <p className="text-xs text-gray-500">Active Members</p>
                    </div>
                  </div>
                ));
              })()}
            </div>

            <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t">
              <div className="text-center">
                <p className="text-xl font-bold text-blue-600">
                  {(() => {
                    // Count unique communities
                    const uniqueCommunities = analytics.overview.top_communities.filter((community, index, self) =>
                      index === self.findIndex(c => c.name === community.name)
                    );
                    return uniqueCommunities.length;
                  })()}
                </p>
                <p className="text-sm text-gray-600">Total Communities Tracked</p>
              </div>
              <div className="text-center">
                <p className="text-xl font-bold text-green-600 transition-all duration-500 ease-in-out">
                  {analytics.overview.top_communities?.reduce((sum, c) => sum + (c.daily_active_members || 0), 0) || 0}
                </p>
                <p className="text-sm text-gray-600">Total Active Members</p>
              </div>
              <div className="text-center">
                <p className="text-xl font-bold text-orange-600 transition-all duration-500 ease-in-out">
                  {analytics.overview.top_communities?.reduce((sum, c) => sum + (c.total_threads_today || 0), 0) || 0}
                </p>
                <p className="text-sm text-gray-600">Total Threads Today</p>
              </div>
              <div className="text-center">
                <p className="text-xl font-bold text-purple-600 transition-all duration-500 ease-in-out">
                  {analytics.overview.top_communities?.reduce((sum, c) => sum + (c.total_posts_today || 0), 0) || 0}
                </p>
                <p className="text-sm text-gray-600">Total Posts Today</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Content Summary */}
      {analytics.overview?.contentSummary && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Content Performance Summary
            </h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-xl font-bold">{analytics.overview.contentSummary.summary?.total_posts || 0}</p>
                <p className="text-sm text-gray-600">Total Posts</p>
              </div>
              <div className="text-center">
                <p className="text-xl font-bold">{analytics.overview.contentSummary.summary?.total_engagement || 0}</p>
                <p className="text-sm text-gray-600">Total Engagement</p>
              </div>
              <div className="text-center">
                <p className="text-xl font-bold">{analytics.overview.contentSummary.summary?.avg_engagement_rate || 0}%</p>
                <p className="text-sm text-gray-600">Avg Engagement</p>
              </div>
              <div className="text-center">
                <p className="text-xl font-bold">{analytics.overview.contentSummary.summary?.top_performing_posts || 0}</p>
                <p className="text-sm text-gray-600">Top Posts</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const UserAnalyticsDashboard = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Total Users"
          value={analytics.users?.total_users}
          icon={Users}
          color="blue"
        />
        <StatCard
          title="Active This Week"
          value={analytics.users?.active_this_week}
          icon={Activity}
          color="green"
        />
        <StatCard
          title="New This Month"
          value={analytics.users?.new_this_month}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {analytics.users?.daily_data && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">User Behavior Patterns</h3>
          </CardHeader>
          <CardContent>
            <div className="h-64 transition-all duration-500 ease-in-out">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={analytics.users.daily_data || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return `${date.getMonth() + 1}/${date.getDate()}`;
                    }}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => {
                      const date = new Date(value);
                      return date.toLocaleDateString();
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="active_users"
                    stroke="#3B82F6"
                    name="Active Users"
                    animationDuration={800}
                    animationEasing="ease-in-out"
                  />
                  <Line
                    type="monotone"
                    dataKey="total_sessions"
                    stroke="#10B981"
                    name="Total Sessions"
                    animationDuration={800}
                    animationEasing="ease-in-out"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {analytics.users?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600 transition-all duration-500 ease-in-out">
                {analytics.users.summary.total_active_days}
              </p>
              <p className="text-sm text-gray-600">Total Active Days</p>
            </div>
          </Card>

          <Card className="p-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600 transition-all duration-500 ease-in-out">
                {analytics.users.summary.total_sessions}
              </p>
              <p className="text-sm text-gray-600">Total Sessions</p>
            </div>
          </Card>

          <Card className="p-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600 transition-all duration-500 ease-in-out">
                {analytics.users.summary.avg_session_duration}s
              </p>
              <p className="text-sm text-gray-600">Avg Session Duration</p>
            </div>
          </Card>
        </div>
      )}
    </div>
  );

  const SystemDashboard = () => {
    const systemMetrics = analytics.systemPerformance;
    const performanceSummary = systemMetrics?.performance_summary || {};
    const metricsByType = systemMetrics?.metrics_by_type || {};

    return (
      <div className="space-y-6">
        {/* Key Performance Indicators */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            title="Avg Session Duration"
            value={performanceSummary.avg_session_duration ? `${performanceSummary.avg_session_duration.average?.toFixed(1)}s` : 'N/A'}
            icon={Clock}
            color="blue"
            trend={performanceSummary.avg_session_duration?.latest > performanceSummary.avg_session_duration?.average ?
              ((performanceSummary.avg_session_duration.latest - performanceSummary.avg_session_duration.average) / performanceSummary.avg_session_duration.average * 100).toFixed(1) : null}
          />
          <StatCard
            title="Active Sessions"
            value={performanceSummary.active_sessions?.latest !== undefined ? performanceSummary.active_sessions.latest : 'N/A'}
            icon={Users}
            color="green"
            trend={performanceSummary.active_sessions?.latest !== undefined && performanceSummary.active_sessions?.average !== undefined && performanceSummary.active_sessions.latest > performanceSummary.active_sessions.average ?
              ((performanceSummary.active_sessions.latest - performanceSummary.active_sessions.average) / Math.max(performanceSummary.active_sessions.average, 0.1) * 100).toFixed(1) : null}
          />
          <StatCard
            title="DB Query Time"
            value={performanceSummary.database_query_time ? `${(performanceSummary.database_query_time.latest / 1000).toFixed(1)}ms` : 'N/A'}
            icon={Server}
            color="orange"
            trend={performanceSummary.database_query_time?.latest < performanceSummary.database_query_time?.average ?
              -((performanceSummary.database_query_time.average - performanceSummary.database_query_time.latest) / performanceSummary.database_query_time.average * 100).toFixed(1) : null}
          />
          <StatCard
            title="Total DB Queries"
            value={performanceSummary.database_queries ? `${(performanceSummary.database_queries.latest / 1000).toFixed(0)}K` : 'N/A'}
            icon={Activity}
            color="purple"
          />
        </div>

        {/* Performance Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Activity className="h-5 w-5" />
                System Load Overview
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Active Users (Hourly)</span>
                  <span className="font-bold">{performanceSummary.active_users_hourly?.latest || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Concurrent Connections</span>
                  <span className="font-bold">{performanceSummary.concurrent_connections?.latest || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Cache Hit Rate</span>
                  <span className="font-bold">{performanceSummary.cache_hit_rate?.latest ? `${(performanceSummary.cache_hit_rate.latest * 100).toFixed(1)}%` : '0%'}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Server className="h-5 w-5" />
                Database Performance
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Query Count</span>
                  <span className="font-bold">{performanceSummary.database_queries?.count || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Avg Query Time</span>
                  <span className="font-bold">{performanceSummary.database_query_time ? `${(performanceSummary.database_query_time.average / 1000).toFixed(1)}ms` : 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Total Queries</span>
                  <span className="font-bold">{performanceSummary.database_queries ? `${(performanceSummary.database_queries.average / 1000).toFixed(0)}K` : 'N/A'}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Session Analytics
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Session Samples</span>
                  <span className="font-bold">{performanceSummary.avg_session_duration?.count || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Avg Duration</span>
                  <span className="font-bold">{performanceSummary.avg_session_duration ? `${performanceSummary.avg_session_duration.average.toFixed(1)}s` : 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Latest Duration</span>
                  <span className="font-bold">{performanceSummary.avg_session_duration ? `${performanceSummary.avg_session_duration.latest.toFixed(1)}s` : 'N/A'}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Database Query Time Chart */}
        {metricsByType.database_query_time && metricsByType.database_query_time.length > 0 && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Server className="h-5 w-5" />
                Database Query Performance Over Time
              </h3>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={metricsByType.database_query_time.slice(-20).map(item => ({
                    time: new Date(item.timestamp).toLocaleTimeString(),
                    query_time: item.value / 1000, // Convert to milliseconds
                    timestamp: item.timestamp
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="time"
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis label={{ value: 'Query Time (ms)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip
                      labelFormatter={(value) => `Time: ${value}`}
                      formatter={(value) => [`${value.toFixed(1)}ms`, 'Query Time']}
                    />
                    <Line
                      type="monotone"
                      dataKey="query_time"
                      stroke="#EF4444"
                      name="Query Time"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Active Sessions and Session Duration */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {metricsByType.active_sessions && metricsByType.active_sessions.length > 0 && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Active Sessions Over Time
                </h3>
              </CardHeader>
              <CardContent>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={metricsByType.active_sessions.slice(-15).map(item => ({
                      time: new Date(item.timestamp).toLocaleTimeString(),
                      sessions: item.value
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="time"
                        angle={-45}
                        textAnchor="end"
                        height={60}
                      />
                      <YAxis />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="sessions"
                        stroke="#10B981"
                        strokeWidth={2}
                        dot={{ r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}

          {metricsByType.avg_session_duration && metricsByType.avg_session_duration.length > 0 && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Average Session Duration
                </h3>
              </CardHeader>
              <CardContent>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={metricsByType.avg_session_duration.slice(-15).map(item => ({
                      time: new Date(item.timestamp).toLocaleTimeString(),
                      duration: item.value
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="time"
                        angle={-45}
                        textAnchor="end"
                        height={60}
                      />
                      <YAxis label={{ value: 'Duration (s)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => [`${value.toFixed(1)}s`, 'Duration']} />
                      <Line
                        type="monotone"
                        dataKey="duration"
                        stroke="#3B82F6"
                        strokeWidth={2}
                        dot={{ r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Database Queries Chart */}
        {metricsByType.database_queries && metricsByType.database_queries.length > 0 && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Total Database Queries Over Time
              </h3>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={metricsByType.database_queries.slice(-20).map(item => ({
                    time: new Date(item.timestamp).toLocaleTimeString(),
                    queries: item.value / 1000, // Convert to thousands for readability
                    timestamp: item.timestamp
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="time"
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis label={{ value: 'Queries (K)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip
                      labelFormatter={(value) => `Time: ${value}`}
                      formatter={(value) => [`${value.toFixed(0)}K`, 'Total Queries']}
                    />
                    <Line
                      type="monotone"
                      dataKey="queries"
                      stroke="#8B5CF6"
                      name="Database Queries"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* System Health Summary */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Shield className="h-5 w-5" />
              System Health Summary
            </h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-2xl font-bold text-blue-600">
                  {systemMetrics?.total_metrics || 0}
                </p>
                <p className="text-sm text-blue-800">Total Metrics Collected</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">
                  {performanceSummary.cache_hit_rate ? `${(performanceSummary.cache_hit_rate.average * 100).toFixed(1)}%` : '0%'}
                </p>
                <p className="text-sm text-green-800">Cache Hit Rate</p>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <p className="text-2xl font-bold text-yellow-600">
                  {performanceSummary.database_query_time ? `${(performanceSummary.database_query_time.latest / 1000).toFixed(0)}ms` : 'N/A'}
                </p>
                <p className="text-sm text-yellow-800">Latest Query Time</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">
                  {systemMetrics?.timestamp ? new Date(systemMetrics.timestamp).toLocaleTimeString() : 'N/A'}
                </p>
                <p className="text-sm text-purple-800">Last Updated</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const ContentDashboard = () => {
    // Calculate summary stats from top content data
    const contentSummary = analytics.topContent?.top_content ? {
      total_posts: analytics.topContent.top_content.length,
      total_views: analytics.topContent.top_content.reduce((sum, post) => sum + (post.view_count || 0), 0),
      total_unique_viewers: analytics.topContent.top_content.reduce((sum, post) => sum + (post.unique_viewers || 0), 0),
      avg_duration: analytics.topContent.top_content.reduce((sum, post) => sum + (post.avg_duration || 0), 0) / analytics.topContent.top_content.length
    } : null;

    return (
      <div className="space-y-6">
        {analytics.topContent?.top_content && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">Top Performing Content</h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.topContent.top_content.slice(0, 5).map((post, index) => (
                  <div key={post.post_id || index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                      <p className="font-medium">Post #{post.post_id?.slice(0, 8) || `${index + 1}`}</p>
                      <p className="text-sm text-gray-600">
                        {post.view_count || 0} views • {post.unique_viewers || 0} unique viewers • {(post.avg_duration || 0).toFixed(1)}s avg duration
                      </p>
                      <p className="text-xs text-gray-500">Content Type: {post.content_type || 'post'}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-green-600">{post.view_count || 0}</p>
                      <p className="text-xs text-gray-500">Views</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {contentSummary && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">Content Analytics Overview</h3>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <p className="text-xl font-bold">{contentSummary.total_posts || 0}</p>
                  <p className="text-sm text-gray-600">Top Posts</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold">{contentSummary.total_views || 0}</p>
                  <p className="text-sm text-gray-600">Total Views</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold">{contentSummary.total_unique_viewers || 0}</p>
                  <p className="text-sm text-gray-600">Unique Viewers</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold">{(contentSummary.avg_duration || 0).toFixed(1)}s</p>
                  <p className="text-sm text-gray-600">Avg Duration</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {analytics.topContent?.top_content && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">Content Performance Chart</h3>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.topContent.top_content.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="post_id"
                      tickFormatter={(value) => `#${value.slice(0, 8)}`}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(value) => `Post: #${value.slice(0, 8)}`}
                      formatter={(value, name) => [value, name === 'view_count' ? 'Views' : name === 'unique_viewers' ? 'Unique Viewers' : name]}
                    />
                    <Legend />
                    <Bar dataKey="view_count" fill="#3B82F6" name="Views" />
                    <Bar dataKey="unique_viewers" fill="#10B981" name="Unique Viewers" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const SearchDashboard = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Total Searches"
          value={analytics.search?.total_searches}
          icon={Search}
          color="blue"
        />
        <StatCard
          title="Unique Queries"
          value={analytics.search?.unique_queries}
          icon={Zap}
          color="green"
        />
        <StatCard
          title="Avg Results"
          value={analytics.search?.avg_results}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {analytics.searchTrends && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Search Trends</h3>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={analytics.searchTrends.daily_searches || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="searches" stroke="#3B82F6" name="Daily Searches" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const AuthenticationDashboard = () => {
    const authData = analytics.authentication;
    const summary = authData?.summary || {};
    const dailyData = authData?.daily_data || [];

    // Calculate additional metrics
    const avgDailyAttempts = dailyData.length > 0 ?
      (dailyData.reduce((sum, day) => sum + day.total_attempts, 0) / dailyData.length).toFixed(0) : 0;

    const totalDays = dailyData.length;
    const peakDayAttempts = dailyData.length > 0 ?
      Math.max(...dailyData.map(day => day.total_attempts)) : 0;

    const recentTrend = dailyData.length >= 2 ?
      dailyData[dailyData.length - 1].total_attempts - dailyData[dailyData.length - 2].total_attempts : 0;

    return (
      <div className="space-y-6">
        {/* Key Authentication Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            title="Total Attempts"
            value={summary.total_attempts?.toLocaleString() || 0}
            icon={Shield}
            color="blue"
            trend={recentTrend > 0 ? ((recentTrend / Math.max(dailyData[dailyData.length - 2]?.total_attempts || 1, 1)) * 100).toFixed(1) : null}
          />
          <StatCard
            title="Success Rate"
            value={summary.success_rate ? `${summary.success_rate.toFixed(1)}%` : 'N/A'}
            icon={CheckCircle}
            color="green"
          />
          <StatCard
            title="Failed Logins"
            value={summary.failed_logins?.toLocaleString() || 0}
            icon={XCircle}
            color="red"
          />
          <StatCard
            title="Successful Logins"
            value={summary.successful_logins?.toLocaleString() || 0}
            icon={Users}
            color="purple"
          />
        </div>

        {/* Authentication Trends Chart */}
        {dailyData.length > 0 && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Authentication Trends Over Time
              </h3>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={dailyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => {
                        const date = new Date(value);
                        return `${date.getMonth() + 1}/${date.getDate()}`;
                      }}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(value) => {
                        const date = new Date(value);
                        return date.toLocaleDateString();
                      }}
                      formatter={(value, name) => [
                        value.toLocaleString(),
                        name === 'successful_logins' ? 'Successful' :
                        name === 'failed_logins' ? 'Failed' : 'Total'
                      ]}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="successful_logins"
                      stroke="#10B981"
                      name="Successful Logins"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="failed_logins"
                      stroke="#EF4444"
                      name="Failed Logins"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="total_attempts"
                      stroke="#3B82F6"
                      name="Total Attempts"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Success Rate Chart */}
        {dailyData.length > 0 && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Daily Success Rate
              </h3>
            </CardHeader>
            <CardContent>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={dailyData.map(day => ({
                    ...day,
                    success_rate: day.total_attempts > 0 ? ((day.successful_logins / day.total_attempts) * 100).toFixed(1) : 0
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => {
                        const date = new Date(value);
                        return `${date.getMonth() + 1}/${date.getDate()}`;
                      }}
                    />
                    <YAxis
                      domain={[90, 100]}
                      label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip
                      labelFormatter={(value) => {
                        const date = new Date(value);
                        return date.toLocaleDateString();
                      }}
                      formatter={(value) => [`${value}%`, 'Success Rate']}
                    />
                    <Line
                      type="monotone"
                      dataKey="success_rate"
                      stroke="#10B981"
                      strokeWidth={3}
                      dot={{ r: 5, fill: '#10B981' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Daily Breakdown Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Activity Summary
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Tracking Days</span>
                  <span className="font-bold">{totalDays}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Avg Daily Attempts</span>
                  <span className="font-bold">{avgDailyAttempts}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Peak Day Attempts</span>
                  <span className="font-bold">{peakDayAttempts.toLocaleString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <CheckCircle className="h-5 w-5" />
                Success Metrics
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Overall Success Rate</span>
                  <span className="font-bold text-green-600">{summary.success_rate?.toFixed(2) || 0}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Total Successful</span>
                  <span className="font-bold text-green-600">{summary.successful_logins?.toLocaleString() || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Best Day Rate</span>
                  <span className="font-bold text-green-600">
                    {dailyData.length > 0 ?
                      Math.max(...dailyData.map(day =>
                        day.total_attempts > 0 ? ((day.successful_logins / day.total_attempts) * 100) : 0
                      )).toFixed(1) : 0}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <XCircle className="h-5 w-5" />
                Failure Analysis
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Total Failed</span>
                  <span className="font-bold text-red-600">{summary.failed_logins?.toLocaleString() || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Failure Rate</span>
                  <span className="font-bold text-red-600">
                    {summary.success_rate ? (100 - summary.success_rate).toFixed(2) : 0}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Worst Day Failures</span>
                  <span className="font-bold text-red-600">
                    {dailyData.length > 0 ? Math.max(...dailyData.map(day => day.failed_logins)) : 0}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity Table */}
        {dailyData.length > 0 && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Recent Authentication Activity
              </h3>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Date</th>
                      <th className="text-right p-2">Total Attempts</th>
                      <th className="text-right p-2">Successful</th>
                      <th className="text-right p-2">Failed</th>
                      <th className="text-right p-2">Success Rate</th>
                      <th className="text-right p-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dailyData.slice(-7).reverse().map((day, index) => {
                      const successRate = day.total_attempts > 0 ? ((day.successful_logins / day.total_attempts) * 100) : 0;
                      const isGoodDay = successRate >= 95;

                      return (
                        <tr key={day.date || index} className="border-b hover:bg-gray-50">
                          <td className="p-2 font-medium">
                            {new Date(day.date).toLocaleDateString()}
                          </td>
                          <td className="p-2 text-right">{day.total_attempts.toLocaleString()}</td>
                          <td className="p-2 text-right text-green-600 font-medium">
                            {day.successful_logins.toLocaleString()}
                          </td>
                          <td className="p-2 text-right text-red-600 font-medium">
                            {day.failed_logins}
                          </td>
                          <td className="p-2 text-right font-bold">
                            <span className={successRate >= 95 ? 'text-green-600' : successRate >= 90 ? 'text-yellow-600' : 'text-red-600'}>
                              {successRate.toFixed(1)}%
                            </span>
                          </td>
                          <td className="p-2 text-right">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              isGoodDay ? 'bg-green-100 text-green-800' :
                              successRate >= 90 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {isGoodDay ? 'Excellent' : successRate >= 90 ? 'Good' : 'Needs Attention'}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* System Health Indicator */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Authentication System Health
            </h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="text-center">
                <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${
                  summary.success_rate >= 95 ? 'bg-green-100' : summary.success_rate >= 90 ? 'bg-yellow-100' : 'bg-red-100'
                }`}>
                  {summary.success_rate >= 95 ? (
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  ) : summary.success_rate >= 90 ? (
                    <Activity className="w-8 h-8 text-yellow-600" />
                  ) : (
                    <XCircle className="w-8 h-8 text-red-600" />
                  )}
                </div>
                <h4 className="font-bold text-lg mb-2">
                  {summary.success_rate >= 95 ? 'Excellent' : summary.success_rate >= 90 ? 'Good' : 'Needs Attention'}
                </h4>
                <p className="text-sm text-gray-600">
                  System performing {summary.success_rate >= 95 ? 'optimally' : summary.success_rate >= 90 ? 'well' : 'below expectations'}
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span>Last Updated:</span>
                  <span className="font-medium">
                    {authData?.timestamp ? new Date(authData.timestamp).toLocaleString() : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span>Data Range:</span>
                  <span className="font-medium">{totalDays} days</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span>Recent Trend:</span>
                  <span className={`font-medium ${recentTrend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {recentTrend >= 0 ? '↗' : '↘'} {Math.abs(recentTrend)} attempts
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const PostSeeDashboard = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Views"
          value={analytics.postSeeAnalytics?.summary?.total_views}
          icon={Eye}
          color="blue"
        />
        <StatCard
          title="Engaged Views"
          value={analytics.postSeeAnalytics?.summary?.engaged_views}
          icon={TrendingUp}
          color="green"
        />
        <StatCard
          title="Avg Duration"
          value={analytics.postSeeAnalytics?.summary?.avg_view_duration ? `${analytics.postSeeAnalytics.summary.avg_view_duration}s` : 'N/A'}
          icon={Clock}
          color="purple"
        />
        <StatCard
          title="Engagement Rate"
          value={analytics.postSeeAnalytics?.summary?.engagement_rate ? `${analytics.postSeeAnalytics.summary.engagement_rate}%` : 'N/A'}
          icon={Activity}
          color="orange"
        />
      </div>

      {analytics.postSeeAnalytics?.breakdowns && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">View Sources Breakdown</h3>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <SimpleBarChart
                data={analytics.postSeeAnalytics.breakdowns}
                xKey="source"
                yKey="value"
                title="Views"
                color="#3B82F6"
              />
            </div>
          </CardContent>
        </Card>
      )}

      {analytics.postSeeAnalytics?.hourly_distribution && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Hourly View Distribution</h3>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={analytics.postSeeAnalytics.hourly_distribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="views" stroke="#10B981" name="Views per Hour" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {analytics.postSeeAnalytics?.device_breakdown && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Device Type Breakdown</h3>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <SimplePieChart
                data={analytics.postSeeAnalytics.device_breakdown}
                title="Device Breakdown"
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  console.log('🔍 Render state:', { loading, error: !!error, analytics: !!analytics, analyticsKeys: analytics ? Object.keys(analytics) : 'none' });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={loadAllAnalytics}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Safety check for analytics data
  if (!analytics || typeof analytics !== 'object') {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-gray-500 mb-4">No analytics data available</p>
          <button
            onClick={loadAllAnalytics}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Load Analytics
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
              Analytics Dashboard
              {isRefreshing && (
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              )}
            </h1>
            <p className="text-gray-600">Comprehensive analytics and insights</p>
          </div>

          {/* Auto-refresh Controls */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="autoRefresh"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="autoRefresh" className="text-sm text-gray-700 flex items-center gap-1">
                Auto-refresh (30s)
                {autoRefresh && (
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                )}
              </label>
            </div>

            {lastRefresh && (
              <div className="flex flex-col items-end">
                <p className="text-xs text-gray-500">
                  Last updated: {lastRefresh.toLocaleTimeString()}
                </p>
                {refreshCount > 1 && (
                  <p className="text-xs text-green-600">
                    Updated {refreshCount - 1} time{refreshCount > 2 ? 's' : ''}
                  </p>
                )}
              </div>
            )}

            <button
              onClick={() => loadAllAnalytics(true)}
              disabled={isRefreshing}
              className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 transition-all duration-200"
            >
              {isRefreshing ? (
                <>
                  <div className="animate-spin h-3 w-3 border border-white border-t-transparent rounded-full"></div>
                  Updating...
                </>
              ) : (
                'Refresh Now'
              )}
            </button>
          </div>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="search">Search</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="authentication">Auth</TabsTrigger>
          <TabsTrigger value="postsee">PostSee</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewDashboard />
        </TabsContent>

        <TabsContent value="users">
          <UserAnalyticsDashboard />
        </TabsContent>

        <TabsContent value="content">
          <ContentDashboard />
        </TabsContent>

        <TabsContent value="search">
          <SearchDashboard />
        </TabsContent>

        <TabsContent value="system">
          <SystemDashboard />
        </TabsContent>

        <TabsContent value="authentication">
          <AuthenticationDashboard />
        </TabsContent>

        <TabsContent value="postsee">
          <PostSeeDashboard />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ComprehensiveAnalyticsDashboard;
