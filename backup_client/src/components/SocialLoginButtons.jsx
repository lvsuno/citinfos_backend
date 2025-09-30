import React, { useState, useEffect } from 'react';
import { FaGoogle, FaFacebook, FaGithub, FaTwitter, FaPlus, FaTimes } from 'react-icons/fa';
import socialAuthService from '../services/socialAuth';
import { useJWTAuth } from '../hooks/useJWTAuth';
import { useRedirectAfterLogin } from '../hooks/useRedirectAfterLogin';

const SocialLoginButtons = ({ onSuccess, onError, isRegistering = false }) => {
  const [loadingProvider, setLoadingProvider] = useState(null);
  const [availableProviders, setAvailableProviders] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const { login } = useJWTAuth();
  const { navigateToStoredLocation } = useRedirectAfterLogin();

  // Load available providers from backend
  useEffect(() => {
    const loadProviders = async () => {
      try {
        const providers = await socialAuthService.getAvailableProviders();
        setAvailableProviders(providers);
      } catch (error) {
        console.warn('Failed to load providers:', error);
        // Use default providers if backend call fails - always show the button
        setAvailableProviders(['google', 'facebook', 'github', 'twitter']);
      }
    };
    loadProviders();
  }, []);

  const handleSocialLogin = async (provider) => {
    if (loadingProvider) return;

    setLoadingProvider(provider);
    setIsExpanded(false); // Close arc

    try {
      const authUrl = await socialAuthService.getOAuthURL(provider);
      window.location.href = authUrl;
    } catch (error) {
      console.error(`${provider} login error:`, error);
      if (onError) {
        onError(`Failed to ${isRegistering ? 'register' : 'sign in'} with ${provider}. Please try again.`);
      }
    } finally {
      setLoadingProvider(null);
    }
  };

  const providerConfig = {
    google: {
      name: 'Google',
      icon: FaGoogle,
      bgColor: 'bg-red-500',
      hoverColor: 'hover:bg-red-600',
    },
    facebook: {
      name: 'Facebook',
      icon: FaFacebook,
      bgColor: 'bg-blue-600',
      hoverColor: 'hover:bg-blue-700',
    },
    github: {
      name: 'GitHub',
      icon: FaGithub,
      bgColor: 'bg-gray-800',
      hoverColor: 'hover:bg-gray-900',
    },
    twitter: {
      name: 'Twitter',
      icon: FaTwitter,
      bgColor: 'bg-blue-400',
      hoverColor: 'hover:bg-blue-500',
    },
  };

  // Filter providers based on availability
  const socialProviders = availableProviders
    .filter(provider => providerConfig[provider])
    .map(provider => ({
      provider,
      ...providerConfig[provider]
    }));

  const getArcPosition = (index, total) => {
    if (total === 1) {
      return { x: 0, y: -80 };
    }

    // Create a wider arc spanning 160 degrees for more dramatic spread
    const arcSpan = (160 * Math.PI) / 180; // Convert to radians
    const startAngle = -arcSpan / 2; // Center the arc
    const angle = startAngle + (index * arcSpan) / (total - 1);
    const radius = 80; // Increased radius for more dramatic effect

    return {
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius - 20, // More upward bias
    };
  };

  // Always show the component, even if no providers are configured
  // The button will be disabled if no providers are available

  return (
    <div className="relative flex items-center justify-center overflow-visible" style={{ minHeight: '100px', minWidth: '180px' }}>
      {/* Toggle Button */}
      <button
        type="button"
        onClick={() => socialProviders.length > 0 ? setIsExpanded(!isExpanded) : null}
        disabled={socialProviders.length === 0}
        className={`
          relative z-20 h-10 px-3 rounded-md border-2 transition-all duration-300 ease-in-out
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          flex items-center gap-1 text-xs font-medium
          ${socialProviders.length === 0
            ? 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed'
            : isExpanded
              ? 'border-blue-500 bg-blue-50 text-blue-600'
              : 'border-gray-300 bg-white text-gray-600 hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600'
          }
        `}
        aria-label={
          socialProviders.length === 0
            ? 'Social login not configured'
            : isExpanded
              ? 'Close social login options'
              : 'Sign in with social accounts'
        }
        title={
          socialProviders.length === 0
            ? 'Social login providers not configured'
            : isExpanded
              ? 'Close social login options'
              : `Sign in with ${socialProviders.map(p => p.name).join(', ')}`
        }
      >
        {socialProviders.length === 0 ? (
          <>
            <FaGoogle className="w-3 h-3 opacity-50" />
            <span>Social</span>
          </>
        ) : isExpanded ? (
          <>
            <FaTimes className="w-3 h-3" />
            <span>Close</span>
          </>
        ) : (
          <>
            <FaGoogle className="w-3 h-3" />
            <span>Social</span>
          </>
        )}
      </button>

      {/* Social Provider Buttons in Arc */}
      {socialProviders.map((provider, index) => {
        const position = getArcPosition(index, socialProviders.length);
        const IconComponent = provider.icon;
        const isLoading = loadingProvider === provider.provider;

        return (
          <button
            key={provider.provider}
            type="button"
            onClick={() => handleSocialLogin(provider.provider)}
            disabled={isLoading || loadingProvider}
            className={`
              absolute w-10 h-10 rounded-full shadow-xl transition-all duration-700 ease-out
              ${provider.bgColor} ${provider.hoverColor} text-white
              hover:scale-150 hover:shadow-2xl focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white
              disabled:opacity-50 disabled:cursor-not-allowed transform-gpu
              ${isExpanded
                ? 'opacity-100 scale-100 pointer-events-auto'
                : 'opacity-0 scale-0 pointer-events-none'
              }
            `}
            style={{
              transform: isExpanded
                ? `translate(${position.x}px, ${position.y}px) scale(1)`
                : 'translate(0, 0) scale(0)',
              transitionDelay: isExpanded ? `${index * 120}ms` : '0ms',
              zIndex: 15,
            }}
            aria-label={`${isRegistering ? 'Register' : 'Sign in'} with ${provider.name}`}
            title={`${isRegistering ? 'Register' : 'Sign in'} with ${provider.name}`}
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto" />
            ) : (
              <IconComponent className="w-4 h-4 mx-auto" />
            )}
          </button>
        );
      })}

      {/* Background Overlay for Click Outside */}
      {isExpanded && (
        <div
          className="fixed inset-0 z-10"
          onClick={() => setIsExpanded(false)}
          aria-hidden="true"
        />
      )}
    </div>
  );
};

export default SocialLoginButtons;