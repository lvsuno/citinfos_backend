import React, { useEffect, useState } from 'react';
import profileAPI from '../services/profileAPI';

const BadgeAPITest = () => {
  const [testResults, setTestResults] = useState({});
  const [loading, setLoading] = useState(false);

  const testAPI = async () => {
    setLoading(true);
    const results = {};

    try {
      // Test with a known user profile ID that has badges
      const testUserId = '3428b922-71e2-4d29-bcd5-bb7be0a8e306'; // lvs profile ID

      results.userId = testUserId;

      const badges = await profileAPI.getUserBadges(testUserId);

      results.success = true;
      results.badges = badges;
      results.badgeCount = badges?.length || 0;

    } catch (error) {
      console.error('API Test Error:', error);
      results.success = false;
      results.error = error.message;
      results.fullError = error;
    }

    setTestResults(results);
    setLoading(false);
  };

  useEffect(() => {
    testAPI();
  }, []);

  return (
    <div style={{
      padding: '20px',
      margin: '20px',
      border: '2px solid #e74c3c',
      borderRadius: '8px',
      backgroundColor: '#fff'
    }}>
      <h3>🔬 Badge API Debug Test</h3>

      {loading && <p>⏳ Testing API...</p>}

      {!loading && (
        <div>
          <p><strong>User ID:</strong> {testResults.userId}</p>
          <p><strong>Success:</strong> {testResults.success ? '✅ Yes' : '❌ No'}</p>

          {testResults.success ? (
            <div>
              <p><strong>Badge Count:</strong> {testResults.badgeCount}</p>
              <p><strong>Badges:</strong></p>
              <pre style={{
                backgroundColor: '#f8f9fa',
                padding: '10px',
                borderRadius: '4px',
                fontSize: '12px',
                overflow: 'auto',
                maxHeight: '200px'
              }}>
                {JSON.stringify(testResults.badges, null, 2)}
              </pre>
            </div>
          ) : (
            <div>
              <p><strong>Error:</strong> {testResults.error}</p>
              <details>
                <summary>Full Error Details</summary>
                <pre style={{
                  backgroundColor: '#f8f9fa',
                  padding: '10px',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}>
                  {JSON.stringify(testResults.fullError, null, 2)}
                </pre>
              </details>
            </div>
          )}

          <button
            onClick={testAPI}
            style={{
              marginTop: '10px',
              padding: '8px 16px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            🔄 Retest API
          </button>
        </div>
      )}
    </div>
  );
};

export default BadgeAPITest;
