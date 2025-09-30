import { useState, useEffect } from 'react';
import { useJWTAuth } from '../hooks/useJWTAuth';
import { verificationManager } from '../utils/verificationManager';

const RESEND_TIMEOUT = 300; // seconds

const VerifyAccount = ({ onSuccess, initialEmail, isReactivation = false, message }) => {
  const { verifyEmail, resendVerificationCode } = useJWTAuth();

  const [form, setForm] = useState({ email: initialEmail || '', code: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [resendTimer, setResendTimer] = useState(RESEND_TIMEOUT);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (!initialEmail) {
      const savedEmail = localStorage.getItem('pendingEmail');
      if (savedEmail) setForm((prev) => ({ ...prev, email: savedEmail }));
    }
  }, [initialEmail]);

  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Use the new verification manager for verification
      const result = await verificationManager.verifyCodeAndLogin(form.email, form.code);

      if (result.success) {
        localStorage.removeItem('pendingEmail');

        // Set success message first to show green checkmark
        setSuccess(result.message || 'Account verified successfully!');

        if (onSuccess) {
          // If there's an onSuccess callback, show success for a moment then close
          setTimeout(() => {
            onSuccess();
          }, 1500); // Give time to see the success message
        } else {
          // If no onSuccess callback, show success and redirect
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 2000);
        }
      } else {
        setError(result.message || 'Verification failed. Please try again.');
      }
    } catch (err) {
      console.error('Verification error:', err);
      // Check if it's actually a successful response disguised as an error
      if (err?.response?.data?.success) {
        setSuccess(err.response.data.message || 'Account verified successfully!');
        if (onSuccess) {
          setTimeout(() => {
            onSuccess();
          }, 1500);
        } else {
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 2000);
        }
      } else {
        setError(err?.response?.data?.message || err?.message || 'Verification failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setError(null);

    try {
      // Use the new verification manager for resending codes
      const success = await verificationManager.resendVerificationCode(form.email);
      if (success) {
        setResendTimer(RESEND_TIMEOUT);
      }
    } catch (err) {
      console.error('Resend error:', err);
      setError(err?.response?.data?.message || err?.message || 'Failed to resend code. Please wait and try again.');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="verify-form-container">
      <h2>{isReactivation ? 'Account Verification Required' : 'Verify Your Account'}</h2>
      {message && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-center">
            <span className="text-yellow-600 mr-2">⚠️</span>
            <p className="text-sm text-yellow-800">{message}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <label className="block text-sm font-medium mb-1">Email</label>
        <input
          name="email"
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={handleChange}
          required
          disabled={!!form.email}
        />
        <small className="block text-gray-500 mb-2">We sent a code to this email.</small>

        <label className="block text-sm font-medium mt-3 mb-1">Verification Code</label>
        <input name="code" placeholder="Enter verification code" value={form.code} onChange={handleChange} required />

        <button
          type="submit"
          disabled={loading}
          className="mt-4 w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-extrabold uppercase tracking-wide rounded-lg shadow-lg hover:from-blue-700 hover:to-purple-700 transform hover:-translate-y-0.5 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Verifying...' : 'Verify Account'}
        </button>
      </form>

      <div className="mt-5 flex flex-col items-center">
        <button
          type="button"
          onClick={handleResend}
          disabled={resendTimer > 0 || resending || !form.email}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition disabled:opacity-50"
        >
          {resending ? 'Resending...' : resendTimer > 0 ? `Resend code in ${resendTimer}s` : 'Resend Code'}
        </button>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-center">
          <span className="block sm:inline">❌ {error}</span>
        </div>
      )}
      {success && (
        <div className="mt-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded text-center">
          <span className="block sm:inline">✅ {success}</span>
          {!onSuccess && (
            <div className="mt-2 text-sm text-green-600">
              Redirecting to dashboard...
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VerifyAccount;
