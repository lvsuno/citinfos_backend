import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ChartBarSquareIcon } from '@heroicons/react/24/outline';
import { useJWTAuth } from '../hooks/useJWTAuth';
import { useRedirectAfterLogin } from '../hooks/useRedirectAfterLogin';
import { verificationManager } from '../utils/verificationManager';
import {
  clearPasswordField,
  clearPasswordState,
  makePasswordInputSecure,
  protectFromDOMInspection,
  preventDevToolsPasswordExposure
} from '../utils/passwordSecurity';
import { SecureForm } from '../components/SecureForm';
import SocialLoginButtons from '../components/SocialLoginButtons';
import Register from './Register';
import VerifyAccount from './VerifyAccount';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, refreshUser } = useJWTAuth();
  const { navigateToStoredLocation, getRedirectInfo, clearStoredLocation } = useRedirectAfterLogin();
  const passwordInputRef = useRef(null);

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Modals
  const [showRegister, setShowRegister] = useState(false);
  const [showVerify, setShowVerify] = useState(false);
  const [verificationSuccess, setVerificationSuccess] = useState(false);
  const [verificationData, setVerificationData] = useState(null); // { message, userEmail, type }

  // Get redirect info for display
  const redirectInfo = getRedirectInfo();

  // Security setup - all functions enabled and working
  useEffect(() => {
    if (passwordInputRef.current) {
      makePasswordInputSecure(passwordInputRef.current);
      protectFromDOMInspection(passwordInputRef.current); // Fixed to be React-compatible
    }

    // Enable dev tools protection during login
    preventDevToolsPasswordExposure();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    // Debug: Check what values we have
    console.log('Login attempt with:', { username, password: password ? '***' : 'EMPTY' });

    if (!username || !password) {
      setError('Username and password are required');
      setIsLoading(false);
      return;
    }

    try {
      // Use the verification manager for login - keep credentials in state during API call
      console.time('login_with_verification_check');
      const result = await verificationManager.loginWithVerificationCheck(username, password, rememberMe);
      console.timeEnd('login_with_verification_check');

      if (result.success) {
  // Successful login - clear password securely and redirect to intended page
        clearPasswordState(setPassword);
        clearPasswordField(passwordInputRef.current);
  console.time('refreshUser');
  await refreshUser();
  console.timeEnd('refreshUser');

        // Use the redirect hook to navigate to stored location or default
        navigateToStoredLocation('/dashboard');
      } else if (result.requiresVerification) {
        // Verification required - clear password securely and show verification modal
        clearPasswordState(setPassword);
        clearPasswordField(passwordInputRef.current);
        setVerificationData({
          message: result.message,
          userEmail: result.userEmail,
          type: result.type || 'expired',
        });
        setShowVerify(true);
        setVerificationSuccess(false);
      } else {
        // Login failed - clear password securely and show error
        clearPasswordState(setPassword);
        clearPasswordField(passwordInputRef.current);
        setError(result.message || 'Login failed. Please check your credentials.');
      }
    } catch (error) {
      console.error('Login error:', error);
      // Error occurred - clear password securely and show error
      clearPasswordState(setPassword);
      clearPasswordField(passwordInputRef.current);
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div>
            <div className="flex justify-center">
              <ChartBarSquareIcon className="h-12 w-12 text-blue-600" />
            </div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              Welcome to SocialPoll
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              Sign in to your account to continue
            </p>
          </div>

          <form className="mt-8 space-y-6" onSubmit={handleSubmit} autoComplete="off">
            {redirectInfo && (
              <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded text-sm">
                <div className="flex items-center space-x-2">
                  <span>🔒</span>
                  <span>
                    Please log in to continue to <strong>{redirectInfo.pageName}</strong>
                  </span>
                </div>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
                {error}
              </div>
            )}

            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <label htmlFor="username" className="sr-only">
                  Username
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  autoComplete="username"
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                  placeholder="Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="password" className="sr-only">
                  Password
                </label>
                <input
                  ref={passwordInputRef}
                  id="password"
                  name="password"
                  type="password"
                  required
                  autoComplete="current-password"
                  data-lpignore="true"
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {/* Remember Me checkbox */}
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="rememberMe"
                  name="rememberMe"
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <label htmlFor="rememberMe" className="ml-2 block text-sm text-gray-900">
                  Remember me
                </label>
              </div>
            </div>

            <div className="flex items-center gap-3 overflow-visible relative">
              <button
                type="submit"
                disabled={isLoading}
                className="group relative flex-1 flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Signing in...' : 'Sign in'}
              </button>

              {/* Divider */}
              <div className="flex items-center">
                <span className="text-xs text-gray-400 px-2">or</span>
              </div>

              {/* Social Login Button */}
              <SocialLoginButtons
                onSuccess={async (result) => {
                  // Handle successful social login
                  await refreshUser();
                  navigateToStoredLocation('/dashboard');
                }}
                onError={(errorMessage) => {
                  setError(errorMessage);
                }}
                isRegistering={false}
              />
            </div>
          </form>

          <div className="text-center mt-4">
            <button
              type="button"
              className="text-blue-600 hover:underline text-sm"
              onClick={() => setShowRegister(true)}
            >
              Don't have an account? Register
            </button>
          </div>
        </div>
      </div>

      {showRegister && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-2xl relative">
            <button
              className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 text-2xl"
              onClick={() => setShowRegister(false)}
              aria-label="Close"
            >
              &times;
            </button>
            <Register onSuccess={() => {
              setShowRegister(false);
             const pendingEmail = localStorage.getItem('pendingEmail') || '';
             setVerificationData({
               message: 'We sent a verification code to your email. Enter it below to finish setting up your account.',
               userEmail: pendingEmail,
               type: 'expiring',
             });
              setShowVerify(true);
              setVerificationSuccess(false);
            }} />
          </div>
        </div>
      )}

      {showVerify && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-lg relative">
            {/* Close disabled until success */}
            <button
              className={`absolute top-2 right-2 text-gray-400 hover:text-gray-600 text-2xl ${!verificationSuccess ? 'opacity-30 cursor-not-allowed' : ''}`}
              onClick={() => verificationSuccess && setShowVerify(false)}
              aria-label="Close"
              disabled={!verificationSuccess}
              tabIndex={!verificationSuccess ? -1 : 0}
            >
              &times;
            </button>
            <VerifyAccount
              onSuccess={async () => {
                setVerificationSuccess(true);
                setShowVerify(false);
                await refreshUser();

                // Navigate to stored location or dashboard
                navigateToStoredLocation('/dashboard');
              }}
              initialEmail={verificationData?.userEmail}
              isReactivation={verificationData?.type === 'expired'}
              message={verificationData?.message}
            />
            {!verificationSuccess && (
              <div className="mt-4 text-center text-sm text-gray-500">You must complete verification to close this window.</div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default Login;
