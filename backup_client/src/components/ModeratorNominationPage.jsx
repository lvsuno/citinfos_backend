import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useJWTAuth } from '../hooks/useJWTAuth';
import { communitiesAPI } from '../services/communitiesAPI';
import notificationsAPI from '../services/notificationsAPI';
import {
  UserGroupIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowLeftIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const ModeratorNominationPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useJWTAuth();

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [membershipData, setMembershipData] = useState(null);

  // Get URL parameters
  const membershipId = searchParams.get('membership_id');
  const notificationId = searchParams.get('notification_id');
  const suggestedAction = searchParams.get('action');
  const communitySlug = searchParams.get('community');

  useEffect(() => {
    // Validate required parameters
    if (!membershipId && !notificationId) {
      setError('Invalid nomination link. Missing membership or notification ID.');
      return;
    }

    // If not authenticated, redirect to login with return URL
    if (!isAuthenticated) {
      const returnUrl = encodeURIComponent(window.location.href);
      navigate(`/login?next=${returnUrl}`);
      return;
    }

    // Load membership data for display
    loadMembershipData();
  }, [membershipId, notificationId, isAuthenticated, navigate]);

  const loadMembershipData = async () => {
    try {
      if (membershipId) {
        // Try to get membership details directly
        const membership = await communitiesAPI.getMembershipById(membershipId);
        setMembershipData(membership);
      } else if (notificationId) {
        // Get notification details and find the user's membership in that community
        const notification = await notificationsAPI.getNotificationDetail(notificationId);

        if (notification.content_object && notification.content_object.slug) {
          // Get the user's membership in this community
          const memberships = await communitiesAPI.getUserMemberships();
          const membership = memberships.find(m =>
            m.community.slug === notification.content_object.slug
          );

          if (membership) {
            setMembershipData(membership);
          } else {
            throw new Error('Membership not found for this community');
          }
        } else {
          throw new Error('Invalid notification data');
        }
      }
    } catch (err) {
      console.error('Failed to load membership data:', err);
      // Don't fail the whole process if we can't load the details
      setMembershipData({
        community: {
          name: 'Community',
          description: 'Join this amazing community!'
        },
        assigned_by: {
          display_name: 'Community Admin'
        }
      });
    }
  };

  const processNomination = async (action) => {
    const effectiveMembershipId = membershipId || membershipData?.id;

    if (!effectiveMembershipId) {
      setError('Invalid nomination link. Please contact support.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await communitiesAPI.processModeratorNomination({
        membership_id: effectiveMembershipId,
        action: action
      });

      const message = action === 'accept'
        ? '🎉 Congratulations! You are now a moderator for this community.'
        : '✅ You have declined the moderator role.';

      setResult({
        type: 'success',
        message: message,
        details: response.message || `Moderator nomination ${action}ed successfully.`,
        community: response.community,
        role: response.role
      });

      // Redirect after success
      setTimeout(() => {
        if (communitySlug) {
          navigate(`/communities/${communitySlug}`);
        } else if (response.community_slug) {
          navigate(`/communities/${response.community_slug}`);
        } else {
          navigate('/communities');
        }
      }, 3000);

    } catch (err) {
      console.error('Error processing nomination:', err);
      setError(err.message || 'An error occurred while processing your response.');
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (!membershipId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <div className="text-center">
            <ExclamationTriangleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h1 className="text-xl font-bold text-gray-900 mb-2">Invalid Link</h1>
            <p className="text-gray-600 mb-4">
              This nomination link is invalid or has expired. Please contact support.
            </p>
            <button
              onClick={() => navigate('/communities')}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <ArrowLeftIcon className="w-4 h-4 mr-2" />
              Back to Communities
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-8 text-white text-center">
          <UserGroupIcon className="w-16 h-16 mx-auto mb-4" />
          <h1 className="text-2xl font-bold mb-2">Moderator Nomination</h1>
          <p className="text-blue-100">You've been invited to become a moderator</p>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Community Information */}
          {membershipData && (
            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <SparklesIcon className="w-8 h-8 text-yellow-500" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {membershipData.community?.name || 'Community'}
                  </h3>
                  <p className="text-gray-600 mb-3">
                    {membershipData.community?.description || 'Join this amazing community!'}
                  </p>
                  <div className="flex items-center text-sm text-gray-500">
                    <span className="font-medium">Assigned by:</span>
                    <span className="ml-2">
                      {membershipData.assigned_by?.display_name ||
                       membershipData.assigned_by?.username ||
                       'Community Admin'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Result Display */}
          {result && (
            <div className={`rounded-lg p-4 mb-6 ${
              result.type === 'success'
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-start space-x-3">
                {result.type === 'success' ? (
                  <CheckCircleIcon className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircleIcon className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <h4 className={`font-medium ${
                    result.type === 'success' ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {result.message}
                  </h4>
                  {result.details && (
                    <p className={`text-sm mt-1 ${
                      result.type === 'success' ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {result.details}
                    </p>
                  )}
                  {result.type === 'success' && (
                    <p className="text-sm text-green-600 mt-2">
                      Redirecting to community page...
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-start space-x-3">
                <ExclamationTriangleIcon className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-red-800">Error</h4>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {!result && !error && (
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => processNomination('accept')}
                disabled={loading}
                className={`flex items-center justify-center px-6 py-3 rounded-lg font-medium transition-all ${
                  suggestedAction === 'accept'
                    ? 'bg-green-600 hover:bg-green-700 text-white transform scale-105 shadow-lg'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <CheckCircleIcon className="w-5 h-5 mr-2" />
                Accept Role
              </button>

              <button
                onClick={() => processNomination('decline')}
                disabled={loading}
                className={`flex items-center justify-center px-6 py-3 rounded-lg font-medium transition-all ${
                  suggestedAction === 'decline'
                    ? 'bg-red-600 hover:bg-red-700 text-white transform scale-105 shadow-lg'
                    : 'bg-red-600 hover:bg-red-700 text-white'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <XCircleIcon className="w-5 h-5 mr-2" />
                Decline Role
              </button>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-6">
              <div className="inline-flex items-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
                <span className="text-gray-600">Processing your response...</span>
              </div>
            </div>
          )}

          {/* Navigation */}
          {!loading && (
            <div className="flex justify-center mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={() => navigate('/communities')}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
              >
                <ArrowLeftIcon className="w-4 h-4 mr-2" />
                Back to Communities
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ModeratorNominationPage;
