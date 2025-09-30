import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import profileAPI from '../services/profileAPI';

const FollowToggleButton = ({
  userId,
  username,
  isFollowing = false,
  followStatus = null,  // 'pending', 'approved', null
  isPrivate = false,
  disabled = false
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [currentFollowingState, setCurrentFollowingState] = useState(isFollowing);
  const [currentFollowStatus, setCurrentFollowStatus] = useState(followStatus);
  const [isHovering, setIsHovering] = useState(false);
  const queryClient = useQueryClient();

  // Update local state when props change
  useEffect(() => {
    console.log(`FollowToggleButton Debug - User: ${username}, isFollowing: ${isFollowing}, followStatus: ${followStatus}, isPrivate: ${isPrivate}`);
    setCurrentFollowingState(isFollowing);
    setCurrentFollowStatus(followStatus);
  }, [isFollowing, followStatus, userId]);

  const followMutation = useMutation(
    async () => {
      // Use the smart toggle method that handles both follow and unfollow
      const result = await profileAPI.toggleFollowUser(userId);
      return result;
    },
    {
      onMutate: () => {
        setIsLoading(true);
      },
      onSuccess: (data) => {
        // Update states based on backend response
        if (data.action === 'followed') {
          setCurrentFollowingState(false); // Not approved yet if private
          // Check if it's a private profile to determine if it's pending
          const newStatus = isPrivate ? 'pending' : 'approved';
          setCurrentFollowStatus(newStatus);
          if (!isPrivate) {
            setCurrentFollowingState(true); // Immediately following for public profiles
          }
        } else if (data.action === 'unfollowed') {
          setCurrentFollowingState(false);
          setCurrentFollowStatus(null);
        } else if (data.action === 'restored') {
          // Restored relationship - check the follow status from response
          const followData = data.follow;
          const status = followData.status || (isPrivate ? 'pending' : 'approved');
          setCurrentFollowingState(status === 'approved');
          setCurrentFollowStatus(status);
        }

        // Force refresh of profile data by invalidating queries
        queryClient.invalidateQueries(['profile', userId]);
        queryClient.invalidateQueries(['profile', username]);
        queryClient.invalidateQueries(['user-profile', userId]);

        // Also refetch the current query to ensure fresh data
        queryClient.refetchQueries(['user-profile', userId]);

        setIsLoading(false);
      },
      onError: (error) => {
        console.error('❌ Follow/unfollow error:', error);
        setIsLoading(false);
      }
    }
  );

  const handleToggleFollow = () => {
    if (disabled || isLoading) return;
    followMutation.mutate();
  };

  const getButtonText = () => {
    if (isLoading) {
      if (currentFollowStatus === 'pending') return 'Cancelling...';
      return currentFollowingState ? 'Unfollowing...' : 'Following...';
    }

    if (currentFollowStatus === 'pending') {
      return isHovering ? 'Cancel Request' : 'Request Pending';
    }
    if (currentFollowingState) return 'Unfollow';
    return 'Follow';
  };

  const getButtonStyle = () => {
    if (disabled) {
      return 'bg-gray-300 text-gray-500 cursor-not-allowed';
    }

    if (currentFollowStatus === 'pending') {
      return isHovering
        ? 'bg-red-500 hover:bg-red-600 text-white transition-colors duration-200'
        : 'bg-yellow-500 hover:bg-red-500 text-white transition-colors duration-200';
    }

    if (currentFollowingState) {
      return 'bg-green-500 hover:bg-red-500 text-white transition-colors duration-200';
    }

    return 'bg-blue-500 hover:bg-blue-600 text-white';
  };

  const getButtonTitle = () => {
    if (disabled) return 'Cannot follow this user';
    if (currentFollowStatus === 'pending') return isHovering ? `Click to cancel follow request to @${username}` : `Follow request pending for @${username}`;
    if (currentFollowingState) return `Unfollow @${username}`;
    return `Follow @${username}`;
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleToggleFollow}
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
        disabled={disabled || isLoading}
        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${getButtonStyle()}`}
        title={getButtonTitle()}
      >
        {getButtonText()}
      </button>

      {/* Status indicators */}
      {currentFollowStatus === 'pending' && !isLoading && (
        <div className="flex items-center" title="Follow request pending">
          <i className="fas fa-clock text-yellow-500 text-lg"></i>
        </div>
      )}

      {currentFollowingState && currentFollowStatus === 'approved' && !isLoading && (
        <div className="flex items-center" title="You are following this user">
          <i className="fas fa-user-check text-green-500 text-lg"></i>
        </div>
      )}
    </div>
  );
};

export default FollowToggleButton;
