import React, { useState } from 'react';
import { useQuery } from 'react-query';
import TinyBadgeIcon from './TinyBadgeIcon';
import profileAPI from '../services/profileAPI';

const TinyBadgeList = ({ userId, maxVisible = 3 }) => {
  const [showAllBadges, setShowAllBadges] = useState(false);

  const { data: badges = [], isLoading, error } = useQuery(
    ['user-badges', userId],
    () => profileAPI.getUserBadges(userId),
    {
      enabled: !!userId,
      staleTime: 5 * 60 * 1000, // 5 minutes cache
      cacheTime: 15 * 60 * 1000, // 15 minutes cache
    }
  );

  if (isLoading) {
    return <div style={{fontSize: '10px', color: 'gray'}}>Loading badges...</div>;
  }

  if (error) {
    console.error('TinyBadgeList - API Error:', error);
    return null; // Hide on error
  }

  if (!badges.length) {
    return null; // Don't show anything if no badges
  }

  // Sort badges by tier priority (Gold > Silver > Bronze)
  const sortedBadges = badges.sort((a, b) => {
    const tierPriority = { 'Gold': 3, 'Silver': 2, 'Bronze': 1 };
    const tierA = tierPriority[a.badge_tier] || 0;
    const tierB = tierPriority[b.badge_tier] || 0;
    return tierB - tierA;
  });

  const visibleBadges = showAllBadges ? sortedBadges : sortedBadges.slice(0, maxVisible);
  const hasMoreBadges = sortedBadges.length > maxVisible;

  const handleToggleBadges = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setShowAllBadges(!showAllBadges);
  };

  return (
    <div className="tiny-badge-list" style={{ marginTop: '1px', marginBottom: '2px' }}>
      <div
        className="badge-container"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '2px',
          flexWrap: showAllBadges ? 'wrap' : 'nowrap'
        }}
      >
        {visibleBadges.map((userBadge, index) => (
          <TinyBadgeIcon
            key={userBadge.id || index}
            name={userBadge.badge_name}
            tier={userBadge.badge_tier}
            icon={userBadge.badge_icon}
            points={userBadge.badge_points}
            showTooltip={true}
          />
        ))}

        {hasMoreBadges && !showAllBadges && (
          <button
            className="more-badges-btn"
            onClick={handleToggleBadges}
            title={`View ${sortedBadges.length - maxVisible} more badges`}
            style={{
              background: '#f8f9fa',
              border: '1px solid #dee2e6',
              borderRadius: '50%',
              width: '12px',
              height: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '8px',
              color: '#6c757d',
              transition: 'all 0.2s ease',
              flexShrink: 0,
              padding: 0
            }}
          >
            <i className="fas fa-plus"></i>
          </button>
        )}

        {showAllBadges && hasMoreBadges && (
          <button
            className="less-badges-btn"
            onClick={handleToggleBadges}
            title="Show fewer badges"
            style={{
              background: '#f8f9fa',
              border: '1px solid #dee2e6',
              borderRadius: '50%',
              width: '12px',
              height: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '8px',
              color: '#6c757d',
              transition: 'all 0.2s ease',
              flexShrink: 0,
              padding: 0
            }}
          >
            <i className="fas fa-minus"></i>
          </button>
        )}
      </div>
    </div>
  );
};

export default TinyBadgeList;
