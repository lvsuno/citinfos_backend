import React, { useState, useEffect } from 'react';
import { useJWTAuth } from '../hooks/useJWTAuth';
import { communitiesAPI } from '../services/communitiesAPI';
import notificationsAPI from '../services/notificationsAPI';
import {
  UserGroupIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const ModeratorNominationContent = ({
  membershipId = null,
  notificationId = null,
  suggestedAction = null,
  onComplete = () => {},
  showBackButton = false,
  onBack = () => {}
}) => {
  const { user, isAuthenticated } = useJWTAuth();

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [membershipData, setMembershipData] = useState(null);

  useEffect(() => {
    // Validate required parameters
    if (!membershipId && !notificationId) {
      setError('Invalid nomination link. Missing membership or notification ID.');
      return;
    }

    // If not authenticated, we can't proceed
    if (!isAuthenticated) {
      setError('You must be logged in to view this nomination.');
      return;
    }

    // Load membership data for display
    loadMembershipData();
  }, [membershipId, notificationId, isAuthenticated]);

  const loadMembershipData = async () => {
    try {
      if (membershipId) {
        // Try to get membership details directly
        const membership = await communitiesAPI.getMembershipById(membershipId);
        setMembershipData(membership);
      } else if (notificationId) {
        // Get notification details and find the user's membership in that community
        const notification = await notificationsAPI.getNotificationDetail(notificationId);
        console.log('Notification data:', notification);

        if (notification.content_object) {
          console.log('Community object:', notification.content_object);

          // Try to get all memberships for this community
          const communityMemberships = await communitiesAPI.getCommunityMemberships(notification.content_object.id);
          console.log('Community memberships:', communityMemberships);
          console.log('Memberships count:', communityMemberships.results?.length);
          console.log('Current user ID:', user.id);

          // Find the current user's membership
          const membership = communityMemberships.results?.find(m => {
            console.log('Checking membership:', m, 'User ID:', m.user?.id || m.user);
            return m.user?.id === user.id || m.user === user.id;
          });

          if (membership) {
            console.log('Found membership:', membership);

                        // Get community stats if member count is not available
            if (!membership.community?.member_count && membership.community?.slug) {
              try {
                // Get the community details which should include membership_count
                const communityDetails = await communitiesAPI.getCommunityBySlug(membership.community.slug);
                console.log('Community details from API:', communityDetails);
                membership.community.member_count = communityDetails.membership_count || communityDetails.member_count;
              } catch (statsError) {
                console.warn('Failed to get community details:', statsError);
                // Fallback: count from memberships we already fetched
                membership.community.member_count = communityMemberships.results?.length || 0;
              }
            }

            setMembershipData(membership);
          } else {
            // For community_role_change notifications, create informational display
            console.log('Creating informational display for role change');

            const fallbackData = {
              id: null, // No membership ID needed for display
              community: notification.content_object,
              user: user,
              role: 'moderator', // Extract from notification message if possible
              assigned_by: notification.sender || { display_name: 'Community Admin' },
              created_at: notification.created_at,
              isRoleChange: true, // Flag to indicate this is just informational
              status: 'accepted' // If it's a role change notification, the role was already assigned
            };

            // Try to get community details for member count
            if (notification.content_object?.slug) {
              try {
                const communityDetails = await communitiesAPI.getCommunityBySlug(notification.content_object.slug);
                console.log('Community details for role change:', communityDetails);
                fallbackData.community = {
                  ...notification.content_object,
                  member_count: communityDetails.membership_count || communityDetails.member_count
                };
              } catch (statsError) {
                console.warn('Failed to get community details for fallback:', statsError);
                // Fallback: use the length of memberships we already fetched
                fallbackData.community.member_count = communityMemberships.results?.length || 0;
              }
            } else {
              // Fallback: use the length of memberships we already fetched
              fallbackData.community.member_count = communityMemberships.results?.length || 0;
            }

            setMembershipData(fallbackData);
          }
        } else {
          throw new Error('Invalid notification data - no community object');
        }
      }
    } catch (err) {
      console.error('Failed to load membership data:', err);
      // Don't fail the whole process if we can't load the details
      setMembershipData({
        id: notificationId || 'unknown',
        community: {
          name: 'Community',
          description: 'Join this amazing community!'
        },
        user: user,
        role: 'moderator',
        assigned_by: {
          display_name: 'Community Admin'
        }
      });
    }
  };

  const processNomination = async (action) => {
    // Only use membership ID if we have a real membership ID, not a notification ID
    const effectiveMembershipId = membershipId || (membershipData?.id && membershipData.id !== notificationId ? membershipData.id : null);

    if (!effectiveMembershipId) {
      setError('Unable to process nomination. Membership information not available.');
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

      console.log('Nomination response:', response); // Debug log

      setResult({
        success: true,
        action: action,
        message: response.message || `Moderator nomination ${action}ed successfully.`,
        details: response.message || `Moderator nomination ${action}ed successfully.`,
        timestamp: new Date().toISOString()
      });

      // Update the membership data locally to reflect the status change
      if (membershipData) {
        const updatedMembershipData = {
          ...membershipData,
          status: action === 'accept' ? 'accepted' : 'declined',
          role: action === 'accept' ? 'moderator' : membershipData.role,
          isRoleChange: action === 'accept', // Mark as role change if accepted
          // Update member count if provided in response
          community: {
            ...membershipData.community,
            member_count: response.member_count || response.community?.member_count || membershipData.community?.member_count
          }
        };
        setMembershipData(updatedMembershipData);
      }

      // Refresh membership data to get updated community stats
      try {
        setTimeout(async () => {
          await loadMembershipData();
        }, 1000); // Small delay to allow backend to process
      } catch (refreshError) {
        console.warn('Failed to refresh membership data:', refreshError);
      }

      // Call completion callback
      onComplete(action, response);

    } catch (err) {
      console.error('Error processing nomination:', err);
      setResult({
        success: false,
        action: action,
        message: err.response?.data?.error || `Failed to ${action} nomination`,
        details: err.response?.data?.detail || err.message || 'Unknown error occurred',
        timestamp: new Date().toISOString()
      });
      setError(err.response?.data?.error || `Failed to ${action} nomination`);
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = () => processNomination('accept');
  const handleDecline = () => processNomination('decline');

  if (error && !membershipData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-lg shadow-sm border p-6 text-center">
            <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Error</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            {showBackButton && (
              <button
                onClick={onBack}
                className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Go Back
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!membershipData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <SparklesIcon className="h-8 w-8 text-yellow-500" />
              <div>
                <h1 className="text-2xl font-bold mb-2">Moderator Nomination</h1>
                <p className="text-gray-600">You've been nominated to become a moderator!</p>
              </div>
            </div>
            {showBackButton && (
              <button
                onClick={onBack}
                className="flex items-center space-x-1 px-3 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <span>Back</span>
              </button>
            )}
          </div>
        </div>

        {/* Community Details */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-start space-x-4">
            <UserGroupIcon className="h-12 w-12 text-blue-500 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                {membershipData.community?.name || 'Community'}
              </h2>
              <p className="text-gray-600 mb-4">
                {membershipData.community?.description || 'Join this amazing community!'}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Assigned by:</span>
                  <p className="text-gray-600">
                    {membershipData.assigned_by?.display_name ||
                     membershipData.assigned_by?.username ||
                     'Community Admin'}
                  </p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Role:</span>
                  <p className="text-gray-600 capitalize">
                    {membershipData.role || 'Moderator'}
                  </p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Members:</span>
                  <p className="text-gray-600">
                    {membershipData.community?.member_count || 'N/A'}
                  </p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Status:</span>
                  <p className={`text-gray-600 capitalize inline-flex items-center space-x-1 ${
                    membershipData.status === 'accepted' ? 'text-green-600' :
                    membershipData.status === 'declined' ? 'text-red-600' :
                    membershipData.status === 'pending' ? 'text-yellow-600' : ''
                  }`}>
                    <span>{membershipData.status || 'Pending'}</span>
                    {membershipData.status === 'accepted' && <CheckCircleIcon className="h-4 w-4" />}
                    {membershipData.status === 'declined' && <XCircleIcon className="h-4 w-4" />}
                    {(membershipData.status === 'pending' || !membershipData.status) && <ExclamationTriangleIcon className="h-4 w-4" />}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons - Only show for actual nominations that are still pending, not role changes */}
        {!result && !membershipData?.isRoleChange &&
         (!membershipData.status || membershipData.status === 'pending') && (
          <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              What would you like to do?
            </h3>
            <p className="text-gray-600 mb-6">
              You can accept this nomination to become a moderator, or decline if you're not interested.
              {suggestedAction && (
                <span className="text-blue-600 font-medium">
                  {' '}(Suggested: {suggestedAction})
                </span>
              )}
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={handleAccept}
                disabled={loading}
                className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <CheckCircleIcon className="h-5 w-5" />
                <span>{loading ? 'Processing...' : 'Accept Nomination'}</span>
              </button>

              <button
                onClick={handleDecline}
                disabled={loading}
                className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <XCircleIcon className="h-5 w-5" />
                <span>{loading ? 'Processing...' : 'Decline Nomination'}</span>
              </button>
            </div>
          </div>
        )}

        {/* Already Processed Nomination - Show for accepted/declined nominations */}
        {!result && !membershipData?.isRoleChange &&
         membershipData.status && membershipData.status !== 'pending' && (
          <div className={`bg-white rounded-lg shadow-sm border p-6 mb-6 ${
            membershipData.status === 'accepted' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
          }`}>
            <div className="flex items-start space-x-3">
              {membershipData.status === 'accepted' ? (
                <CheckCircleIcon className="h-6 w-6 text-green-600 flex-shrink-0 mt-1" />
              ) : (
                <XCircleIcon className="h-6 w-6 text-red-600 flex-shrink-0 mt-1" />
              )}
              <div>
                <h3 className={`text-lg font-semibold mb-2 ${
                  membershipData.status === 'accepted' ? 'text-green-900' : 'text-red-900'
                }`}>
                  Nomination {membershipData.status === 'accepted' ? 'Accepted' : 'Declined'}
                </h3>
                <p className={`${
                  membershipData.status === 'accepted' ? 'text-green-800' : 'text-red-800'
                }`}>
                  {membershipData.status === 'accepted'
                    ? `You have accepted the moderator nomination for ${membershipData.community?.name}. You now have moderator privileges.`
                    : `You have declined the moderator nomination for ${membershipData.community?.name}.`
                  }
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Role Change Information - Show for role changes */}
        {membershipData?.isRoleChange && !result && (
          <div className="bg-white rounded-lg shadow-sm border p-6 mb-6 border-blue-200 bg-blue-50">
            <div className="flex items-start space-x-3">
              <CheckCircleIcon className="h-6 w-6 text-blue-600 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-blue-900 mb-2">
                  Role Assignment Complete
                </h3>
                <p className="text-blue-800">
                  Your role in <strong>{membershipData.community?.name}</strong> has been updated to <strong>moderator</strong>.
                  You now have moderator privileges in this community.
                </p>
                <p className="text-blue-700 text-sm mt-2">
                  This change was made by {membershipData.assigned_by?.display_name || 'a community administrator'}.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Result Display */}
        {result && (
          <div className={`bg-white rounded-lg shadow-sm border p-6 ${
            result.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
          }`}>
            <div className="flex items-start space-x-3">
              {result.success ? (
                <CheckCircleIcon className="h-6 w-6 text-green-600 flex-shrink-0 mt-1" />
              ) : (
                <XCircleIcon className="h-6 w-6 text-red-600 flex-shrink-0 mt-1" />
              )}
              <div className="flex-1">
                <h3 className={`text-lg font-semibold mb-2 ${
                  result.success ? 'text-green-900' : 'text-red-900'
                }`}>
                  {result.success ? 'Success!' : 'Error'}
                </h3>
                <p className={`mb-2 ${
                  result.success ? 'text-green-800' : 'text-red-800'
                }`}>
                  {result.message}
                </p>
                {result.details && result.details !== result.message && (
                  <p className={`text-sm ${
                    result.success ? 'text-green-700' : 'text-red-700'
                  }`}>
                    {result.details}
                  </p>
                )}
                <p className={`text-xs mt-2 ${
                  result.success ? 'text-green-600' : 'text-red-600'
                }`}>
                  {new Date(result.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Help Text */}
        <div className="text-center text-sm text-gray-500 mt-6">
          <p>
            Need help? Contact the community administrators or{' '}
            <a href="/support" className="text-blue-600 hover:text-blue-700">
              visit our support page
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ModeratorNominationContent;
