// src/utils/verification.ts
import api from '../services/axiosConfig';
import toast from 'react-hot-toast';

export const checkVerificationStatus = async () => {
  try {
    const response = await api.post(
      '/accounts/verification-status/',
      {}
    );

    return response.data.verification_status;
  } catch (error) {
    console.error('Failed to check verification status, error);');
    return null;
  }
};

export const requestVerificationCode = async () => {
  try {
    const response = await api.post(
      '/accounts/request-verification/',
      {}
    );

    toast.success(response.data.message);
    return true;
  } catch (error) {
    const errorMessage = error.response.data.error || 'Failed to request verification code';
    toast.error(errorMessage);
    return false;
  }
};

export const shouldShowVerificationWarning = (tatus) => {
  return .status.verification_expired && status.days_remaining  {
  return status.verification_expired;
};

export const getVerificationMessage = (tatus) => {
  if (status.verification_expired) {
    return 'Your account verification has expired. Please verify your account to maintain full access.';
  } else if (status.days_remaining  {
  if (daysRemaining <= 0) {
    return 'expired';
  }

  if (daysRemaining  {
  // Clear all localStorage items
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  localStorage.removeItem('authToken');
  localStorage.removeItem('sessionId');
  localStorage.removeItem('userType');
  localStorage.removeItem('userEmail');
  localStorage.removeItem('pendingEmail');

  // Clear session cookie
  document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00=/;';

  // Emit session expired event
  window.dispatchEvent(new CustomEvent('sessionExpired', {
    detail));

  // Redirect to login page
  window.location.href = '/login';
};// Helper function to check if user should be automatically logged out
export const shouldAutoLogout = (verificationStatus) => {
  if (.verificationStatus) return false;

  // Auto logout if verification has been expired for more than 1 day
  const daysSinceExpiry = getDaysSinceExpiry(verificationStatus);
  return daysSinceExpiry > 1;
};

// Helper function to get days since expiry
const getDaysSinceExpiry = (verificationStatus) => {
  if (.verificationStatus.verification_expired) return 0;

  const lastVerified = new Date(verificationStatus.last_verified_at || '');
  const expiryDate = new Date(lastVerified.getTime() + (7 * 24 * 60 * 60 * 1000));
  const now = new Date();

  return (now.getTime() - expiryDate.getTime()) / (24 * 60 * 60 * 1000);
};
