import React, { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import { useQuery } from 'react-query';
import { TrophyIcon, SparklesIcon, StarIcon, LockClosedIcon, EyeIcon } from '@heroicons/react/24/outline';
import { profileAPI } from '../../services/profileAPI';
import BadgeCard from '../BadgeCard';

/* BadgesGrid
   Props:
     userId: user ID to fetch badges for (if null, fetches current user badges)
     stats: user stats object
     joinedAt: ISO date
     showAllBadges: override for showing all badges
     isOwner: whether the current user is viewing their own profile (for privacy)
*/

const Badge = ({ badge, showProgress = false }) => {
  const earned = badge.earned;
  const progress = badge.progress || 0;

  // Use the exact API data - no conversion needed
  const badgeCardProps = {
    id: badge.id,
    name: badge.name, // Direct from badge_name
    tier: badge.tier, // Direct from badge_tier
    icon: badge.icon, // Direct from badge_icon (already in Font Awesome format)
    description: badge.description,
    points: badge.points, // Direct from badge_points
    earnedAt: badge.earned ? badge.earned_at : null, // Pass earnedAt for earned badges
    size: 'medium'
  };

  return (
    <div className={`relative ${earned ? '' : 'opacity-60'}`}>
      <BadgeCard {...badgeCardProps} />

      {/* Progress Bar for Locked Badges */}
      {!earned && showProgress && (
        <div className="mt-3 px-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-medium text-gray-600">Progress</span>
            <span className="text-xs text-gray-500">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(progress, 100)}%` }}
            ></div>
          </div>
          {badge.progressInfo && (
            <p className="text-xs text-gray-500 mt-2 text-center">
              {badge.progressInfo.current_value}/{badge.progressInfo.required_value} {badge.progressInfo.stat_field?.replace(/_/g, ' ')}
              <br />
              <span className="text-blue-600 font-medium">
                {badge.progressInfo.remaining} more needed
              </span>
            </p>
          )}
        </div>
      )}      {/* Lock overlay for unearned badges */}
      {!earned && (
        <div className="absolute top-2 right-2 h-6 w-6 rounded-full bg-gray-500 flex items-center justify-center">
          <LockClosedIcon className="h-4 w-4 text-white" />
        </div>
      )}
    </div>
  );
};

Badge.propTypes = {
  badge: PropTypes.object.isRequired,
  showProgress: PropTypes.bool
};

const BadgesGrid = ({ userId = null, stats = {}, joinedAt, showAllBadges = false, isOwner = false }) => {
  const [showAllBadgesState, setShowAllBadgesState] = useState(showAllBadges);

  // Privacy check - only show badges to profile owner
  if (!isOwner) {
    return (
      <div className="text-center py-8">
        <div className="h-12 w-12 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
          <TrophyIcon className="h-6 w-6 text-gray-400" />
        </div>
        <p className="text-sm text-gray-500">Badges are private</p>
        <p className="text-xs text-gray-400 mt-1">Only visible to the profile owner</p>
      </div>
    );
  }

  // Fetch user badges from API
  const { data: badgesData = [], isLoading, error } = useQuery(
    ['user-badges', userId],
    () => profileAPI.getUserBadges(userId),
    {
      enabled: true, // Always enabled since getUserBadges handles userId = null for current user
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 15 * 60 * 1000, // 15 minutes
    }
  );

  // Fetch nearest achievable badge for locked badge display
  const { data: nearestBadgeData } = useQuery(
    ['nearest-achievable-badge', userId],
    () => profileAPI.getNearestAchievableBadge(userId),
    {
      enabled: true,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 15 * 60 * 1000, // 15 minutes
    }
  );

  // Helper function to calculate progress for locked badges using real API criteria
  const calculateProgress = (badgeDefinition, stats) => {
    if (!badgeDefinition.criteria || !stats) return 0;

    const { criteria } = badgeDefinition;
    if (criteria.type === 'stat_threshold') {
      const statField = criteria.stat; // Use 'stat' field from API
      const threshold = criteria.value; // Use 'value' field from API
      const currentValue = stats[statField] || 0;
      return Math.min(Math.round((currentValue / threshold) * 100), 100);
    }

    return 0;
  };

  // Process and format badge data
  const processedBadges = useMemo(() => {
    // Process earned badges from API
    const earnedBadges = badgesData.map(userBadge => ({
      id: userBadge.id,
      name: userBadge.badge_name, // Direct from API
      tier: userBadge.badge_tier, // Direct from API
      icon: userBadge.badge_icon, // Direct from API (already in Font Awesome format)
      description: userBadge.badge_description || `${userBadge.badge_name} badge`, // Use server description
      points: userBadge.badge_points, // Direct from API
      earned: true,
      earned_at: userBadge.earned_at,
      code: userBadge.badge_code,
      progress: 100
    }));

    // Add the nearest achievable badge as locked badge if available
    const lockedBadges = [];
    if (nearestBadgeData?.badge) {
      const nearestBadge = nearestBadgeData.badge;
      const progressInfo = nearestBadgeData.progress_info;

      lockedBadges.push({
        id: `locked-${nearestBadge.id}`,
        name: nearestBadge.name,
        tier: nearestBadge.tier,
        icon: nearestBadge.icon,
        description: nearestBadge.description || `${nearestBadge.name} achievement`,
        points: nearestBadge.points,
        earned: false,
        earned_at: null,
        code: nearestBadge.code,
        criteria: nearestBadge.criteria,
        progress: Math.round(progressInfo.progress_percentage || 0),
        progressInfo: progressInfo // Additional progress details
      });
    }

    return [...earnedBadges, ...lockedBadges];
  }, [badgesData, nearestBadgeData]);

  const computed = useMemo(() => {
    if (!processedBadges.length) return { displayBadges: [], allBadges: [], earnedCount: 0 };

    // Sort all badges by points (descending) for priority
    const sortedBadges = [...processedBadges].sort((a, b) => {
      // First sort by earned status (earned badges first)
      if (a.earned && !b.earned) return -1;
      if (!a.earned && b.earned) return 1;

      // Then by points (higher points first)
      if (a.points !== b.points) return (b.points || 0) - (a.points || 0);

      // For unearned badges, sort by progress (higher progress first)
      if (!a.earned && !b.earned) return b.progress - a.progress;

      // For earned badges, sort by earned date (most recent first)
      if (a.earned && b.earned) {
        return new Date(b.earned_at) - new Date(a.earned_at);
      }

      return 0;
    });

    // Get earned badges
    const earnedBadges = sortedBadges.filter(badge => badge.earned);

    // Get unearned badges sorted by progress (closest to completion first)
    const unearnedBadges = sortedBadges.filter(badge => !badge.earned);

    // Take top 3 earned badges + 1 closest attainable locked badge for preview
    const topEarned = earnedBadges.slice(0, 3);
    const closestLocked = unearnedBadges.slice(0, 1);

    // Display badges logic
    const displayBadges = showAllBadgesState
      ? sortedBadges
      : [...topEarned, ...closestLocked].filter(Boolean);

    return {
      displayBadges,
      allBadges: sortedBadges,
      earnedCount: earnedBadges.length
    };
  }, [processedBadges, showAllBadgesState]);

  // Loading state
  if (isLoading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-sm text-gray-500">Loading badges...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    console.error('BadgesGrid - API Error:', error);
    return (
      <div className="text-center py-8">
        <div className="h-12 w-12 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
          <TrophyIcon className="h-6 w-6 text-red-400" />
        </div>
        <p className="text-sm text-red-500">Failed to load badges</p>
        <p className="text-xs text-gray-400 mt-1">Please try again later</p>
      </div>
    );
  }

  // Empty state
  if (!computed.displayBadges.length) {
    return (
      <div className="text-center py-8">
        <div className="h-12 w-12 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
          <TrophyIcon className="h-6 w-6 text-gray-400" />
        </div>
        <p className="text-sm text-gray-500">No badges earned yet</p>
        <p className="text-xs text-gray-400 mt-1">Start engaging with the community to earn your first badge!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Badge Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {computed.displayBadges.map((badge, index) => (
          <Badge
            key={badge.id}
            badge={badge}
            showProgress={!badge.earned && !showAllBadgesState}
          />
        ))}
      </div>

      {/* See All / Show Less Button */}
      {computed.allBadges.length > 4 && (
        <div className="text-center mt-6">
          <button
            onClick={() => setShowAllBadgesState(!showAllBadgesState)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors duration-200"
          >
            <EyeIcon className="h-4 w-4" />
            {showAllBadgesState ? (
              <>Show Less ({computed.earnedCount} earned)</>
            ) : (
              <>See All Badges ({computed.allBadges.length} total)</>
            )}
          </button>
        </div>
      )}

      {/* Encouragement Text */}
      {!showAllBadgesState && computed.displayBadges.length > 0 && (
        <div className="text-center mt-4">
          <p className="text-xs text-gray-500">
            🎯 {computed.earnedCount > 0 ? 'Keep engaging to unlock more badges!' : 'Start your badge collection journey!'}
          </p>
        </div>
      )}
    </div>
  );
};

BadgesGrid.propTypes = {
  userId: PropTypes.string, // User ID to fetch badges for (null for current user)
  stats: PropTypes.object,
  joinedAt: PropTypes.string,
  showAllBadges: PropTypes.bool,
  isOwner: PropTypes.bool
};

export default BadgesGrid;
