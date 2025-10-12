/**
 * NotificationBadge Component
 *
 * Simple badge component that displays unread notification count
 * and provides access to notification list
 */

import React, { useState } from 'react';
import { BellIcon } from '@heroicons/react/24/outline';
import { BellIcon as BellIconSolid } from '@heroicons/react/24/solid';
import { useNotifications } from '../contexts/NotificationContext';

const NotificationBadge = () => {
  const { unreadCount, isConnected, connectionFailed, actions } = useNotifications();
  const [showDropdown, setShowDropdown] = useState(false);

  const handleBellClick = () => {
    setShowDropdown(!showDropdown);
  };

  const hasUnread = unreadCount > 0;

  return (
    <div className="relative">
      {/* Bell Icon Button */}
      <button
        onClick={handleBellClick}
        className="relative p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        aria-label="Notifications"
      >
        {hasUnread ? (
          <BellIconSolid className="h-6 w-6 text-blue-500" />
        ) : (
          <BellIcon className="h-6 w-6 text-gray-600 dark:text-gray-300" />
        )}

        {/* Unread Count Badge */}
        {hasUnread && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-500 rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}

        {/* Connection Status Indicator */}
        {!connectionFailed && (
          <span
            className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white dark:border-gray-800 ${
              isConnected ? 'bg-green-500' : 'bg-gray-400'
            }`}
            title={isConnected ? 'Connected' : 'Connecting...'}
          />
        )}

        {/* Connection Failed Indicator */}
        {connectionFailed && (
          <span
            className="absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white dark:border-gray-800 bg-red-500"
            title="Connection failed"
          />
        )}
      </button>

      {/* Simple Dropdown (will be replaced with full notification panel later) */}
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Notifications
              </h3>
              <button
                onClick={() => setShowDropdown(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* Connection Status */}
            <div className="mb-4 p-2 rounded bg-gray-50 dark:bg-gray-700">
              <div className="flex items-center space-x-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    isConnected
                      ? 'bg-green-500'
                      : connectionFailed
                      ? 'bg-red-500'
                      : 'bg-yellow-500'
                  }`}
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {isConnected
                    ? 'Connected'
                    : connectionFailed
                    ? 'Connection Failed'
                    : 'Connecting...'}
                </span>
                {connectionFailed && (
                  <button
                    onClick={actions.reconnect}
                    className="ml-auto text-xs text-blue-500 hover:text-blue-700"
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>

            {/* Unread Count */}
            <div className="text-center py-8">
              <BellIconSolid className="h-12 w-12 mx-auto mb-2 text-gray-400" />
              <p className="text-gray-600 dark:text-gray-400">
                {hasUnread
                  ? `You have ${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}`
                  : 'No new notifications'}
              </p>
              {hasUnread && (
                <button
                  onClick={() => {
                    actions.markAllAsRead();
                    setShowDropdown(false);
                  }}
                  className="mt-4 px-4 py-2 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  Mark all as read
                </button>
              )}
            </div>

            {/* Placeholder for future notification list */}
            <div className="text-xs text-center text-gray-500 dark:text-gray-400 mt-4">
              Full notification list coming soon...
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBadge;
