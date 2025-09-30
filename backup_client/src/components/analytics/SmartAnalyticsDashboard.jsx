import React, { useState, useEffect } from 'react';
import { AlertTriangle, BarChart3, RefreshCw } from 'lucide-react';

// Smart error boundary wrapper for analytics
class AnalyticsErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Analytics Dashboard Error:', error, errorInfo);
    console.error('Error message:', error.message);
    console.error('Error stack:', error.stack);
    console.error('Component stack:', errorInfo.componentStack);

    // Log specific recharts errors
    if (error.message?.includes('recharts') || error.stack?.includes('recharts')) {
      console.warn('Recharts library error detected, falling back to simple dashboard');
    }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}

const SmartAnalyticsDashboard = () => {
  const [dashboardMode, setDashboardMode] = useState('loading');
  const [error, setError] = useState(null);

  // Lazy load the components
  const [ComprehensiveAnalyticsDashboard, setComprehensiveAnalyticsDashboard] = useState(null);
  const [FallbackAnalyticsDashboard, setFallbackAnalyticsDashboard] = useState(null);

  useEffect(() => {
    loadDashboardComponents();
  }, []);

  const loadDashboardComponents = async () => {
    try {
      setDashboardMode('loading');
      setError(null);

      // First, always load the fallback
      const fallbackModule = await import('./FallbackAnalyticsDashboard');
      setFallbackAnalyticsDashboard(() => fallbackModule.default);

      // Then try to load the comprehensive dashboard with recharts
      try {
        console.log('🔄 Testing recharts availability...');
        // Test if recharts is available
        const rechartsModule = await import('recharts');
        console.log('✅ Recharts imported successfully', Object.keys(rechartsModule));

        console.log('🔄 Loading ComprehensiveAnalyticsDashboard...');
        const comprehensiveModule = await import('./ComprehensiveAnalyticsDashboard');
        console.log('✅ ComprehensiveAnalyticsDashboard module loaded', typeof comprehensiveModule.default);

        // Test if the component is actually a valid React component
        if (typeof comprehensiveModule.default !== 'function') {
          throw new Error('ComprehensiveAnalyticsDashboard is not a valid React component');
        }

        // Test if the component can be instantiated without immediate errors
        try {
          const TestComponent = comprehensiveModule.default;
          console.log('🔄 Testing component instantiation...');
          // Just test if it's callable - don't actually render yet
          const testInstance = React.createElement(TestComponent);
          console.log('✅ Component instantiation successful');
        } catch (instantiationError) {
          console.error('❌ Component instantiation failed:', instantiationError);
          throw instantiationError;
        }

        setComprehensiveAnalyticsDashboard(() => comprehensiveModule.default);
        setDashboardMode('comprehensive');

        console.log('✅ Comprehensive analytics dashboard loaded successfully');
      } catch (rechartsError) {
        console.error('❌ Failed to load comprehensive dashboard:', rechartsError);
        console.error('Error details:', rechartsError.message);
        console.error('Error stack:', rechartsError.stack);

        setError(`Charts failed to load, switched to Standard Mode`);
        setDashboardMode('fallback');
      }
    } catch (error) {
      console.error('❌ Failed to load analytics dashboards:', error);
      setError('Failed to load analytics components');
      setDashboardMode('error');
    }
  };

  const forceFallbackMode = () => {
    setDashboardMode('fallback');
    console.log('🔄 Manually switched to fallback mode');
  };

  const retryComprehensive = () => {
    loadDashboardComponents();
  };

  // Loading state
  if (dashboardMode === 'loading') {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics dashboard...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (dashboardMode === 'error') {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Analytics Unavailable</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={retryComprehensive}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 inline-flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Dashboard mode indicator
  const DashboardModeIndicator = () => (
    <div className="mb-4 p-3 bg-gray-50 border-l-4 border-blue-500 rounded">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-blue-500" />
          <span className="font-medium">
            {dashboardMode === 'comprehensive' ? 'Enhanced Mode' : 'Standard Mode'}
          </span>
          <span className="text-sm text-gray-600">
            {dashboardMode === 'comprehensive'
              ? '(Charts & Visualizations Active)'
              : '(Tables & Cards Only)'}
          </span>
        </div>
        <div className="flex gap-2">
          {dashboardMode === 'comprehensive' && (
            <button
              onClick={forceFallbackMode}
              className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Use Standard Mode
            </button>
          )}
          {dashboardMode === 'fallback' && (
            <button
              onClick={retryComprehensive}
              className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
            >
              Try Enhanced Mode
            </button>
          )}
        </div>
      </div>
    </div>
  );

  // Render comprehensive dashboard with error boundary
  if (dashboardMode === 'comprehensive' && ComprehensiveAnalyticsDashboard && FallbackAnalyticsDashboard) {
    return (
      <div>
        <DashboardModeIndicator />
        <AnalyticsErrorBoundary fallback={
          <div>
            <div className="mb-4 p-3 bg-yellow-50 border-l-4 border-yellow-400 rounded">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                <span className="font-medium text-yellow-800">
                  Charts failed to load, switched to Standard Mode
                </span>
                <button
                  onClick={retryComprehensive}
                  className="ml-auto text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200"
                >
                  Retry Enhanced Mode
                </button>
              </div>
            </div>
            <FallbackAnalyticsDashboard />
          </div>
        }>
          <ComprehensiveAnalyticsDashboard />
        </AnalyticsErrorBoundary>
      </div>
    );
  }

  // Render fallback dashboard
  if (dashboardMode === 'fallback' && FallbackAnalyticsDashboard) {
    return (
      <div>
        <DashboardModeIndicator />
        <FallbackAnalyticsDashboard />
      </div>
    );
  }

  // Fallback to simple message if components failed to load
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <AlertTriangle className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Dashboard Loading Issue</h3>
        <p className="text-gray-600 mb-4">Unable to load dashboard components</p>
        <button
          onClick={loadDashboardComponents}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Reload Dashboard
        </button>
      </div>
    </div>
  );
};

export default SmartAnalyticsDashboard;
