import React, { useState } from 'react';
import {
  CogIcon,
  ShieldCheckIcon,
  UserGroupIcon,
  ExclamationTriangleIcon,
  TrashIcon,
  KeyIcon,
  BellIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

/**
 * CommunitySettings - Role-based settings component
 *
 * Different settings available based on user role:
 * - Non-member: Only join button
 * - Member: Notification settings, leave community
 * - Moderator: Member management, content moderation
 * - Admin: Community settings, role management
 * - Creator: All settings + delete community
 */
const CommunitySettings = ({
  community,
  userRole = 'non-member',
  currentUserId,
  onJoin,
  onLeave,
  onUpdateSettings,
  onDeleteCommunity
}) => {
  const [activeTab, setActiveTab] = useState('general');

  // Define available tabs based on user role
  const getAvailableTabs = () => {
    const baseTabs = [];

    if (userRole === 'non-member') {
      return [{ id: 'join', name: 'Join Community', icon: UserGroupIcon }];
    }

    // Member and above
    baseTabs.push({ id: 'general', name: 'General', icon: CogIcon });
    baseTabs.push({ id: 'notifications', name: 'Notifications', icon: BellIcon });

    // Moderator and above
    if (['moderator', 'admin', 'creator'].includes(userRole)) {
      baseTabs.push({ id: 'moderation', name: 'Moderation', icon: ShieldCheckIcon });
      baseTabs.push({ id: 'members', name: 'Members', icon: UserGroupIcon });
    }

    // Admin and creator
    if (['admin', 'creator'].includes(userRole)) {
      baseTabs.push({ id: 'community', name: 'Community', icon: CogIcon });
      baseTabs.push({ id: 'roles', name: 'Roles', icon: KeyIcon });
    }

    // Creator only
    if (userRole === 'creator') {
      baseTabs.push({ id: 'danger', name: 'Danger Zone', icon: ExclamationTriangleIcon });
    }

    return baseTabs;
  };

  const renderJoinCommunity = () => (
    <div className="space-y-6">
      <div className="text-center py-8">
        <UserGroupIcon className="h-16 w-16 text-blue-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Join the Community</h3>
        <p className="text-gray-600 mb-6">
          Become a member to participate in discussions, create threads, and connect with other members.
        </p>
        <button
          onClick={onJoin}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          Join Community
        </button>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">What you can do as a member:</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Create and participate in discussion threads</li>
          <li>• Post content within threads (no direct community posts)</li>
          <li>• Comment on posts and vote on content</li>
          <li>• As thread author: Pin posts and vote for best comments</li>
        </ul>
      </div>
    </div>
  );

  const renderGeneralSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">General Settings</h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-gray-200">
            <div>
              <span className="font-medium text-gray-900">Membership Status</span>
              <p className="text-sm text-gray-600">Your current role in this community</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              userRole === 'creator' ? 'bg-orange-100 text-orange-800' :
              userRole === 'admin' ? 'bg-red-100 text-red-800' :
              userRole === 'moderator' ? 'bg-purple-100 text-purple-800' :
              'bg-green-100 text-green-800'
            }`}>
              {userRole.charAt(0).toUpperCase() + userRole.slice(1)}
            </span>
          </div>

          <div className="flex items-center justify-between py-3 border-b border-gray-200">
            <div>
              <span className="font-medium text-gray-900">Thread Creation</span>
              <p className="text-sm text-gray-600">You can create new discussion threads</p>
            </div>
            <span className="text-green-600 font-medium">Enabled</span>
          </div>

          <div className="flex items-center justify-between py-3 border-b border-gray-200">
            <div>
              <span className="font-medium text-gray-900">Post Within Threads</span>
              <p className="text-sm text-gray-600">Posts must be made within threads only</p>
            </div>
            <span className="text-green-600 font-medium">Enabled</span>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-medium text-yellow-900 mb-2">Thread Author Privileges</h4>
            <p className="text-sm text-yellow-700">
              When you create a thread, you can pin important posts and vote for the best comments to highlight valuable contributions.
            </p>
          </div>
        </div>
      </div>

      <div className="pt-6 border-t border-gray-200">
        <button
          onClick={onLeave}
          className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
        >
          Leave Community
        </button>
      </div>
    </div>
  );

  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Notification Settings</h3>

      <div className="space-y-4">
        {[
          { name: 'New threads in community', description: 'Get notified when new threads are created' },
          { name: 'Posts in your threads', description: 'Get notified when someone posts in threads you created' },
          { name: 'Comments on your posts', description: 'Get notified when someone comments on your posts' },
          { name: 'Your comments voted as best', description: 'Get notified when thread authors mark your comments as best' },
          { name: 'Community announcements', description: 'Get notified about important community updates' }
        ].map((setting, index) => (
          <div key={index} className="flex items-center justify-between py-3 border-b border-gray-200">
            <div>
              <span className="font-medium text-gray-900">{setting.name}</span>
              <p className="text-sm text-gray-600">{setting.description}</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        ))}
      </div>
    </div>
  );

  const renderModerationSettings = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Moderation Tools</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">Content Moderation</h4>
          <p className="text-sm text-gray-600 mb-3">Manage posts and comments</p>
          <ul className="text-sm space-y-1">
            <li>• Delete inappropriate posts</li>
            <li>• Remove harmful comments</li>
            <li>• Review reported content</li>
          </ul>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">Member Management</h4>
          <p className="text-sm text-gray-600 mb-3">Manage community members</p>
          <ul className="text-sm space-y-1">
            <li>• Temporary user suspensions</li>
            <li>• Ban problematic users</li>
            <li>• Review join requests</li>
          </ul>
        </div>
      </div>
    </div>
  );

  const renderDangerZone = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-red-900 mb-4">Danger Zone</h3>

      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <ExclamationTriangleIcon className="h-6 w-6 text-red-600 flex-shrink-0 mt-1" />
          <div className="flex-1">
            <h4 className="font-medium text-red-900 mb-2">Delete Community</h4>
            <p className="text-sm text-red-700 mb-4">
              Permanently delete this community and all its content. This action cannot be undone.
              All threads, posts, comments, and member data will be lost forever.
            </p>
            <button
              onClick={onDeleteCommunity}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors font-medium"
            >
              <TrashIcon className="h-4 w-4 inline mr-2" />
              Delete Community
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'join':
        return renderJoinCommunity();
      case 'general':
        return renderGeneralSettings();
      case 'notifications':
        return renderNotificationSettings();
      case 'moderation':
        return renderModerationSettings();
      case 'members':
        return <div>Member management coming soon...</div>;
      case 'community':
        return <div>Community settings coming soon...</div>;
      case 'roles':
        return <div>Role management coming soon...</div>;
      case 'danger':
        return renderDangerZone();
      default:
        return renderGeneralSettings();
    }
  };

  const tabs = getAvailableTabs();

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Tab Navigation */}
      {tabs.length > 1 && (
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>
      )}

      {/* Tab Content */}
      <div className="p-6">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default CommunitySettings;
