import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { MunicipalityProvider } from './contexts/MunicipalityContext';
import VerifyAccount from './components/VerifyAccount';
// import AuthStateMonitor from './components/dev/AuthStateMonitor';
import { getAvailableCountries } from './config/adminDivisions';
import { generateDynamicRoutes } from './components/DynamicRoutes';
import LandingPage from './pages/LandingPage';
import SignUpPage from './pages/SignUpPage';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import MapPage from './pages/MapPage';
import UserSettingsPage from './pages/UserSettingsPage';
import UserProfile from './pages/UserProfile';
import ChatPage from './pages/ChatPage';
import AboutPage from './pages/AboutPage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';
import NotificationsPage from './pages/NotificationsPage';
import ThreadDetail from './components/social/ThreadDetail';
import ThreadsPage from './pages/ThreadsPage';

// Create a QueryClient instance for react-query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Inner component that has access to AuthContext for global verification modal
function AppContent() {
  const { user, showVerificationModal, setShowVerificationModal, verificationMessage, refreshUserData, resetVerificationModal } = useAuth();

  const handleVerificationSuccess = async () => {
    setShowVerificationModal(false);
    // Reset the flag so modal can show again if verification expires later
    if (resetVerificationModal) {
      resetVerificationModal();
    }
    // Refresh user data to update verification status
    if (refreshUserData) {
      await refreshUserData();
    }
  };

  return (
    <>
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/signup" element={<SignUpPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/carte" element={<MapPage />} />
          <Route path="/carte-municipalites" element={<MapPage />} />
          <Route path="/profil" element={<UserProfile />} />
          <Route path="/parametres" element={<UserSettingsPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          <Route path="/politique-confidentialite" element={<PrivacyPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/conditions-utilisation" element={<TermsPage />} />
          <Route path="/terms" element={<TermsPage />} />

          {/* Thread routes */}
          <Route path="/community/:communityId/threads" element={<ThreadsPage />} />
          <Route path="/community/:communityId/thread/:threadId" element={<ThreadDetail />} />

          {/* Dynamic routes - automatically generated based on available country data */}
          {generateDynamicRoutes()}
        </Routes>
      </Router>

      {/* Global Verification Modal - triggered by API interceptor when verification expires */}
      {showVerificationModal && user && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px'
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              width: '100%',
              maxWidth: '700px', // Match verification page (lg={7} = 58.33% ≈ 700px on 1200px container)
              maxHeight: '90vh',
              overflow: 'auto',
              boxShadow: '0 10px 40px rgba(0,0,0,0.3)'
            }}
          >
            <VerifyAccount
              show={showVerificationModal}
              autoSendCode={true}
              onSuccess={handleVerificationSuccess}
              userEmail={user.email}
              initialEmail={user.email}
              message={verificationMessage || 'Your account verification has expired. Please verify to continue.'}
            />
          </div>
        </div>
      )}      {/* Development-only Auth State Monitor - Disabled to reduce console noise */}
      {/* {process.env.NODE_ENV === 'development' && <AuthStateMonitor />} */}
    </>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <NotificationProvider>
            <MunicipalityProvider>
              <AppContent />
            </MunicipalityProvider>
          </NotificationProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
