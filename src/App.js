import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
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
import ChatPage from './pages/ChatPage';
import AboutPage from './pages/AboutPage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <MunicipalityProvider>
          <Router>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/signup" element={<SignUpPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/carte-municipalites" element={<MapPage />} />
              <Route path="/profil" element={<UserProfile />} />
              <Route path="/parametres" element={<UserSettingsPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />
              <Route path="/politique-confidentialite" element={<PrivacyPage />} />
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="/conditions-utilisation" element={<TermsPage />} />
              <Route path="/terms" element={<TermsPage />} />

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
