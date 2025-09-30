import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  HomeIcon,
  ChartBarSquareIcon,
  UserGroupIcon,
  UserIcon,
  Bars3Icon,
  XMarkIcon,
  WrenchScrewdriverIcon,
  CpuChipIcon,
  ChatBubbleLeftRightIcon,
  PlusCircleIcon,
  BeakerIcon,
  AcademicCapIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
  MagnifyingGlassIcon,
  ArrowRightOnRectangleIcon,
  TrophyIcon,
  ChartPieIcon,
  ChevronDownIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';
import CommunityIcon from './ui/CommunityIcon';
import PropTypes from 'prop-types';
import { Toaster } from 'react-hot-toast';
import { useJWTAuth } from '../hooks/useJWTAuth';
import NotificationBell from './notifications/NotificationBell';

// Animated logo component simplified to plain GIF
const AnimatedLogo = () => (
  <img
    src="/static/images/anim-logo.gif"
    alt="App Logo"
    className="h-8 w-auto block select-none"
    draggable={false}
    decoding="async"
    loading="lazy"
  />
);

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useJWTAuth();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem('sidebarCollapsed') === 'true';
    } catch (_) {
      return false;
    }
  }); // persisted state
  const [chatDropdownOpen, setChatDropdownOpen] = useState(false);

  // Persist collapsed state cleanly
  useEffect(() => {
    try { localStorage.setItem('sidebarCollapsed', String(collapsed)); } catch (_) {}
  }, [collapsed]);

  // Close chat dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (chatDropdownOpen && !event.target.closest('[data-chat-dropdown]')) {
        setChatDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [chatDropdownOpen]);
  // Global search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('all');
  const performSearch = (e) => {
    e && e.preventDefault();
    if (!searchQuery.trim()) return;

    // Use React Router's navigate function for proper navigation
    navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}&type=${encodeURIComponent(searchType)}`);
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Force navigation even if logout fails
      navigate('/login');
    }
  };

  // Main application navigation
  const navigation = [
    { name: 'Home', href: '/dashboard', icon: HomeIcon },
    { name: 'History', href: '/history', icon: GlobeAltIcon },
    { name: 'Communities', href: '/communities', icon: UserGroupIcon },
    {
      name: 'Chats',
      icon: ChatBubbleLeftRightIcon,
      isDropdown: true,
      submenu: [
        { name: 'AI Chat', href: '/ai-conversations', icon: CpuChipIcon },
        { name: 'Private Chat', href: '/chat', icon: ChatBubbleLeftRightIcon }
      ]
    },
    { name: 'Analytics', href: '/analytics', icon: ChartPieIcon },
    { name: 'Profile', href: '/profile', icon: UserIcon }
  ];

  // Development and testing pages (conditionally shown)
  const devNavigation = [
    { name: 'Analytics Test', href: '/analytics-test', icon: BeakerIcon },
    { name: 'Badge Demo', href: '/badge-demo', icon: BeakerIcon },
    { name: 'Community Demo', href: '/community-demo', icon: UserGroupIcon },
    { name: 'Post Simulator', href: '/post-simulator', icon: PlusCircleIcon },
    { name: 'A/B Testing', href: '/ab-testing', icon: AcademicCapIcon },
    { name: 'Notification Test', href: '/notification-tester', icon: BeakerIcon },
    { name: 'API Test', href: '/api-test', icon: BeakerIcon },
    { name: 'Auth Test', href: '/auth-test', icon: AcademicCapIcon }
  ];

  // Show dev navigation only in development mode or for admin users
  const showDevNav = process.env.NODE_ENV === 'development' || user?.is_staff;

  const isActiveRoute = (href) => {
    if (href === '/') return location.pathname === '/';
    return location.pathname.startsWith(href);
  };

  const isChatRouteActive = () => {
    return location.pathname.startsWith('/ai-conversations') || location.pathname.startsWith('/chat');
  };

  // Get user display info
  const userDisplayName = user?.username || user?.first_name || 'User';
  const userInitial = userDisplayName.charAt(0).toUpperCase();

  return (

    <div className="min-h-screen flex flex-col bg-gray-100">
      {/* Global toast container */}
      <Toaster position="top-right" gutter={8} toastOptions={{ className: 'text-sm font-medium', duration: 4000 }} />
      {/* Horizontal Navigation Bar */}
      <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
        <div className="px-3 sm:px-4 lg:px-6 flex items-center h-14 justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <AnimatedLogo />
            <span className="text-lg font-bold text-gray-900 whitespace-nowrap">CityHub</span>
            <div className="flex items-center gap-1 ml-6">
              {navigation.map(item => {
                if (item.isDropdown) {
                  const isActive = isChatRouteActive();
                  return (
                    <div key={item.name} className="relative" data-chat-dropdown>
                      <button
                        onClick={() => setChatDropdownOpen(!chatDropdownOpen)}
                        className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center gap-1 ${
                          isActive ? 'bg-blue-100 text-blue-900' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        }`}
                      >
                        <CommunityIcon Icon={item.icon} color={isActive ? 'blue' : 'gray'} size="sm" />
                        <span>{item.name}</span>
                        <ChevronDownIcon className={`h-4 w-4 transition-transform duration-200 ${chatDropdownOpen ? 'rotate-180' : ''}`} />
                      </button>
                      {chatDropdownOpen && (
                        <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-50 min-w-48">
                          <div className="py-1">
                            {item.submenu.map(subItem => {
                              const subActive = isActiveRoute(subItem.href);
                              return (
                                <Link
                                  key={subItem.name}
                                  to={subItem.href}
                                  onClick={() => setChatDropdownOpen(false)}
                                  className={`block px-4 py-2 text-sm transition-colors duration-200 flex items-center gap-2 ${
                                    subActive
                                      ? 'bg-blue-50 text-blue-900'
                                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                                  }`}
                                >
                                  <CommunityIcon Icon={subItem.icon} color={subActive ? 'blue' : 'gray'} size="sm" />
                                  {subItem.name}
                                </Link>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                } else {
                  const active = isActiveRoute(item.href);
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center gap-1 ${
                        active ? 'bg-blue-100 text-blue-900' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                    >
                      <CommunityIcon Icon={item.icon} color={active ? 'blue' : 'gray'} size="sm" />
                      <span>{item.name}</span>
                    </Link>
                  );
                }
              })}
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* Global Search */}
            <form onSubmit={performSearch} className="hidden sm:flex items-center bg-gray-50 border border-gray-200 rounded-md px-2 py-1.5 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-400 transition w-80 max-w-lg">
              <MagnifyingGlassIcon className="h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={e=>setSearchQuery(e.target.value)}
                placeholder="Search..."
                className="flex-1 bg-transparent text-[13px] placeholder-gray-400 focus:outline-none"
              />
              <select
                value={searchType}
                onChange={e=>setSearchType(e.target.value)}
                className="bg-white text-[11px] border border-gray-200 rounded px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-blue-400"
                title="Filter"
              >
                <option value="all">All</option>
                <option value="posts">Posts</option>
                <option value="users">Users</option>
                <option value="communities">Communities</option>
                <option value="messages">Messages</option>
                <option value="polls">Polls</option>
                <option value="ai_conversations">AI</option>
              </select>
            </form>
            {/* Notification Bell */}
            <NotificationBell />
            {/* User Info */}
            <div className="flex items-center space-x-2">
              <div className="h-7 w-7 rounded-full bg-blue-500 flex items-center justify-center">
                <span className="text-white text-xs font-medium">{userInitial}</span>
              </div>
              <span className="text-xs font-medium text-gray-700 hidden sm:inline">{userDisplayName}</span>
              <button
                onClick={handleLogout}
                className="ml-2 px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
                title="Logout"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5 mr-1 inline-block text-gray-400 group-hover:text-gray-500" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-4">
            <div className="px-4 sm:px-5 lg:px-6">
              {children}
            </div>
          </div>

        </main>
      </div>
    </div>
  );
};

Layout.propTypes = { children: PropTypes.node.isRequired };

export default Layout;
