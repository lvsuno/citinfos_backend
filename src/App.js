import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';
import { AuthProvider } from './contexts/AuthContext';
import { MunicipalityProvider } from './contexts/MunicipalityContext';
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
import UserProfilePage from './pages/UserProfilePage';
import ChatPage from './pages/ChatPage';
import AboutPage from './pages/AboutPage';
import ContactPage from './pages/ContactPage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminUserProfile from './pages/admin/UserProfile';
import AdminProfile from './pages/admin/AdminProfile';
import UserCreation from './pages/admin/UserCreation';
import UserManagement from './pages/admin/UserManagement';
import MunicipalityManagement from './pages/admin/MunicipalityManagement';
import SupportManagement from './pages/admin/SupportManagement';
import ModeratorDashboard from './pages/moderator/ModeratorDashboard';
import ModeratorProfile from './pages/moderator/ModeratorProfile';
import ModerationFeed from './pages/moderator/ModerationFeed';
import AccountSuspended from './pages/AccountSuspended';

// Composant pour gérer les événements globaux
const GlobalEventHandler = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleAccountSuspended = (event) => {
      const { suspensionData } = event.detail;
      console.log('🚫 Account suspended, redirecting to suspension page');
      navigate('/account-suspended', {
        state: { suspensionData },
        replace: true
      });
    };

    // Écouter l'événement de suspension de compte
    window.addEventListener('accountSuspended', handleAccountSuspended);

    return () => {
      window.removeEventListener('accountSuspended', handleAccountSuspended);
    };
  }, [navigate]);

  return null;
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <MunicipalityProvider>
          <Router>
            <GlobalEventHandler />
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/signup" element={<SignUpPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/carte" element={<MapPage />} />
              <Route path="/carte-municipalites" element={<MapPage />} />
              <Route path="/profil" element={<UserProfile />} />
              <Route path="/user/:username" element={<UserProfilePage />} />
              <Route path="/parametres" element={<UserSettingsPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/contact" element={<ContactPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />
              <Route path="/politique-confidentialite" element={<PrivacyPage />} />
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="/conditions-utilisation" element={<TermsPage />} />
              <Route path="/terms" element={<TermsPage />} />

              {/* Page de suspension de compte */}
              <Route path="/account-suspended" element={<AccountSuspended />} />

              {/* Admin routes - protected by role */}
              <Route path="/admin/dashboard" element={<AdminDashboard />} />
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/admin/profile" element={<AdminProfile />} />
              <Route path="/admin/create-user" element={<UserCreation />} />
              <Route path="/admin/users" element={<UserManagement />} />
              <Route path="/admin/users/:userId" element={<AdminUserProfile />} />
              <Route path="/admin/municipalities" element={<MunicipalityManagement />} />
              <Route path="/admin/support" element={<SupportManagement />} />

              {/* Moderator routes - protected by role */}
              <Route path="/moderator/dashboard" element={<ModeratorDashboard />} />
              <Route path="/moderator" element={<ModeratorDashboard />} />
              <Route path="/moderator/profile" element={<ModeratorProfile />} />
              <Route path="/moderator/feed" element={<ModerationFeed />} />
              <Route path="/moderator/reported" element={<ModerationFeed />} />
              <Route path="/moderator/pending" element={<ModerationFeed />} />

              {/* Dynamic routes - automatically generated based on available country data */}
              {generateDynamicRoutes()}
            </Routes>
          </Router>

          {/* Development-only Auth State Monitor - Disabled to reduce console noise */}
          {/* {process.env.NODE_ENV === 'development' && <AuthStateMonitor />} */}
        </MunicipalityProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
