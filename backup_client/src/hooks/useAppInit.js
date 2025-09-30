// src/hooks/useAppInit.js
// React hook for application initialization with automatic verification checking
import { useState, useEffect } from 'react';
import { verificationManager } from '../utils/verificationManager';

/**
 * Hook for initializing the app with automatic verification checking
 * Call this in your main App component or route guard
 * @returns {Object} Initialization status and verification state
 */
export const useAppInit = () => {
  const [initState, setInitState] = useState({
    loading: true,
    loggedIn: false,
    verificationExpired: false,
    error: null,
    user: null
  });

  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Check verification status on app load
        const status = await verificationManager.checkVerificationStatusOnLoad();

        if (status.checking) {
          // Still checking, keep loading
          return;
        }

        if (status.expired) {
          // Verification expired - user will be redirected to login
          setInitState({
            loading: false,
            loggedIn: false,
            verificationExpired: true,
            error: null,
            user: null
          });
          return;
        }

        if (status.loggedIn) {
          // User is logged in with valid verification
          const user = JSON.parse(localStorage.getItem('user') || '{}');
          setInitState({
            loading: false,
            loggedIn: true,
            verificationExpired: false,
            error: null,
            user: user
          });
        } else {
          // User not logged in
          setInitState({
            loading: false,
            loggedIn: false,
            verificationExpired: false,
            error: null,
            user: null
          });
        }

      } catch (error) {
        console.error('App initialization error:', error);
        setInitState({
          loading: false,
          loggedIn: false,
          verificationExpired: false,
          error: 'Failed to initialize app',
          user: null
        });
      }
    };

    initializeApp();

    // Listen for verification state changes
    const unsubscribe = verificationManager.onVerificationStateChange((state) => {
      if (state.expired || state.loggedOut) {
        setInitState(prev => ({
          ...prev,
          loggedIn: false,
          verificationExpired: true,
          user: null
        }));
      } else if (state.verified && state.user) {
        setInitState(prev => ({
          ...prev,
          loggedIn: true,
          verificationExpired: false,
          user: state.user
        }));
      }
    });

    return unsubscribe;
  }, []);

  return initState;
};

export default useAppInit;
