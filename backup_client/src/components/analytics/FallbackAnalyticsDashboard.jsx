import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { TrendingUp, Users, Eye, Activity, Server, Search, Zap, Clock, Globe, Shield } from 'lucide-react';
import analyticsAPI from '../../services/analyticsAPI';

const FallbackAnalyticsDashboard = () => {
  const [loading, setLoading] = useState(true);
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

  useEffect(() => {
    loadAllAnalytics();
  }, []);

  const loadAllAnalytics = async () => {
    try {
      setLoading(true);
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
        postSeeAnalytics,
        contentSummary
      ] = await Promise.allSettled([
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
        analyticsAPI.getPostViewAnalytics(),
        analyticsAPI.getContentAnalyticsSummary()
      ]);

      setAnalytics({
        overview: overview.status === 'fulfilled' ? overview.value : null,
        content: content.status === 'fulfilled' ? content.value : null,
        users: users.status === 'fulfilled' ? users.value : null,
        equipment: equipment.status === 'fulfilled' ? equipment.value : null,
        search: search.status === 'fulfilled' ? search.value : null,
        authentication: authentication.status === 'fulfilled' ? authentication.value : null,
        realtime: realtime.status === 'fulfilled' ? realtime.value : null,
        topContent: topContent.status === 'fulfilled' ? topContent.value : null,
        systemPerformance: systemPerformance.status === 'fulfilled' ? systemPerformance.value : null,
        userBehavior: userBehavior.status === 'fulfilled' ? userBehavior.value : null,
        searchTrends: searchTrends.status === 'fulfilled' ? searchTrends.value : null,
        postSeeAnalytics: postSeeAnalytics.status === 'fulfilled' ? postSeeAnalytics.value : null,
        contentSummary: contentSummary.status === 'fulfilled' ? contentSummary.value : null
      });

    } catch (error) {
      console.error('Failed to load analytics:', error);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, color = "blue", trend = null, description = null }) => (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold">{value || 'N/A'}</p>
          {trend && (
            <p className={`text-sm ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend > 0 ? '+' : ''}{trend}%
            </p>
          )}
          {description && (
            <p className="text-xs text-gray-500 mt-1">{description}</p>
          )}
        </div>
        <Icon className={`h-8 w-8 text-${color}-500 ml-4`} />
      </div>
    </Card>
  );

  const DataTable = ({ title, data, columns }) => (
    <Card>
      <CardHeader>
        <h3 className="text-lg font-semibold">{title}</h3>
      </CardHeader>
      <CardContent>
        {data && data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto">
              <thead>
                <tr className="border-b">
                  {columns.map((col, index) => (
                    <th key={index} className="text-left py-2 px-4 font-medium text-gray-600">
                      {col.header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.slice(0, 10).map((row, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    {columns.map((col, colIndex) => (
                      <td key={colIndex} className="py-2 px-4">
                        {col.accessor ? row[col.accessor] : col.render ? col.render(row) : '-'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No data available</p>
        )}
      </CardContent>
    </Card>
  );

  const OverviewDashboard = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Users"
          value={analytics.overview?.total_users || analytics.users?.total_users}
          icon={Users}
          color="blue"
          description="Registered users"
        />
        <StatCard
          title="Active Today"
          value={analytics.overview?.active_today || analytics.realtime?.active_users}
          icon={Activity}
          color="green"
          description="Currently active"
        />
        <StatCard
          title="Total Views"
          value={analytics.postSeeAnalytics?.summary?.total_views || analytics.content?.total_views}
          icon={Eye}
          color="purple"
          description="Post views tracked"
        />
        <StatCard
          title="System Load"
          value={analytics.systemPerformance?.cpu_usage ? `${analytics.systemPerformance.cpu_usage}%` : 'N/A'}
          icon={Server}
          color="orange"
          description="Current CPU usage"
        />
      </div>

      {/* PostSee Analytics Summary */}
      {analytics.postSeeAnalytics && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Eye className="h-5 w-5" />
              PostSee Analytics Summary
            </h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-2xl font-bold text-blue-600">
                  {analytics.postSeeAnalytics.summary?.total_views || 0}
                </p>
                <p className="text-sm text-gray-600">Total Views</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">
                  {analytics.postSeeAnalytics.summary?.engaged_views || 0}
                </p>
                <p className="text-sm text-gray-600">Engaged Views</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">
                  {analytics.postSeeAnalytics.summary?.avg_view_duration || 0}s
                </p>
                <p className="text-sm text-gray-600">Avg Duration</p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <p className="text-2xl font-bold text-orange-600">
                  {analytics.postSeeAnalytics.summary?.engagement_rate || 0}%
                </p>
                <p className="text-sm text-gray-600">Engagement Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top Content */}
      {analytics.topContent && (
        <DataTable
          title="Top Performing Content"
          data={analytics.topContent.posts || []}
          columns={[
            { header: 'Content', accessor: 'title', render: (row) => row.title || `Post #${row.id}` },
            { header: 'Views', accessor: 'views' },
            { header: 'Engagements', accessor: 'engagement' },
            { header: 'Score', accessor: 'score' }
          ]}
        />
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
          description="All registered users"
        />
        <StatCard
          title="Active This Week"
          value={analytics.users?.active_this_week}
          icon={Activity}
          color="green"
          description="Weekly active users"
        />
        <StatCard
          title="New This Month"
          value={analytics.users?.new_this_month}
          icon={TrendingUp}
          color="purple"
          description="New registrations"
        />
      </div>

      {/* User Activity Table */}
      {analytics.userBehavior?.daily_activity && (
        <DataTable
          title="Daily User Activity"
          data={analytics.userBehavior.daily_activity}
          columns={[
            { header: 'Date', accessor: 'date' },
            { header: 'Active Users', accessor: 'active_users' },
            { header: 'New Users', accessor: 'new_users' },
            { header: 'Sessions', accessor: 'sessions' }
          ]}
        />
      )}
    </div>
  );

  const SystemDashboard = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="CPU Usage"
          value={analytics.systemPerformance?.cpu_usage ? `${analytics.systemPerformance.cpu_usage}%` : 'N/A'}
          icon={Server}
          color="orange"
          description="Current CPU load"
        />
        <StatCard
          title="Memory Usage"
          value={analytics.systemPerformance?.memory_usage ? `${analytics.systemPerformance.memory_usage}%` : 'N/A'}
          icon={Activity}
          color="red"
          description="RAM utilization"
        />
        <StatCard
          title="Active Sessions"
          value={analytics.realtime?.active_sessions}
          icon={Globe}
          color="blue"
          description="Current user sessions"
        />
        <StatCard
          title="Response Time"
          value={analytics.systemPerformance?.avg_response_time ? `${analytics.systemPerformance.avg_response_time}ms` : 'N/A'}
          icon={Clock}
          color="green"
          description="Average API response"
        />
      </div>

      {/* Authentication Analytics */}
      {analytics.authentication && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Authentication Analytics
            </h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-xl font-bold">{analytics.authentication.total_attempts || 0}</p>
                <p className="text-sm text-gray-600">Total Attempts</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-xl font-bold text-green-600">{analytics.authentication.success_rate || 0}%</p>
                <p className="text-sm text-gray-600">Success Rate</p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <p className="text-xl font-bold">{analytics.authentication.avg_response_time || 0}ms</p>
                <p className="text-sm text-gray-600">Avg Response Time</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const ContentDashboard = () => (
    <div className="space-y-6">
      {/* Content Summary Cards */}
      {analytics.contentSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            title="Total Posts"
            value={analytics.contentSummary.summary?.total_posts || 0}
            icon={TrendingUp}
            color="blue"
            description="All posts created"
          />
          <StatCard
            title="Total Engagement"
            value={analytics.contentSummary.summary?.total_engagement || 0}
            icon={Activity}
            color="green"
            description="Likes, comments, shares"
          />
          <StatCard
            title="Avg Engagement"
            value={`${analytics.contentSummary.summary?.avg_engagement_rate || 0}%`}
            icon={Eye}
            color="purple"
            description="Average engagement rate"
          />
          <StatCard
            title="Top Posts"
            value={analytics.contentSummary.summary?.top_performing_posts || 0}
            icon={TrendingUp}
            color="orange"
            description="High-performing content"
          />
        </div>
      )}

      {/* Top Content Table */}
      {analytics.topContent && (
        <DataTable
          title="Top Performing Content Details"
          data={analytics.topContent.posts || []}
          columns={[
            { header: 'Title', render: (row) => row.title || `Post #${row.id}` },
            { header: 'Views', accessor: 'views' },
            { header: 'Likes', accessor: 'likes' },
            { header: 'Comments', accessor: 'comments' },
            { header: 'Shares', accessor: 'shares' },
            { header: 'Score', accessor: 'score' }
          ]}
        />
      )}
    </div>
  );

  const SearchDashboard = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Total Searches"
          value={analytics.search?.total_searches}
          icon={Search}
          color="blue"
          description="All search queries"
        />
        <StatCard
          title="Unique Queries"
          value={analytics.search?.unique_queries}
          icon={Zap}
          color="green"
          description="Distinct search terms"
        />
        <StatCard
          title="Avg Results"
          value={analytics.search?.avg_results}
          icon={TrendingUp}
          color="purple"
          description="Results per search"
        />
      </div>

      {/* Search Trends Table */}
      {analytics.searchTrends?.daily_searches && (
        <DataTable
          title="Daily Search Activity"
          data={analytics.searchTrends.daily_searches}
          columns={[
            { header: 'Date', accessor: 'date' },
            { header: 'Searches', accessor: 'searches' },
            { header: 'Unique Queries', accessor: 'unique_queries' },
            { header: 'Avg Results', accessor: 'avg_results' }
          ]}
        />
      )}

      {/* Popular Search Terms */}
      {analytics.search?.popular_terms && (
        <DataTable
          title="Popular Search Terms"
          data={analytics.search.popular_terms}
          columns={[
            { header: 'Search Term', accessor: 'term' },
            { header: 'Count', accessor: 'count' },
            { header: 'Results Found', accessor: 'results' }
          ]}
        />
      )}
    </div>
  );

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

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <p className="text-gray-600">Comprehensive analytics and insights (Fallback Mode - Tables & Cards Only)</p>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="search">Search</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
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
      </Tabs>
    </div>
  );
};

export default FallbackAnalyticsDashboard;
