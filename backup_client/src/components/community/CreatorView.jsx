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
  KeyIcon,
  StarIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

/**
 * CreatorView - View for community creators
 *
 * Creator Permissions (from backend role creation):
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
 * ✅ can_delete_community: True - Can delete the entire community
 *
 * Shows ultimate community control including community deletion
 */
const CreatorView = ({ community, onLeave }) => {
  const [activeTab, setActiveTab] = useState('threads');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const tabs = [
    { id: 'threads', name: 'Threads', icon: QueueListIcon },
    { id: 'posts', name: 'Recent Posts', icon: DocumentTextIcon },
    { id: 'moderation', name: 'Moderation', icon: ShieldCheckIcon },
    { id: 'administration', name: 'Administration', icon: CogIcon },
    { id: 'analytics', name: 'Analytics', icon: ChartBarIcon },
    { id: 'advanced', name: 'Creator Tools', icon: StarIcon }
  ];

  const renderCreatorToolsPanel = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Creator Tools</h3>
        <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full">Creator</span>
      </div>

      {/* Creator exclusive actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="font-medium text-yellow-900 mb-2 flex items-center">
            <StarIcon className="h-4 w-4 mr-2" />
            Community Ownership
          </h4>
          <p className="text-sm text-yellow-800 mb-3">Transfer ownership to another member</p>
          <button className="w-full bg-yellow-600 text-white px-3 py-2 rounded text-sm hover:bg-yellow-700">
            Transfer Ownership
          </button>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h4 className="font-medium text-red-900 mb-2 flex items-center">
            <TrashIcon className="h-4 w-4 mr-2" />
            Delete Community
          </h4>
          <p className="text-sm text-red-800 mb-3">Permanently delete this community</p>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="w-full bg-red-600 text-white px-3 py-2 rounded text-sm hover:bg-red-700"
          >
            Delete Community
          </button>
        </div>
      </div>

      {/* Community backup */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-4">Data Management</h4>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-blue-50 rounded">
            <div>
              <p className="text-sm font-medium text-blue-900">Export Community Data</p>
              <p className="text-xs text-blue-700">Download a complete backup of your community</p>
            </div>
            <button className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
              Export
            </button>
          </div>

          <div className="flex items-center justify-between p-3 bg-green-50 rounded">
            <div>
              <p className="text-sm font-medium text-green-900">Archive Community</p>
              <p className="text-xs text-green-700">Make community read-only while preserving data</p>
            </div>
            <button className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
              Archive
            </button>
          </div>
        </div>
      </div>

      {/* Community history */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">Community History</h4>
        <div className="space-y-3">
          <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded">
            <div className="flex-shrink-0">
              <StarIcon className="h-5 w-5 text-yellow-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-900">Community created</p>
              <p className="text-xs text-gray-500">{new Date(community.created_at).toLocaleDateString()} • You founded this community</p>
            </div>
          </div>

          <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded">
            <div className="flex-shrink-0">
              <UserGroupIcon className="h-5 w-5 text-blue-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-900">First 10 members milestone</p>
              <p className="text-xs text-gray-500">2 weeks ago • Community growth</p>
            </div>
          </div>
        </div>
      </div>

      {/* Delete confirmation modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <TrashIcon className="h-8 w-8 text-red-600" />
              <h3 className="text-lg font-semibold text-gray-900">Delete Community</h3>
            </div>

            <div className="mb-6">
              <p className="text-gray-700 mb-4">
                Are you sure you want to permanently delete <strong>{community.name}</strong>?
              </p>
              <div className="bg-red-50 border border-red-200 rounded p-3">
                <p className="text-sm text-red-800">
                  <strong>This action cannot be undone.</strong> All posts, threads, and member data will be permanently deleted.
                </p>
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  // Handle community deletion
                  setShowDeleteConfirm(false);
                }}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Delete Forever
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderAdministrationPanel = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Administration Tools</h3>
        <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">Full Access</span>
      </div>

      {/* Enhanced admin actions for creator */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2 flex items-center">
            <CogIcon className="h-4 w-4 mr-2" />
            Community Settings
          </h4>
          <p className="text-sm text-blue-800 mb-3">Full control over all community settings</p>
          <button className="w-full bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700">
            Manage Settings
          </button>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-medium text-green-900 mb-2 flex items-center">
            <UserGroupIcon className="h-4 w-4 mr-2" />
            Member Management
          </h4>
          <p className="text-sm text-green-800 mb-3">Complete member and role management</p>
          <button className="w-full bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700">
            Manage Members
          </button>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h4 className="font-medium text-purple-900 mb-2 flex items-center">
            <KeyIcon className="h-4 w-4 mr-2" />
            Role Management
          </h4>
          <p className="text-sm text-purple-800 mb-3">Create, modify, and delete all roles</p>
          <button className="w-full bg-purple-600 text-white px-3 py-2 rounded text-sm hover:bg-purple-700">
            Manage Roles
          </button>
        </div>
      </div>

      {/* Creator-specific settings */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-4">Creator Settings</h4>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Community Visibility</p>
              <p className="text-xs text-gray-500">Control who can find your community</p>
            </div>
            <select className="border border-gray-300 rounded px-3 py-1 text-sm">
              <option>Public</option>
              <option>Listed</option>
              <option>Private</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Join Approval</p>
              <p className="text-xs text-gray-500">Require approval for new members</p>
            </div>
            <input type="checkbox" className="rounded" />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Content Moderation</p>
              <p className="text-xs text-gray-500">Auto-moderate community content</p>
            </div>
            <input type="checkbox" className="rounded" defaultChecked />
          </div>
        </div>
      </div>
    </div>
  );

  const renderAnalyticsPanel = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Advanced Analytics</h3>

      {/* Enhanced metrics for creator */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Members', value: community.membership_count, change: '+12%', color: 'text-green-600' },
          { label: 'Revenue', value: '$0', change: 'N/A', color: 'text-gray-600' },
          { label: 'Retention Rate', value: '85%', change: '+3%', color: 'text-green-600' },
          { label: 'Community Score', value: '9.2', change: '+0.4', color: 'text-green-600' }
        ].map((metric, index) => (
          <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">{metric.label}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{metric.value}</p>
            <p className={`text-xs ${metric.color} mt-1`}>{metric.change}</p>
          </div>
        ))}
      </div>

      {/* Community health metrics */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-4">Community Health</h4>
        <div className="space-y-4">
          {[
            { metric: 'Member Engagement', score: 85, status: 'Excellent' },
            { metric: 'Content Quality', score: 78, status: 'Good' },
            { metric: 'Growth Rate', score: 92, status: 'Excellent' },
            { metric: 'Moderation Load', score: 65, status: 'Moderate' }
          ].map((item, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700">{item.metric}</span>
                  <span className="font-medium">{item.score}/100 - {item.status}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      item.score >= 80 ? 'bg-green-600' :
                      item.score >= 60 ? 'bg-yellow-600' : 'bg-red-600'
                    }`}
                    style={{ width: `${item.score}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // Use same thread and post rendering as AdminView but with enhanced creator controls
  const renderThreads = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Discussion Threads</h3>
        <button className="inline-flex items-center px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors">
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Thread
        </button>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800">
          <strong>Creator Access:</strong> You have ultimate control over all community content and can pin posts within threads and vote for best comments.
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
                <button className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">Pin Best</button>
                <button className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">Feature</button>
                <button className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">Delete</button>
                <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">Active</span>
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
        return <div>Recent Posts (same as AdminView)</div>; // Reuse AdminView logic
      case 'moderation':
        return <div>Moderation (same as AdminView)</div>; // Reuse AdminView logic
      case 'administration':
        return renderAdministrationPanel();
      case 'analytics':
        return renderAnalyticsPanel();
      case 'advanced':
        return renderCreatorToolsPanel();
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
        {/* Creator tools */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <StarIcon className="h-5 w-5 mr-2 text-yellow-600" />
            Creator Tools
          </h3>
          <div className="space-y-3">
            <button className="w-full text-left p-3 rounded-lg bg-yellow-50 hover:bg-yellow-100 text-yellow-700 transition-colors">
              Transfer Ownership
            </button>
            <button className="w-full text-left p-3 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 transition-colors">
              Export Data
            </button>
            <button className="w-full text-left p-3 rounded-lg bg-green-50 hover:bg-green-100 text-green-700 transition-colors">
              Archive Community
            </button>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="w-full text-left p-3 rounded-lg bg-red-50 hover:bg-red-100 text-red-700 transition-colors"
            >
              Delete Community
            </button>
          </div>
        </div>

        {/* Creator privileges */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Privileges</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 mr-2"></span>
              All administrator privileges
            </li>

            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 mr-2"></span>
              Transfer community ownership
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 mr-2"></span>
              Delete community permanently
            </li>
          </ul>
        </div>

        {/* Community founding info */}
        <div className="bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-lg shadow-sm p-6 text-white">
          <h3 className="text-lg font-semibold mb-2 flex items-center">
            <StarIcon className="h-5 w-5 mr-2" />
            Community Founder
          </h3>
          <p className="text-yellow-100 text-sm mb-4">
            You created this community on {new Date(community.created_at).toLocaleDateString()}. Thank you for building this space!
          </p>
          <div className="bg-yellow-400 bg-opacity-20 rounded p-3">
            <p className="text-xs font-medium">
              Special Powers: manage everything.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreatorView;
