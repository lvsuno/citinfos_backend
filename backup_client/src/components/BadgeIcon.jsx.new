import React, { useState, useEffect } from 'react';

const BadgeIcon = ({ name, tier, icon, points, showTooltip = true, className }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [fontAwesomeLoaded, setFontAwesomeLoaded] = useState(false);

  // CSS styles as objects
  const styles = {
    badgeIconComponent: {
      position: 'relative',
      display: 'inline-block',
      margin: '0 2px',
      isolation: 'isolate',
      zIndex: isHovered ? 1000 : 'auto',
    },
    badgeMiniIconContainer: {
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '24px',
      height: '24px',
      minWidth: '24px',
      minHeight: '24px',
      background: 'white',
      borderRadius: '50%',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      borderWidth: '1px',
      borderStyle: 'solid',
      borderColor: '#e2e8f0',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      overflow: 'visible',
      willChange: 'transform, box-shadow',
      zIndex: 'auto',
    },
    badgeMiniIconContainerHover: {
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      borderColor: '#cbd5e1',
      background: '#f1f5f9',
      zIndex: 999,
    },
    badgeMiniIcon: {
      fontSize: '12px',
      transition: 'all 0.2s ease',
      position: 'relative',
      zIndex: 1,
      display: 'inline-block',
      lineHeight: 1,
    },
    badgeTooltip: {
      position: 'absolute',
      bottom: '100%',
      left: '50%',
      transform: 'translateX(-50%)',
      marginBottom: '8px',
      opacity: 0,
      visibility: 'hidden',
      transition: 'all 0.2s ease',
      zIndex: 99999,
      pointerEvents: 'none',
    },
    badgeTooltipVisible: {
      opacity: 1,
      visibility: 'visible',
      transform: 'translateX(-50%) translateY(-4px)',
      zIndex: 99999,
    },
    tooltipContent: {
      background: 'rgba(30, 41, 59, 0.95)',
      color: 'white',
      padding: '8px 12px',
      borderRadius: '6px',
      fontSize: '12px',
      textAlign: 'center',
      whiteSpace: 'nowrap',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
      position: 'relative',
      border: '1px solid rgba(255, 255, 255, 0.1)',
    },
    tooltipName: {
      fontWeight: 600,
      marginBottom: '2px',
    },
    tooltipTier: {
      fontWeight: 500,
      fontSize: '10px',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
    },
    tooltipPoints: {
      fontSize: '10px',
      color: '#94a3b8',
      marginTop: '2px',
    }
  };

  useEffect(() => {
    // Check if FontAwesome is loaded
    const checkFontAwesome = () => {
      const testElement = document.createElement('span');
      testElement.className = 'fas fa-home';
      testElement.style.position = 'absolute';
      testElement.style.visibility = 'hidden';
      testElement.style.fontSize = '0px';
      document.body.appendChild(testElement);

      const computedStyle = window.getComputedStyle(testElement, '::before');
      const isLoaded = computedStyle.content !== 'none' && computedStyle.content !== '';

      document.body.removeChild(testElement);
      return isLoaded;
    };

    if (checkFontAwesome()) {
      setFontAwesomeLoaded(true);
    } else {
      // Check periodically if FontAwesome has loaded
      const interval = setInterval(() => {
        if (checkFontAwesome()) {
          setFontAwesomeLoaded(true);
          clearInterval(interval);
        }
      }, 100);

      // Clean up after 5 seconds
      const timeout = setTimeout(() => {
        clearInterval(interval);
        setFontAwesomeLoaded(true); // Give up and show anyway
      }, 5000);

      return () => {
        clearInterval(interval);
        clearTimeout(timeout);
      };
    }
  }, []);

  // Define tier colors (exact same as HTML)
  const tierColors = {
    Bronze: '#CD7F32',
    Silver: '#C0C0C0',
    Gold: '#FFD700'
  };

  const tierColor = tierColors[tier];

  // Show a fallback if FontAwesome isn't loaded
  if (!fontAwesomeLoaded) {
    return (
      <div
        className={className}
        style={styles.badgeIconComponent}
      >
        <div
          style={styles.badgeMiniIconContainer}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <span
            style={{
              color: tierColor,
              fontSize: '8px',
              fontWeight: 'bold'
            }}
            title={showTooltip ? `${name} (${tier})${points ? ` - ${points} points` : ''}` : ''}
          >
            {tier?.charAt(0) || '?'}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={className}
      style={styles.badgeIconComponent}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        style={{
          ...styles.badgeMiniIconContainer,
          ...(isHovered ? styles.badgeMiniIconContainerHover : {})
        }}
      >
        <i
          className={`${icon}`}
          style={{
            ...styles.badgeMiniIcon,
            color: tierColor,
            ...(isHovered ? { transform: 'scale(1.05)', opacity: 1 } : {})
          }}
          title={showTooltip ? `${name} (${tier})${points ? ` - ${points} points` : ''}` : ''}
        />
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div
          style={{
            ...styles.badgeTooltip,
            ...(isHovered ? styles.badgeTooltipVisible : {})
          }}
        >
          <div style={styles.tooltipContent}>
            <div style={styles.tooltipName}>{name}</div>
            <div style={{...styles.tooltipTier, color: tierColor}}>
              {tier}
            </div>
            {points && (
              <div style={styles.tooltipPoints}>
                {points} points
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default BadgeIcon;
