import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import BadgeIcon from './BadgeIcon';
import profileAPI from '../services/profileAPI';
const UserBadgeList = ({ userId, maxVisible = 3, badges: providedBadges }) => {
  const [showAllBadges, setShowAllBadges] = useState(false);
  const [hoveredButton, setHoveredButton] = useState(null);

  // If badges are provided as props, use them instead of fetching
  const shouldFetch = !providedBadges && !!userId;
  const { data: fetchedBadges = [], isLoading, error } = useQuery(
    ['user-badges', userId],
    () => profileAPI.getUserBadges(userId),
    {
      enabled: shouldFetch,
      staleTime: 5 * 60 * 1000, // 5 minutes cache
      cacheTime: 15 * 60 * 1000, // 15 minutes cache
    }
  );

  // Use provided badges or fetched badges
  const badges = providedBadges || fetchedBadges;

  const styles = {
    userBadgeList: {
      marginTop: '2px',
      marginBottom: '4px',
      position: 'relative',
      isolation: 'isolate',
      overflow: 'visible'
    },
    badgeContainer: {
      display: 'flex',
      alignItems: 'center',
      gap: '4px',
      flexWrap: showAllBadges ? 'wrap' : 'nowrap',
      position: 'relative',
      zIndex: 10
    },
    moreButton: {
      background: '#f8f9fa',
      borderWidth: '1px',
      borderStyle: 'solid',
      borderColor: '#dee2e6',
      borderRadius: '50%',
      width: '20px',
      height: '20px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      fontSize: '10px',
      color: '#6c757d',
      transition: 'all 0.2s ease',
      flexShrink: 0,
      position: 'relative',
      zIndex: 1
    },
    moreButtonHover: {
      background: '#e9ecef',
      borderColor: '#adb5bd',
      color: '#495057',
      transform: 'scale(1.05)',
      zIndex: 10
    }
  };

  // Only show loading if we're actually fetching and don't have provided badges
  if (shouldFetch && isLoading) {
    return <div style={{fontSize: '12px', color: 'gray'}}>Loading badges...</div>;
  }

  // Only show error if we were fetching (not when using provided badges)
  if (shouldFetch && error) {
    console.error('UserBadgeList - API Error:', error);
    return null; // Hide on error
  }

  if (!badges.length) {
    return null;
  }

  // Sort badges by tier priority (Gold > Silver > Bronze) and take top badges
  const sortedBadges = badges.sort((a, b) => {
    const tierPriority = { 'Gold': 3, 'Silver': 2, 'Bronze': 1 };
    // Handle both badge_definition and direct badge structures
    const badgeA = a.badge_definition || a;
    const badgeB = b.badge_definition || b;
    const tierA = tierPriority[badgeA.tier || badgeA.badge_tier] || 0;
    const tierB = tierPriority[badgeB.tier || badgeB.badge_tier] || 0;
    return tierB - tierA;
  });

  const visibleBadges = showAllBadges ? sortedBadges : sortedBadges.slice(0, maxVisible);
  const hasMoreBadges = sortedBadges.length > maxVisible;

  const handleToggleBadges = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setShowAllBadges(!showAllBadges);
  };

  const getButtonStyle = (buttonType) => {
    const isHovered = hoveredButton === buttonType;
    return {
      ...styles.moreButton,
      ...(isHovered ? styles.moreButtonHover : {})
    };
  };

  return (
    <div style={styles.userBadgeList}>
      <div style={styles.badgeContainer}>
        {visibleBadges.map((userBadge) => (
          <BadgeIcon
            key={userBadge.id}
            name={userBadge.badge_name}
            tier={userBadge.badge_tier}
            icon={userBadge.badge_icon}
            points={userBadge.badge_points}
            showTooltip={true}
            style={{ flexShrink: 0, position: 'relative', zIndex: 'auto' }}
          />
        ))}

        {hasMoreBadges && !showAllBadges && (
          <button
            style={getButtonStyle('more')}
            onClick={handleToggleBadges}
            onMouseEnter={() => setHoveredButton('more')}
            onMouseLeave={() => setHoveredButton(null)}
            title={`View ${sortedBadges.length - maxVisible} more badges`}
          >
            <i className="fas fa-plus"></i>
          </button>
        )}

        {showAllBadges && hasMoreBadges && (
          <button
            style={getButtonStyle('less')}
            onClick={handleToggleBadges}
            onMouseEnter={() => setHoveredButton('less')}
            onMouseLeave={() => setHoveredButton(null)}
            title="Show fewer badges"
          >
            <i className="fas fa-minus"></i>
          </button>
        )}
      </div>
    </div>
  );
};

export default UserBadgeList;
