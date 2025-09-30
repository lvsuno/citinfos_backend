import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useJWTAuth } from '../hooks/useJWTAuth';
import { useRedirectAfterLogin } from '../hooks/useRedirectAfterLogin';
import socialAuthService from '../services/socialAuth';

const OAuthCallback = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { refreshUser } = useJWTAuth();
  const { navigateToStoredLocation } = useRedirectAfterLogin();
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        const urlParams = new URLSearchParams(location.search);

        // Check for OAuth errors first
        const error = urlParams.get('error');
        if (error) {
          throw new Error(`OAuth error: ${error}`);
        }

        // Use the improved callback handler from socialAuthService
        const provider = urlParams.get('state') || 'github'; // Provider from state parameter
        const result = await socialAuthService.handleOAuthCallback(provider, urlParams);

        if (result.success) {
          // Set tokens
          if (result.access_token) {
            localStorage.setItem('access_token', result.access_token);
          }
          if (result.refresh_token) {
            localStorage.setItem('refresh_token', result.refresh_token);
          }

          // Refresh user data
          await refreshUser();

          setStatus('success');

          // Redirect after short delay
          setTimeout(() => {
            navigateToStoredLocation('/dashboard');
          }, 1000);
        } else {
          throw new Error(result.error || 'Authentication failed');
        }
      } catch (error) {
        console.error('OAuth callback error:', error);
        setError(error.message);
        setStatus('error');

        // Redirect to login after error
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      }
    };

    handleOAuthCallback();
  }, [location, navigate, refreshUser, navigateToStoredLocation]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
        {status === 'processing' && (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Completing Authentication
            </h2>
            <p className="text-gray-600">
              Please wait while we sign you in...
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="text-green-500 mb-4">
              <svg className="h-12 w-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Authentication Successful!
            </h2>
            <p className="text-gray-600">
              Redirecting you to the application...
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="text-red-500 mb-4">
              <svg className="h-12 w-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Authentication Failed
            </h2>
            <p className="text-gray-600 mb-4">
              {error || 'An error occurred during authentication.'}
            </p>
            <button
              onClick={() => navigate('/login')}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Return to Login
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default OAuthCallback;