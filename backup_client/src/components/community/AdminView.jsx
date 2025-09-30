import React, { useState } from 'react';
import {
  PlusIcon,
  QueueListIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  UserGroupIcon,
  CogIcon,
  ChartBarIcon,
  KeyIcon
} from '@heroicons/react/24/outline';

/**
 * AdminView - View for community administrators
 *
 * Admin Permissions (from backend role creation):
 * ✅ can_post: True - Can create posts
 * ✅ can_comment: True - Can comment on posts
 * ✅ can_vote: True - Can vote on posts and comments
 * ✅ can_report: True - Can report content
 * ✅ can_moderate: True - Can moderate content
 * ✅ can_manage_members: True - Can manage community members
 * ✅ can_manage_community: True - Can manage community settings
 * ✅ can_delete_posts: True - Can delete posts and comments
 * ✅ can_ban_users: True - Can ban users from community
 * ✅ can_manage_roles: True - Can assign/modify user roles
 * ❌ can_delete_community: False - Cannot delete the entire community
 *
 * Shows full admin controls, community settings, role management
 */
const AdminView = ({ community, onLeave }) => {
  const [activeTab, setActiveTab] = useState('threads');

  const tabs = [
    { id: 'threads', name: 'Threads', icon: QueueListIcon },
    { id: 'posts', name: 'Recent Posts', icon: DocumentTextIcon },
    { id: 'moderation', name: 'Moderation', icon: ShieldCheckIcon },
    { id: 'administration', name: 'Administration', icon: CogIcon },
    { id: 'analytics', name: 'Analytics', icon: ChartBarIcon }
  ];

  const renderAdministrationPanel = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Administration Tools</h3>
        <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">Administrator</span>
      </div>

      {/* Admin actions grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2 flex items-center">
            <CogIcon className="h-4 w-4 mr-2" />
            Community Settings
          </h4>
          <p className="text-sm text-blue-800 mb-3">Configure community rules, privacy, and features</p>
          <button className="w-full bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700">
            Manage Settings
          </button>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-medium text-green-900 mb-2 flex items-center">
            <UserGroupIcon className="h-4 w-4 mr-2" />
            Member Management
          </h4>
          <p className="text-sm text-green-800 mb-3">Manage roles, permissions, and memberships</p>
          <button className="w-full bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700">
            Manage Members
          </button>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h4 className="font-medium text-purple-900 mb-2 flex items-center">
            <KeyIcon className="h-4 w-4 mr-2" />
            Role Management
          </h4>
          <p className="text-sm text-purple-800 mb-3">Create and manage community roles</p>
          <button className="w-full bg-purple-600 text-white px-3 py-2 rounded text-sm hover:bg-purple-700">
            Manage Roles
          </button>
        </div>
      </div>

      {/* Community configuration */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-4">Community Configuration</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h5 className="text-sm font-medium text-gray-700 mb-2">Basic Settings</h5>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex justify-between">
                <span>Community Type:</span>
                <span className="font-medium">{community.community_type}</span>
              </li>
              <li className="flex justify-between">
                <span>Join Approval:</span>
                <span className="font-medium">Automatic</span>
              </li>
              <li className="flex justify-between">
                <span>Content Moderation:</span>
                <span className="font-medium">Enabled</span>
              </li>
            </ul>
          </div>
          <div>
            <h5 className="text-sm font-medium text-gray-700 mb-2">Features</h5>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex justify-between">
                <span>Threads:</span>
                <span className="text-green-600 font-medium">Enabled</span>
              </li>
              <li className="flex justify-between">
                <span>File Uploads:</span>
                <span className="text-green-600 font-medium">Enabled</span>
              </li>
              <li className="flex justify-between">
                <span>Polls:</span>
                <span className="text-green-600 font-medium">Enabled</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Recent admin activity */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">Recent Admin Activity</h4>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-start space-x-3 p-3 bg-gray-50 rounded">
              <div className="flex-shrink-0">
                <CogIcon className="h-5 w-5 text-red-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">Community settings updated</p>
                <p className="text-xs text-gray-500">Privacy settings modified • 1 day ago</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderAnalyticsPanel = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Community Analytics</h3>

      {/* Key metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Members', value: community.membership_count, change: '+12%', color: 'text-green-600' },
          { label: 'Active Today', value: '45', change: '+8%', color: 'text-green-600' },
          { label: 'Posts This Week', value: '128', change: '-3%', color: 'text-red-600' },
          { label: 'Engagement Rate', value: '73%', change: '+5%', color: 'text-green-600' }
        ].map((metric, index) => (
          <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">{metric.label}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{metric.value}</p>
            <p className={`text-xs ${metric.color} mt-1`}>{metric.change} from last week</p>
          </div>
        ))}
      </div>

      {/* Growth chart placeholder */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-4">Member Growth</h4>
        <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
          <p className="text-gray-500">📊 Analytics Chart Placeholder</p>
        </div>
      </div>

      {/* Activity breakdown */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-4">Activity Breakdown</h4>
        <div className="space-y-3">
          {[
            { activity: 'Posts Created', count: 45, percentage: 60 },
            { activity: 'Comments Posted', count: 123, percentage: 80 },
            { activity: 'Threads Started', count: 12, percentage: 30 },
            { activity: 'Member Interactions', count: 89, percentage: 70 }
          ].map((item, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-700">{item.activity}</span>
                  <span className="font-medium">{item.count}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${item.percentage}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderModerationPanel = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Advanced Moderation</h3>
        <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">Admin Access</span>
      </div>

      {/* Moderation queue */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3 flex items-center justify-between">
          Moderation Queue
          <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">5 pending</span>
        </h4>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-start justify-between p-3 bg-gray-50 rounded">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">Reported Content #{i}</p>
                <p className="text-xs text-gray-500">Multiple reports • High priority</p>
              </div>
              <div className="flex space-x-2">
                <button className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Approve</button>
                <button className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">Remove</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Banned users */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">Banned Users</h4>
        <div className="space-y-2">
          {[1, 2].map((i) => (
            <div key={i} className="flex items-center justify-between p-2 bg-red-50 rounded">
              <span className="text-sm text-gray-900">User{i} (Spam violations)</span>
              <button className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">Unban</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderThreads = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Discussion Threads</h3>
        <button className="inline-flex items-center px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors">
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Thread
        </button>
      </div>

      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-sm text-red-800">
          <strong>Admin Access:</strong> You have full control over all threads including deletion, archiving, and featured status.
        </p>
      </div>

      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 mb-1">Sample Thread Title {i}</h4>
                <p className="text-sm text-gray-600 mb-2">
                  This is a sample thread description...
                </p>
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <span>12 posts</span>
                  <span>5 contributors</span>
                  <span>2 hours ago</span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">Feature</button>
                <button className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">Archive</button>
                <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">Active</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderRecentPosts = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Recent Posts</h3>

      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-gray-300 rounded-full"></div>
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">User {i}</span>
                    <span className="text-xs text-gray-500">in Thread Name</span>
                    <span className="text-xs text-gray-500">•</span>
                    <span className="text-xs text-gray-500">3 hours ago</span>
                  </div>
                  <div className="flex space-x-1">
                    <button className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">Edit</button>
                    <button className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">Delete</button>
                  </div>
                </div>
                <p className="text-gray-700 mb-3">
                  This is a sample post content...
                </p>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <button className="hover:text-blue-600">👍 12</button>
                  <button className="hover:text-blue-600">💬 5 replies</button>
                  <button className="hover:text-blue-600">↗️ Share</button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'threads':
        return renderThreads();
      case 'posts':
        return renderRecentPosts();
      case 'moderation':
        return renderModerationPanel();
      case 'administration':
        return renderAdministrationPanel();
      case 'analytics':
        return renderAnalyticsPanel();
      default:
        return renderThreads();
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
      <div className="lg:col-span-3 space-y-6">
        {/* Tab navigation */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6 overflow-x-auto">
              {tabs.map((tab) => {
                const IconComponent = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 whitespace-nowrap ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <IconComponent className="h-4 w-4" />
                    <span>{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="p-6">
            {renderTabContent()}
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* Admin tools */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <CogIcon className="h-5 w-5 mr-2 text-red-600" />
            Admin Tools
          </h3>
          <div className="space-y-3">
            <button className="w-full text-left p-3 rounded-lg bg-red-50 hover:bg-red-100 text-red-700 transition-colors">
              Community Settings
            </button>
            <button className="w-full text-left p-3 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 transition-colors">
              Role Management
            </button>
            <button className="w-full text-left p-3 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 transition-colors">
              Analytics Dashboard
            </button>
            <button className="w-full text-left p-3 rounded-lg bg-yellow-50 hover:bg-yellow-100 text-yellow-700 transition-colors">
              Content Management
            </button>
          </div>
        </div>

        {/* Admin privileges */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Privileges</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-red-600 rounded-full mt-2 mr-2"></span>
              All moderator privileges
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-red-600 rounded-full mt-2 mr-2"></span>
              Manage community settings
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-red-600 rounded-full mt-2 mr-2"></span>
              Create and manage roles
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-red-600 rounded-full mt-2 mr-2"></span>
              Access analytics and insights
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-red-600 rounded-full mt-2 mr-2"></span>
              Manage community features
            </li>
          </ul>
        </div>

        {/* Leave community */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Membership</h3>
          <p className="text-sm text-gray-600 mb-4">
            You're an administrator of this community.
          </p>
          <button
            onClick={onLeave}
            className="w-full text-center p-2 rounded-lg bg-red-50 hover:bg-red-100 text-red-700 text-sm transition-colors"
          >
            Leave Community
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminView;
