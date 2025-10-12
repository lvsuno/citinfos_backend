#!/bin/bash

# Quick Test Script - Creates a test page for the analytics dashboard
# Run from project root: ./scripts/quick_test_analytics.sh

set -e

echo "🧪 Creating Analytics Test Page..."

# Create test page directory if it doesn't exist
mkdir -p src/pages

# Create the test page
cat > src/pages/AnalyticsTest.jsx << 'EOF'
import React from 'react';
import { VisitorAnalyticsDashboard } from '../components/analytics';
import './AnalyticsTest.css';

/**
 * Test page for Visitor Analytics Dashboard
 *
 * Access at: http://localhost:3000/analytics-test
 *
 * Requirements:
 * - User must be authenticated
 * - User must be admin or moderator
 * - Backend must be running at localhost:8000
 * - WebSocket endpoint must be accessible
 */
export default function AnalyticsTest() {
    return (
        <div className="analytics-test-page">
            <div className="test-header">
                <h1>📊 Visitor Analytics Dashboard - Test Page</h1>
                <p className="test-info">
                    This is a test page for the analytics dashboard components.
                    Check the browser console for any errors or warnings.
                </p>
            </div>

            <div className="test-status">
                <div className="status-item">
                    <span className="status-label">Backend:</span>
                    <span className="status-value">http://localhost:8000</span>
                </div>
                <div className="status-item">
                    <span className="status-label">WebSocket:</span>
                    <span className="status-value">ws://localhost:8000/ws/analytics/visitors/</span>
                </div>
                <div className="status-item">
                    <span className="status-label">Chart.js:</span>
                    <span className="status-value">4.5.0</span>
                </div>
            </div>

            <div className="test-dashboard">
                <VisitorAnalyticsDashboard />
            </div>
        </div>
    );
}
EOF

# Create CSS for the test page
cat > src/pages/AnalyticsTest.css << 'EOF'
.analytics-test-page {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
    background-color: #f5f7fa;
    min-height: 100vh;
}

.test-header {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.test-header h1 {
    margin: 0 0 0.5rem 0;
    color: #2c3e50;
    font-size: 1.8rem;
}

.test-info {
    color: #7f8c8d;
    margin: 0;
    font-size: 0.95rem;
}

.test-status {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
}

.status-item {
    display: flex;
    gap: 0.5rem;
}

.status-label {
    font-weight: 600;
    color: #34495e;
}

.status-value {
    color: #7f8c8d;
    font-family: monospace;
    font-size: 0.9rem;
}

.test-dashboard {
    /* Dashboard component has its own styling */
}

@media (max-width: 768px) {
    .analytics-test-page {
        padding: 1rem;
    }

    .test-status {
        flex-direction: column;
        gap: 0.75rem;
    }

    .status-item {
        flex-direction: column;
        gap: 0.25rem;
    }
}
EOF

echo "✅ Test page created: src/pages/AnalyticsTest.jsx"
echo "✅ Test CSS created: src/pages/AnalyticsTest.css"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Add the route to your App.js or router:"
echo "   import AnalyticsTest from './pages/AnalyticsTest';"
echo "   <Route path=\"/analytics-test\" element={<AnalyticsTest />} />"
echo ""
echo "2. Visit the test page:"
echo "   http://localhost:3000/analytics-test"
echo ""
echo "3. Check browser console for:"
echo "   - Chart.js loading status"
echo "   - API call responses"
echo "   - WebSocket connection status"
echo "   - Any errors or warnings"
echo ""
echo "🎯 To add the route automatically, you can manually edit your router file"
echo "   or integrate the dashboard into your admin/moderator pages."
