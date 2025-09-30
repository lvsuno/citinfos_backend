import React, { useState } from 'react';
import UserBadgeList from './UserBadgeList';
import FontAwesomeLoader from './FontAwesomeLoader';
import { useJWTAuth } from '../hooks/useJWTAuth';

const UserProfileCard = ({
  userId,
  userName,
  userBio = "This user hasn't added a bio yet.",
  avatar,
  postsCount = 0,
  commentsCount = 0,
  pollsCount = 0,
  memberSince,
  maxVisibleBadges = 4,
  // Privacy props
  isPrivate = false,
  canViewDetails = true,
  context = {},
  // Display options
  showBio = true,
  showAvatar = true,
  showTitle = true
}) => {
  const { user, isAuthenticated } = useJWTAuth();
  const [isHovered, setIsHovered] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 480);

  React.useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 480);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Format the member since date
  const formatMemberSince = (date) => {
    if (!date) return new Date().getFullYear();
    const year = new Date(date).getFullYear();
    return year;
  };

  // Generate placeholder avatar if none provided
  const getAvatarSrc = () => {
    if (avatar) return avatar;

    // Generate a placeholder with user's initial
    const initial = userName ? userName.charAt(0).toUpperCase() : 'U';
    return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48'%3E%3Ccircle cx='24' cy='24' r='24' fill='%23667eea'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='20' fill='white' font-family='system-ui'%3E${initial}%3C/text%3E%3C/svg%3E`;
  };

  // Check privacy settings
  const shouldShowStats = canViewDetails;
  const shouldShowBadges = context.can_view_badges !== false; // Default to true unless explicitly false

  const styles = {
    userProfileCard: {
      background: 'white',
      borderWidth: '1px',
      borderStyle: 'solid',
      borderColor: isHovered ? '#cbd5e1' : '#e2e8f0',
      borderRadius: '12px',
      padding: isMobile ? '15px' : '20px',
      transition: 'all 0.3s ease',
      boxShadow: isHovered ? '0 8px 20px rgba(0, 0, 0, 0.15)' : '0 2px 4px rgba(0, 0, 0, 0.1)',
      position: 'relative',
      overflow: 'visible',
      transform: isHovered ? 'translateY(-2px)' : 'translateY(0)',
      zIndex: isHovered ? 50 : 'auto'
    },
    cardHeader: {
      display: 'flex',
      gap: !showAvatar ? '0' : (isMobile ? '12px' : '15px'),
      alignItems: 'flex-start'
    },
    cardAvatar: {
      width: isMobile ? '40px' : '48px',
      height: isMobile ? '40px' : '48px',
      borderRadius: '50%',
      objectFit: 'cover',
      flexShrink: 0,
      borderWidth: '2px',
      borderStyle: 'solid',
      borderColor: '#e2e8f0'
    },
    cardInfo: {
      flex: 1,
      minWidth: 0
    },
    cardName: {
      color: '#2d3748',
      margin: '0 0 8px 0',
      fontSize: isMobile ? '1rem' : '1.1rem',
      fontWeight: 600,
      lineHeight: 1.2
    },
    cardBadges: {
      display: 'flex',
      alignItems: 'center',
      gap: '4px',
      marginBottom: '8px',
      position: 'relative',
      zIndex: 10,
      isolation: 'isolate',
      overflow: 'visible'
    },
    cardBio: {
      color: '#4a5568',
      fontSize: isMobile ? '13px' : '14px',
      lineHeight: 1.4,
      marginBottom: '10px',
      wordWrap: 'break-word'
    },
    cardStats: {
      display: 'flex',
      alignItems: 'center',
      gap: isMobile ? '6px' : '8px',
      fontSize: isMobile ? '11px' : '12px',
      color: '#718096',
      lineHeight: 1.3,
      flexWrap: 'wrap'
    },
    statItem: {
      display: 'flex',
      alignItems: 'center',
      gap: '4px'
    },
    statIcon: {
      width: isMobile ? '12px' : '14px',
      height: isMobile ? '12px' : '14px',
      color: '#9ca3af',
      flexShrink: 0,
      fontSize: isMobile ? '10px' : '12px',
      textAlign: 'center',
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center'
    },
    statSeparator: {
      color: '#d1d5db',
      margin: '0 2px',
      display: isMobile ? 'none' : 'block'
    },
    memberSince: {
      color: '#718096',
      fontSize: isMobile ? '10px' : 'inherit'
    },
    cardStatsPrivate: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      fontSize: '12px',
      color: '#9ca3af',
      lineHeight: 1.3,
      flexWrap: 'wrap',
      marginTop: '4px'
    },
    privateMessage: {
      display: 'flex',
      alignItems: 'center',
      gap: '4px',
      color: '#9ca3af',
      fontStyle: 'italic'
    }
  };

  return (
    <FontAwesomeLoader>
      <div
        style={styles.userProfileCard}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div style={styles.cardHeader}>
          {showAvatar && (
            <img
              src={getAvatarSrc()}
              alt={`${userName}'s avatar`}
              style={styles.cardAvatar}
            />
          )}
          <div style={styles.cardInfo}>
            {showTitle && <h5 style={styles.cardName}>{userName}</h5>}
            {userId && shouldShowBadges && (
              <div style={styles.cardBadges}>
                <UserBadgeList userId={userId} maxVisible={maxVisibleBadges} />
              </div>
            )}
            {showBio && <div style={styles.cardBio}>{userBio}</div>}
            {shouldShowStats ? (
              <div style={styles.cardStats}>
                <div style={styles.statItem}>
                  <i className="fas fa-file-alt" style={styles.statIcon}></i>
                  <span>{postsCount}</span>
                </div>
                <div style={styles.statSeparator}>•</div>
                <div style={styles.statItem}>
                  <i className="fas fa-comments" style={styles.statIcon}></i>
                  <span>{commentsCount}</span>
                </div>
                <div style={styles.statSeparator}>•</div>
                <div style={styles.statItem}>
                  <i className="fas fa-poll" style={styles.statIcon}></i>
                  <span>{pollsCount}</span>
                </div>
                <div style={styles.statSeparator}>•</div>
                <div style={styles.memberSince}>
                  Member since {formatMemberSince(memberSince)}
                </div>
              </div>
            ) : (
              <div style={styles.cardStatsPrivate}>
                <div style={styles.privateMessage}>
                  <i className="fas fa-lock" style={styles.statIcon}></i>
                  <span>This account is private</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </FontAwesomeLoader>
  );
};

export default UserProfileCard;
