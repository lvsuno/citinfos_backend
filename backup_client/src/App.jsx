import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import PropTypes from 'prop-types';

// Import components
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import { useJWTAuth, JWTAuthProvider } from './hooks/useJWTAuth';
import { NotificationProvider } from './context/NotificationContext';
import NotificationToastContainer from './components/notifications/NotificationToastContainer';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Polls from './pages/Polls';
import Communities from './pages/Communities';
// ...existing code...
import AIConversations from './pages/AIConversations';
import Profile from './pages/Profile';
import UserProfile from './pages/UserProfile';
import Login from './pages/Login';
import Register from './pages/Register';
import VerifyAccount from './pages/VerifyAccount';
import OAuthCallback from './pages/OAuthCallback';
import CreatePoll from './pages/CreatePoll';
import CommunityDetail from './pages/CommunityDetail';
import PollDetail from './pages/PollDetail';
import APITest from './components/APITest';
import AuthTest from './components/AuthTest';
import CommunityDashboard from './components/CommunityDashboard';
import PostSimulator from './pages/PostSimulator';
import PrivateChatroom from './pages/PrivateChatroom';
import ABTesting from './pages/ABTesting';
import { ABTestingProvider } from './hooks/useABTesting';
import SearchResults from './pages/SearchResults';
import SocialInteractionTest from './components/tests/SocialInteractionTest';
import BadgesPage from './pages/BadgesPage';
import BadgeDemo from './components/BadgeDemo';
import BadgeDemoKeep from './components/BadgeDemo_tokeep';
import CommunityCardDemo from './components/CommunityCardDemo';
import NotificationTester from './components/NotificationTester';
import NotificationsPage from './pages/NotificationsPage';
import NotificationDetail from './components/NotificationDetail';
import ModeratorNominationPage from './components/ModeratorNominationPage';
import AnalyticsPage from './pages/AnalyticsPage';
import AnalyticsTestPage from './components/AnalyticsTestPage';
import PostExamples from './components/PostExamples';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <JWTAuthProvider>
      <QueryClientProvider client={queryClient}>
        <NotificationProvider>
          <ABTestingProvider>
            <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/verify" element={<VerifyAccount />} />
            <Route path="/auth/callback" element={<OAuthCallback />} />

            {/* Dashboard as default entry point - will redirect to login if not authenticated */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />

            {/* Dashboard route */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />

            {/* History route */}
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <Layout>
                    <History />
                  </Layout>
                </ProtectedRoute>
              }
            />

            {/* Add other protected routes with Layout wrapper */}
            <Route
              path="/polls"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Polls />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/polls/create"
              element={
                <ProtectedRoute>
                  <Layout>
                    <CreatePoll />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/polls/:id"
              element={
                <ProtectedRoute>
                  <Layout>
                    <PollDetail />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/communities"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Communities />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/communities/:id"
              element={
                <ProtectedRoute>
                  <Layout>
                    <CommunityDetail />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/c/:slug"
              element={
                <ProtectedRoute>
                  <Layout>
                    <CommunityDetail />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Profile />
                  </Layout>
                </ProtectedRoute>
              }
            />
// ...existing code...
            <Route
              path="/ai-conversations"
              element={
                <ProtectedRoute>
                  <Layout>
                    <AIConversations />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/notifications"
              element={
                <ProtectedRoute>
                  <Layout>
                    <NotificationsPage />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/badges"
              element={
                <ProtectedRoute>
                  <Layout>
                    <BadgesPage />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <Layout>
                    <AnalyticsPage />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics-test"
              element={
                <ProtectedRoute>
                  <Layout>
                    <AnalyticsTestPage />
                  </Layout>
                </ProtectedRoute>
              }
            />
// ...existing code...
            <Route
              path="/chat"
              element={
                <ProtectedRoute>
                  <Layout>
                    <PrivateChatroom />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/user/:username"
              element={
                <ProtectedRoute>
                  <Layout>
                    <UserProfile />
                  </Layout>
                </ProtectedRoute>
              }
            />

            {/* Catch all redirect to dashboard for unauthenticated users */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>            {/* Global toast notifications */}
            <Toaster position="top-right" />

            {/* Real-time notification toasts */}
            <NotificationToastContainer />
          </Router>
        </ABTestingProvider>
      </NotificationProvider>
    </QueryClientProvider>
    </JWTAuthProvider>
  );
}

export default App;
