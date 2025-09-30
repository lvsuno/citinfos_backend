/**
 * NotificationBell - Bell icon with notification count and dropdown
 *
 * Displays notification bell in header/navbar with real-time updates
 */

import React, { useState, useRef, useEffect } from 'react';
import { FaBell, FaCircle, FaWifi, FaSpinner } from 'react-icons/fa';
import { MdWifiOff } from 'react-icons/md';
import { useNotifications } from '../../context/NotificationContext';
import NotificationDropdown from './NotificationDropdown';

const NotificationBell = ({ className = '', showDropdown = true }) => {
  const {
    unreadCount,
    isConnected,
    isConnecting,
    connectionFailed,
    actions
  } = useNotifications();

  const [isOpen, setIsOpen] = useState(false);
  const [showBadgeAnimation, setShowBadgeAnimation] = useState(false);
  const bellRef = useRef(null);
  const dropdownRef = useRef(null);
  const prevUnreadCount = useRef(unreadCount);

  // Animate badge when count increases
  useEffect(() => {
    if (unreadCount > prevUnreadCount.current) {
      setShowBadgeAnimation(true);
      setTimeout(() => setShowBadgeAnimation(false), 1000);
    }
    prevUnreadCount.current = unreadCount;
  }, [unreadCount]);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        bellRef.current && !bellRef.current.contains(event.target) &&
        dropdownRef.current && !dropdownRef.current.contains(event.target)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleBellClick = () => {
    if (showDropdown) {
      setIsOpen(!isOpen);
    }
  };

  const getConnectionStatusIcon = () => {
    if (isConnecting) {
      return <FaSpinner className="h-3 w-3 text-yellow-500 animate-spin" />;
    }
    if (!isConnected || connectionFailed) {
      return <MdWifiOff className="h-3 w-3 text-red-500" />;
    }
    return <FaWifi className="h-3 w-3 text-green-500" />;
  };

  const getConnectionStatusText = () => {
    if (isConnecting) return 'Connecting...';
    if (connectionFailed) return 'Connection failed';
    if (!isConnected) return 'Disconnected';
    return 'Connected';
  };

  return (
    <div className={`relative ${className}`}>
      {/* Bell button */}
      <button
        ref={bellRef}
        onClick={handleBellClick}
        className={`
          relative p-2 rounded-full transition-all duration-200
          ${isConnected
            ? 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
            : 'text-gray-400 hover:text-gray-600'
          }
          ${isOpen ? 'bg-gray-100 text-gray-800' : ''}
          ${unreadCount > 0 ? 'animate-pulse' : ''}
        `}
        title={`Notifications (${unreadCount} unread) - ${getConnectionStatusText()}`}
      >
        <FaBell className="h-5 w-5" />

        {/* Notification count badge */}
        {unreadCount > 0 && (
          <span
            className={`
              absolute -top-1 -right-1 flex items-center justify-center
              min-w-[1.25rem] h-5 px-1 text-xs font-bold text-white
              bg-red-500 rounded-full border-2 border-white
              transition-all duration-300
              ${showBadgeAnimation ? 'animate-bounce scale-110' : 'scale-100'}
            `}
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}

        {/* Connection status indicator */}
        <div
          className="absolute -bottom-1 -right-1 bg-white rounded-full p-0.5"
          title={getConnectionStatusText()}
        >
          {getConnectionStatusIcon()}
        </div>
      </button>

      {/* Dropdown */}
      {showDropdown && isOpen && (
        <div
          ref={dropdownRef}
          className="absolute right-0 mt-2 z-50"
        >
          <NotificationDropdown onClose={() => setIsOpen(false)} />
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
