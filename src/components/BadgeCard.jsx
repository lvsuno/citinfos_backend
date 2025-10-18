import React, { useState } from 'react';

const BadgeCard = ({
  id,
  name,
  tier,
  icon, // Font Awesome class like 'fa-comments'
  description,
  points,
  earnedAt, // ISO date string when badge was earned
  size = 'medium',
  className = ''
}) => {
  const [isHovered, setIsHovered] = useState(false);
  // Define tier colors (exact same as HTML)
  const tierColors = {
    Bronze: '#CD7F32',
    Silver: '#C0C0C0',
    Gold: '#FFD700'
  };

  // Size configurations
  const sizeConfig = {
    small: {
      container: 'max-w-xs',
      cardPadding: '10px',
      iconSize: '18px',
      iconContainer: '35px',
      nameSize: '13px',
      descSize: '10px',
      tierSize: '9px'
    },
    medium: {
      container: 'w-full max-w-none', // Changed to allow full width within grid
      cardPadding: '12px',
      iconSize: '20px',
      iconContainer: '42px',
      nameSize: '14px',
      descSize: '12px',
      tierSize: '10px'
    },
    large: {
      container: 'max-w-md',
      cardPadding: '18px',
      iconSize: '28px',
      iconContainer: '60px',
      nameSize: '18px',
      descSize: '14px',
      tierSize: '12px'
    }
  };

  const config = sizeConfig[size];
  const tierColor = tierColors[tier];

  // CSS-in-JS styles
  const styles = {
    badgeCardComponent: {
      width: '100%',
      maxWidth: config.container === 'w-full max-w-none' ? 'none' :
                config.container === 'max-w-xs' ? '20rem' : '28rem'
    },
    badgeCard: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      padding: config.cardPadding,
      background: '#f8fafc',
      borderRadius: '8px',
      borderWidth: '1px',
      borderStyle: 'solid',
      borderColor: '#e2e8f0',
      transition: 'all 0.2s ease',
      width: '100%'
    },
    badgeCardHover: {
      background: '#f1f5f9',
      borderColor: '#cbd5e1',
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
    },
    badgeIconContainer: {
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: config.iconContainer,
      height: config.iconContainer,
      background: 'white',
      borderRadius: '50%',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      flexShrink: 0
    },
    badgeIcon: {
      fontSize: config.iconSize,
      transition: 'all 0.2s ease',
      color: tierColor
    },
    badgeInfo: {
      flex: 1,
      minWidth: 0
    },
    badgeName: {
      fontWeight: 600,
      color: '#1e293b',
      marginBottom: '2px',
      fontSize: config.nameSize,
      lineHeight: 1.2
    },
    badgeDescription: {
      fontSize: config.descSize,
      color: '#64748b',
      lineHeight: 1.3,
      wordWrap: 'break-word'
    },
    badgePoints: {
      fontSize: config.descSize,
      color: '#059669',
      fontWeight: 500,
      marginTop: '1px'
    },
    badgeTierSection: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'flex-end',
      gap: '2px',
      flexShrink: 0
    },
    badgeTier: {
      fontSize: config.tierSize,
      fontWeight: 500,
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
      padding: '4px 8px',
      borderRadius: '4px',
      color: 'white',
      background: tier === 'Bronze' ? '#CD7F32' :
                  tier === 'Silver' ? '#C0C0C0' : '#FFD700'
    },
    badgeTierGold: {
      color: '#1a1a1a'
    },
    earnedDate: {
      fontSize: config.tierSize,
      color: '#374151',
      fontWeight: 500,
      textAlign: 'center',
      marginTop: '4px'
    }
  };

  return (
    <div
      style={{...styles.badgeCardComponent, className}}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        style={{
          ...styles.badgeCard,
          ...(isHovered ? styles.badgeCardHover : {})
        }}
      >
        <div style={styles.badgeIconContainer}>
          <i
            className={`${icon}`}
            style={styles.badgeIcon}
          />
        </div>
        <div style={styles.badgeInfo}>
          <div style={styles.badgeName}>{name}</div>
          <div style={styles.badgeDescription}>{description}</div>
          {points && <div style={styles.badgePoints}>{points} points</div>}
        </div>
        <div style={styles.badgeTierSection}>
          <div
            style={{
              ...styles.badgeTier,
              ...(tier === 'Gold' ? styles.badgeTierGold : {})
            }}
          >
            {tier.toUpperCase()}
          </div>
          {earnedAt && (
            <div style={styles.earnedDate}>
              Earned {new Date(earnedAt).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: '2-digit'
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BadgeCard;
