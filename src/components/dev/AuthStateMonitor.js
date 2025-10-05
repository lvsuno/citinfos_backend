import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import authDebugger from '../../utils/authDebugger';

/**
 * AuthStateMonitorContent - The actual monitor component
 */
const AuthStateMonitorContent = () => {
    const { user, loading } = useAuth();
    const [authState, setAuthState] = useState(null);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        // Update auth state periodically, but only show console output if tokens exist or user is logged in
        const updateAuthState = () => {
            const hasTokens = !!localStorage.getItem('access_token') || !!localStorage.getItem('refresh_token');
            const hasUser = !!user;

            // Only run the debugger if there's something meaningful to show
            if (hasTokens || hasUser) {
                const state = authDebugger.checkAuthState();
                setAuthState(state);
            } else {
                // Silent state update without console output for public pages
                setAuthState({
                    hasAccessToken: false,
                    hasRefreshToken: false,
                    accessTokenLength: 0,
                    hasSavedUser: false,
                    savedUserData: null,
                    timestamp: new Date().toISOString()
                });
            }
        };

        updateAuthState();
        const interval = setInterval(updateAuthState, 2000);

        return () => clearInterval(interval);
    }, [user]);

    const toggleVisibility = () => {
        setIsVisible(!isVisible);
    };

    const handleClearAuth = () => {
        authDebugger.clearAuthData();
        // Refresh the page to reset everything
        window.location.reload();
    };

    const handleTestRecovery = async () => {
        const result = await authDebugger.testAuthRecovery();
        if (result) {
            alert('Recovery successful! Check console for details.');
        } else {
            alert('Recovery failed. Check console for details.');
        }
    };

    return (
        <div style={{
            position: 'fixed',
            top: '10px',
            right: '10px',
            zIndex: 9999,
            backgroundColor: '#1a1a1a',
            color: '#fff',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            fontFamily: 'monospace',
            fontSize: '12px'
        }}>
            {/* Toggle Button */}
            <button
                onClick={toggleVisibility}
                style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: '#333',
                    color: '#fff',
                    border: 'none',
                    borderRadius: isVisible ? '8px 8px 0 0' : '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}
            >
                <span style={{
                    fontSize: '16px',
                    color: user ? '#10b981' : '#ef4444'
                }}>
                    🔐
                </span>
                Auth Monitor
                <span style={{ marginLeft: 'auto' }}>
                    {isVisible ? '▼' : '▶'}
                </span>
            </button>

            {/* Auth State Panel */}
            {isVisible && (
                <div style={{
                    padding: '12px',
                    borderTop: '1px solid #444'
                }}>
                    <div style={{ marginBottom: '12px' }}>
                        <strong>Current State:</strong>
                        <div style={{
                            padding: '4px 8px',
                            backgroundColor: loading ? '#f59e0b' : user ? '#10b981' : '#ef4444',
                            color: '#fff',
                            borderRadius: '4px',
                            marginTop: '4px',
                            textAlign: 'center'
                        }}>
                            {loading ? 'Loading...' : user ? `Logged in: ${user.username}` : 'Not logged in'}
                        </div>
                    </div>

                    {authState && (
                        <div style={{ marginBottom: '12px' }}>
                            <strong>Token State:</strong>
                            <ul style={{
                                margin: '4px 0',
                                paddingLeft: '16px',
                                listStyle: 'none'
                            }}>
                                <li style={{ color: authState.hasAccessToken ? '#10b981' : '#ef4444' }}>
                                    {authState.hasAccessToken ? '✓' : '✗'} Access Token
                                </li>
                                <li style={{ color: authState.hasRefreshToken ? '#10b981' : '#ef4444' }}>
                                    {authState.hasRefreshToken ? '✓' : '✗'} Refresh Token
                                </li>
                                <li style={{ color: authState.hasSavedUser ? '#10b981' : '#ef4444' }}>
                                    {authState.hasSavedUser ? '✓' : '✗'} Saved User
                                </li>
                            </ul>
                        </div>
                    )}

                    <div style={{
                        display: 'flex',
                        gap: '8px',
                        flexDirection: 'column'
                    }}>
                        <button
                            onClick={() => authDebugger.checkAuthState()}
                            style={{
                                padding: '4px 8px',
                                backgroundColor: '#3b82f6',
                                color: '#fff',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '11px'
                            }}
                        >
                            Check State
                        </button>

                        <button
                            onClick={handleTestRecovery}
                            style={{
                                padding: '4px 8px',
                                backgroundColor: '#8b5cf6',
                                color: '#fff',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '11px'
                            }}
                        >
                            Test Recovery
                        </button>

                        <button
                            onClick={handleClearAuth}
                            style={{
                                padding: '4px 8px',
                                backgroundColor: '#ef4444',
                                color: '#fff',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '11px'
                            }}
                        >
                            Clear Auth Data
                        </button>

                        <button
                            onClick={() => authDebugger.getStorageInfo()}
                            style={{
                                padding: '4px 8px',
                                backgroundColor: '#6b7280',
                                color: '#fff',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '11px'
                            }}
                        >
                            View Storage
                        </button>
                    </div>

                    <div style={{
                        marginTop: '8px',
                        fontSize: '10px',
                        color: '#9ca3af',
                        textAlign: 'center'
                    }}>
                        DEV MODE ONLY
                    </div>
                </div>
            )}
        </div>
    );
};

/**
 * AuthStateMonitor - Wrapper that only renders in development
 */
const AuthStateMonitor = () => {
    // Only render in development - this check happens before any hooks
    if (process.env.NODE_ENV !== 'development') {
        return null;
    }

    return <AuthStateMonitorContent />;
};

export default AuthStateMonitor;