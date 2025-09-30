import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Chip,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  TrendingUp,
  People,
  Build,
  Search,
  Article,
  Assessment,
  Refresh,
  Download,
  Visibility,
  ThumbUp,
  Share,
  Comment
} from '@mui/icons-material';
import { analyticsAPI } from '../services/analyticsAPI';

const AdminAnalytics = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analyticsData, setAnalyticsData] = useState({
    overview: null,
    content: null,
    equipment: null,
    users: null,
    search: null,
    authentication: null
  });

  // Load analytics data
  const loadAnalyticsData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [
        overviewData,
        contentData,
        equipmentData,
        userData,
        searchData,
        authData
      ] = await Promise.all([
        analyticsAPI.getOverviewAnalytics(),
        analyticsAPI.getContentAnalytics(),
        analyticsAPI.getEquipmentAnalytics(),
        analyticsAPI.getUserAnalytics(),
        analyticsAPI.getSearchAnalytics(),
        analyticsAPI.getAuthenticationAnalytics()
      ]);

      setAnalyticsData({
        overview: overviewData,
        content: contentData,
        equipment: equipmentData,
        users: userData,
        search: searchData,
        authentication: authData
      });
    } catch (err) {
      setError('Failed to load analytics data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  // Export analytics data
  const handleExport = async (type) => {
    try {
      const blob = await analyticsAPI.exportAnalytics(type);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `analytics_${type}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to export data: ' + err.message);
    }
  };

  // Metric Card Component
  const MetricCard = ({ title, value, icon, color = 'primary', subtitle, trend }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="h6">
              {title}
            </Typography>
            <Typography variant="h4" component="div" color={`${color}.main`}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="textSecondary">
                {subtitle}
              </Typography>
            )}
            {trend && (
              <Box display="flex" alignItems="center" mt={1}>
                <TrendingUp
                  fontSize="small"
                  color={trend > 0 ? 'success' : 'error'}
                />
                <Typography
                  variant="body2"
                  color={trend > 0 ? 'success.main' : 'error.main'}
                  sx={{ ml: 0.5 }}
                >
                  {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
                </Typography>
              </Box>
            )}
          </Box>
          <Box color={`${color}.main`}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  // Overview Tab
  const OverviewTab = () => (
    <Grid container spacing={3}>
      {/* Key Metrics */}
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Total Users"
          value={analyticsData.overview?.total_users || 0}
          icon={<People fontSize="large" />}
          color="primary"
          trend={analyticsData.overview?.user_growth_rate}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Total Posts"
          value={analyticsData.overview?.total_posts || 0}
          icon={<Article fontSize="large" />}
          color="secondary"
          trend={analyticsData.overview?.post_growth_rate}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Total Equipment"
          value={analyticsData.overview?.total_equipment || 0}
          icon={<Build fontSize="large" />}
          color="success"
          trend={analyticsData.overview?.equipment_growth_rate}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Daily Active Users"
          value={analyticsData.overview?.daily_active_users || 0}
          icon={<TrendingUp fontSize="large" />}
          color="warning"
          trend={analyticsData.overview?.dau_growth_rate}
        />
      </Grid>

      {/* System Performance */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            System Performance
          </Typography>
          <Box mb={2}>
            <Typography variant="body2" color="textSecondary">
              Average Response Time
            </Typography>
            <Box display="flex" alignItems="center" mt={1}>
              <LinearProgress
                variant="determinate"
                value={Math.min((analyticsData.overview?.avg_response_time || 0) / 10, 100)}
                sx={{ flexGrow: 1, mr: 2 }}
              />
              <Typography variant="body2">
                {analyticsData.overview?.avg_response_time || 0}ms
              </Typography>
            </Box>
          </Box>
          <Box mb={2}>
            <Typography variant="body2" color="textSecondary">
              Database Performance
            </Typography>
            <Box display="flex" alignItems="center" mt={1}>
              <LinearProgress
                variant="determinate"
                value={Math.min((analyticsData.overview?.db_query_time || 0) / 5, 100)}
                sx={{ flexGrow: 1, mr: 2 }}
                color="secondary"
              />
              <Typography variant="body2">
                {analyticsData.overview?.db_query_time || 0}ms
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Grid>

      {/* Recent Activity */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Recent Activity
          </Typography>
          <Box>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Last 24 Hours
            </Typography>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography variant="body2">New Users:</Typography>
              <Chip
                label={analyticsData.overview?.new_users_24h || 0}
                size="small"
                color="primary"
              />
            </Box>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography variant="body2">New Posts:</Typography>
              <Chip
                label={analyticsData.overview?.new_posts_24h || 0}
                size="small"
                color="secondary"
              />
            </Box>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography variant="body2">Equipment Listed:</Typography>
              <Chip
                label={analyticsData.overview?.equipment_listed_24h || 0}
                size="small"
                color="success"
              />
            </Box>
          </Box>
        </Paper>
      </Grid>
    </Grid>
  );

  // Content Analytics Tab
  const ContentTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Total Views"
          value={analyticsData.content?.total_views || 0}
          icon={<Visibility fontSize="large" />}
          color="primary"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Total Likes"
          value={analyticsData.content?.total_likes || 0}
          icon={<ThumbUp fontSize="large" />}
          color="success"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Total Shares"
          value={analyticsData.content?.total_shares || 0}
          icon={<Share fontSize="large" />}
          color="warning"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Total Comments"
          value={analyticsData.content?.total_comments || 0}
          icon={<Comment fontSize="large" />}
          color="secondary"
        />
      </Grid>

      {/* Top Performing Content */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Top Performing Content</Typography>
            <Button
              size="small"
              onClick={() => handleExport('content')}
              startIcon={<Download />}
            >
              Export
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Content</TableCell>
                  <TableCell align="right">Views</TableCell>
                  <TableCell align="right">Likes</TableCell>
                  <TableCell align="right">Comments</TableCell>
                  <TableCell align="right">Engagement Rate</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(analyticsData.content?.top_content || []).map((item, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                        {item.title || `Content ${item.id}`}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {item.content_type}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{item.view_count}</TableCell>
                    <TableCell align="right">{item.like_count}</TableCell>
                    <TableCell align="right">{item.comment_count}</TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${item.engagement_rate.toFixed(1)}%`}
                        color={item.engagement_rate > 5 ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Grid>
    </Grid>
  );

  // Equipment Analytics Tab
  const EquipmentTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Total Revenue"
          value={`$${(analyticsData.equipment?.total_revenue || 0).toLocaleString()}`}
          icon={<TrendingUp fontSize="large" />}
          color="success"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Active Rentals"
          value={analyticsData.equipment?.active_rentals || 0}
          icon={<Build fontSize="large" />}
          color="primary"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Conversion Rate"
          value={`${(analyticsData.equipment?.conversion_rate || 0).toFixed(1)}%`}
          icon={<Assessment fontSize="large" />}
          color="warning"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Avg Rating"
          value={(analyticsData.equipment?.avg_rating || 0).toFixed(1)}
          icon={<TrendingUp fontSize="large" />}
          color="secondary"
        />
      </Grid>

      {/* Equipment Performance Table */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Equipment Performance</Typography>
            <Button
              size="small"
              onClick={() => handleExport('equipment')}
              startIcon={<Download />}
            >
              Export
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Equipment</TableCell>
                  <TableCell align="right">Views</TableCell>
                  <TableCell align="right">Rentals</TableCell>
                  <TableCell align="right">Revenue</TableCell>
                  <TableCell align="right">Rating</TableCell>
                  <TableCell align="right">Popularity</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(analyticsData.equipment?.top_equipment || []).map((item, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 250 }}>
                        {item.name || `Equipment ${item.id}`}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{item.total_views}</TableCell>
                    <TableCell align="right">{item.successful_rentals}</TableCell>
                    <TableCell align="right">${item.total_revenue}</TableCell>
                    <TableCell align="right">{item.average_rating.toFixed(1)}</TableCell>
                    <TableCell align="right">
                      <LinearProgress
                        variant="determinate"
                        value={item.popularity_score}
                        sx={{ width: 60 }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Grid>
    </Grid>
  );

  // Search Analytics Tab
  const SearchTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Total Searches"
          value={analyticsData.search?.total_searches || 0}
          icon={<Search fontSize="large" />}
          color="primary"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Avg CTR"
          value={`${(analyticsData.search?.avg_ctr || 0).toFixed(1)}%`}
          icon={<TrendingUp fontSize="large" />}
          color="success"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Zero Results"
          value={`${(analyticsData.search?.zero_result_rate || 0).toFixed(1)}%`}
          icon={<Assessment fontSize="large" />}
          color="error"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Avg Response Time"
          value={`${analyticsData.search?.avg_response_time || 0}ms`}
          icon={<Assessment fontSize="large" />}
          color="warning"
        />
      </Grid>

      {/* Popular Search Terms */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Popular Search Terms
          </Typography>
          <Box>
            {(analyticsData.search?.popular_terms || []).map((term, index) => (
              <Box
                key={index}
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                mb={1}
              >
                <Typography variant="body2">{term.query}</Typography>
                <Chip
                  label={term.count}
                  size="small"
                  color="primary"
                />
              </Box>
            ))}
          </Box>
        </Paper>
      </Grid>

      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Search Performance Trends
          </Typography>
          <Box>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Last 7 Days
            </Typography>
            <Box mb={2}>
              <Typography variant="body2">Success Rate</Typography>
              <LinearProgress
                variant="determinate"
                value={analyticsData.search?.success_rate || 0}
                sx={{ mt: 1 }}
                color="success"
              />
              <Typography variant="caption" color="textSecondary">
                {(analyticsData.search?.success_rate || 0).toFixed(1)}%
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2">User Satisfaction</Typography>
              <LinearProgress
                variant="determinate"
                value={analyticsData.search?.satisfaction_score || 0}
                sx={{ mt: 1 }}
                color="primary"
              />
              <Typography variant="caption" color="textSecondary">
                {(analyticsData.search?.satisfaction_score || 0).toFixed(1)}%
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Grid>
    </Grid>
  );

  // User Analytics Tab
  const UserTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Active Users"
          value={analyticsData.users?.active_users || 0}
          icon={<People fontSize="large" />}
          color="primary"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Avg Session Time"
          value={`${Math.round((analyticsData.users?.avg_session_time || 0) / 60)}m`}
          icon={<Assessment fontSize="large" />}
          color="secondary"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Retention Rate"
          value={`${(analyticsData.users?.retention_rate || 0).toFixed(1)}%`}
          icon={<TrendingUp fontSize="large" />}
          color="success"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Bounce Rate"
          value={`${(analyticsData.users?.bounce_rate || 0).toFixed(1)}%`}
          icon={<Assessment fontSize="large" />}
          color="warning"
        />
      </Grid>

      {/* User Activity Levels */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            User Activity Distribution
          </Typography>
          <Grid container spacing={2}>
            {Object.entries(analyticsData.users?.activity_distribution || {}).map(([level, count]) => (
              <Grid item xs={12} sm={6} md={2.4} key={level}>
                <Box textAlign="center" p={2}>
                  <Typography variant="h4" color="primary.main">
                    {count}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" textTransform="capitalize">
                    {level.replace('_', ' ')}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );

  // Authentication Analytics Tab
  const AuthTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Login Success Rate"
          value={`${(analyticsData.authentication?.success_rate || 0).toFixed(1)}%`}
          icon={<Assessment fontSize="large" />}
          color="success"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Avg Auth Time"
          value={`${analyticsData.authentication?.avg_auth_time || 0}ms`}
          icon={<TrendingUp fontSize="large" />}
          color="primary"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Failed Attempts"
          value={analyticsData.authentication?.failed_attempts || 0}
          icon={<Assessment fontSize="large" />}
          color="error"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <MetricCard
          title="Token Renewals"
          value={analyticsData.authentication?.token_renewals || 0}
          icon={<Refresh fontSize="large" />}
          color="warning"
        />
      </Grid>

      {/* Authentication Methods */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Authentication Methods Usage
          </Typography>
          <Grid container spacing={2}>
            {Object.entries(analyticsData.authentication?.auth_methods || {}).map(([method, data]) => (
              <Grid item xs={12} sm={6} md={3} key={method}>
                <Box textAlign="center" p={2}>
                  <Typography variant="h5" color="primary.main">
                    {data.count}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" textTransform="capitalize">
                    {method}
                  </Typography>
                  <Typography variant="caption" color="success.main">
                    {data.success_rate.toFixed(1)}% success
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Analytics Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={loadAnalyticsData}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Navigation Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          aria-label="analytics tabs"
        >
          <Tab label="Overview" icon={<Assessment />} />
          <Tab label="Content" icon={<Article />} />
          <Tab label="Equipment" icon={<Build />} />
          <Tab label="Users" icon={<People />} />
          <Tab label="Search" icon={<Search />} />
          <Tab label="Authentication" icon={<TrendingUp />} />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <Box>
        {activeTab === 0 && <OverviewTab />}
        {activeTab === 1 && <ContentTab />}
        {activeTab === 2 && <EquipmentTab />}
        {activeTab === 3 && <UserTab />}
        {activeTab === 4 && <SearchTab />}
        {activeTab === 5 && <AuthTab />}
      </Box>
    </Container>
  );
};

export default AdminAnalytics;
