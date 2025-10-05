import React from 'react';
import { useNavigate } from 'react-router-dom';
import VerifyAccount from '../components/VerifyAccount';

const VerifyEmailPage = () => {
  const navigate = useNavigate();

  const handleVerificationSuccess = (result) => {
    // Navigate to user's dashboard or municipality page
    if (result.user && result.user.municipality) {
      // If user has a municipality, go to municipality dashboard
      navigate(`/municipality/${result.user.municipality}`, { replace: true });
    } else {
      // Otherwise go to general dashboard
      navigate('/dashboard', { replace: true });
    }
  };

  return (
    <VerifyAccount
      onSuccess={handleVerificationSuccess}
    />
  );
};

export default VerifyEmailPage;