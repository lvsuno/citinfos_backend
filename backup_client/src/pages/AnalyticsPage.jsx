/**
 * AnalyticsPage Component
 * Smart Analytics Dashboard with automatic fallback handling
 */

import React from 'react';
import SmartAnalyticsDashboard from '../components/analytics/SmartAnalyticsDashboard';

const AnalyticsPage = () => {
  return (
    <div className="analytics-page min-h-screen bg-gray-50">
      <SmartAnalyticsDashboard />
    </div>
  );
};

export default AnalyticsPage;
