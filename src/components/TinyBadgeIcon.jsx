import React, { useState, useEffect } from 'react';

const TinyBadgeIcon = ({
  name,
  tier,
  icon,
  points,
  showTooltip = true
}) => {
  const [fontAwesomeLoaded, setFontAwesomeLoaded] = useState(false);

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

  if (!name || !tier || !icon) return null;

  // Tier-based colors
  const tierColors = {
    Bronze: '#CD7F32',
    Silver: '#C0C0C0',
    Gold: '#FFD700'
  };

  const tierColor = tierColors[tier] || '#6B7280';
  const title = showTooltip ? `${name} (${tier})` : '';

  // Show a fallback if FontAwesome isn't loaded
  if (!fontAwesomeLoaded) {
    return (
      <span
        className="inline-flex items-center justify-center flex-shrink-0 h-3 w-3 text-xs font-bold rounded-full"
        style={{ backgroundColor: tierColor, color: 'white', fontSize: '6px' }}
        title={title}
      >
        {tier.charAt(0)}
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center justify-center flex-shrink-0 h-3 w-3 hover:scale-110 transition-transform duration-100 ease-in-out"
      title={title}
    >
      <i
        className={icon} // Use icon directly since it already includes 'fas fa-'
        style={{
          color: tierColor,
          fontSize: '10px',
          lineHeight: 1
        }}
      />
    </span>
  );
};

export default TinyBadgeIcon;
