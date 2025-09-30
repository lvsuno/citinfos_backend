import React, { useState } from 'react';
import {
  PlusIcon,
  QueueListIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  UserGroupIcon,
  EyeIcon,
  TrashIcon,
  StarIcon
} from '@heroicons/react/24/outline';

/**
 * ModeratorView - View for community moderators
 *
 * Moderator Permissions (from backend role creation):
 * ✅ can_post: True - Can create posts
 * ✅ can_comment: True - Can comment on posts
 * ✅ can_vote: True - Can vote on posts and comments
 * ✅ can_report: True - Can report content
 * ✅ can_moderate: True - Can moderate content (approve/reject/edit)
 * ✅ can_manage_members: True - Can manage community members
 * ✅ can_delete_posts: True - Can delete posts and comments
 * ✅ can_ban_users: True - Can ban users from community
 * ❌ can_manage_community: False - Cannot manage community settings
 * ❌ can_manage_roles: False - Cannot manage user roles
 *
 * Shows moderation tools, member management, content management
 */
const ModeratorView = ({ community, onLeave }) => {
  const [activeTab, setActiveTab] = useState('threads');

  const tabs = [
    { id: 'threads', name: 'Threads', icon: QueueListIcon },
    { id: 'posts', name: 'Recent Posts', icon: DocumentTextIcon },
    { id: 'moderation', name: 'Moderation', icon: ShieldCheckIcon },
    { id: 'reports', name: 'Reports', icon: ExclamationTriangleIcon }
  ];

  const renderModerationPanel = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Moderation Tools</h3>
        <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">Moderator</span>
      </div>

      {/* Quick moderation actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2 flex items-center">
            <EyeIcon className="h-4 w-4 mr-2" />
            Content Review
          </h4>
          <p className="text-sm text-blue-800 mb-3">Review and moderate community content</p>
          <button className="w-full bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700">
            View Pending Content
          </button>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="font-medium text-yellow-900 mb-2 flex items-center">
            <UserGroupIcon className="h-4 w-4 mr-2" />
            Member Management
          </h4>
          <p className="text-sm text-yellow-800 mb-3">Manage community members and roles</p>
          <button className="w-full bg-yellow-600 text-white px-3 py-2 rounded text-sm hover:bg-yellow-700">
            Manage Members
          </button>
        </div>
      </div>

      {/* Recent moderation activity */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">Recent Moderation Activity</h4>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-start space-x-3 p-3 bg-gray-50 rounded">
              <div className="flex-shrink-0">
                <ShieldCheckIcon className="h-5 w-5 text-purple-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">Post moderated in "Sample Thread"</p>
                <p className="text-xs text-gray-500">Content approved • 2 hours ago</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderReportsPanel = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Content Reports</h3>
        <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">3 pending</span>
      </div>

      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white border border-red-200 rounded-lg p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />
                  <span className="font-medium text-gray-900">Reported Post</span>
                  <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">Spam</span>
                </div>
                <p className="text-sm text-gray-600 mb-2">
                  "This post appears to be promotional content without context..."
                </p>
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <span>Reported by User{i}</span>
                  <span>•</span>
                  <span>1 hour ago</span>
                </div>
              </div>
              <div className="flex space-x-2">
                <button className="px-3 py-1 text-xs bg-green-100 text-green-800 rounded hover:bg-green-200">
                  Approve
                </button>
                <button className="px-3 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200">
                  Remove
                </button>
              </div>
            </div>
          </div>
        ))}
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

      {/* Moderator notice */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <p className="text-sm text-purple-800">
          <strong>Moderator Tools:</strong> You can delete inappropriate content, and manage members requests.
        </p>
      </div>

      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <h4 className="font-medium text-gray-900">Sample Thread Title {i}</h4>
                  {i === 1 && <StarIcon className="h-4 w-4 text-yellow-500" />}
                </div>
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
                <button className="p-1 text-gray-400 hover:text-yellow-600" title="Pin Thread">
                  <StarIcon className="h-4 w-4" />
                </button>
                <button className="p-1 text-gray-400 hover:text-red-600" title="Delete Thread">
                  <TrashIcon className="h-4 w-4" />
                </button>
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
                    <button className="p-1 text-gray-400 hover:text-red-600" title="Delete Post">
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <p className="text-gray-700 mb-3">
                  This is a sample post content that shows how posts appear...
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
      case 'reports':
        return renderReportsPanel();
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
            <nav className="-mb-px flex space-x-8 px-6">
              {tabs.map((tab) => {
                const IconComponent = tab.icon;
                const showBadge = tab.id === 'reports';
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 relative ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <IconComponent className="h-4 w-4" />
                    <span>{tab.name}</span>
                    {showBadge && (
                      <span className="bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                        3
                      </span>
                    )}
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
        {/* Moderator tools */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <ShieldCheckIcon className="h-5 w-5 mr-2 text-purple-600" />
            Moderator Tools
          </h3>
          <div className="space-y-3">
            <button className="w-full text-left p-3 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 transition-colors">
              Review Reports
            </button>
            <button className="w-full text-left p-3 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 transition-colors">
              Manage Members
            </button>
            <button className="w-full text-left p-3 rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-700 transition-colors">
              View Mod Logs
            </button>
          </div>
        </div>

        {/* Moderator privileges */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Privileges</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-purple-600 rounded-full mt-2 mr-2"></span>
              All member privileges
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-purple-600 rounded-full mt-2 mr-2"></span>
              Delete inappropriate posts
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-purple-600 rounded-full mt-2 mr-2"></span>
              Ban users from community
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-purple-600 rounded-full mt-2 mr-2"></span>
              Manage member requests
            </li>
          </ul>
        </div>

        {/* Leave community */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Membership</h3>
          <p className="text-sm text-gray-600 mb-4">
            You're a moderator of this community.
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

export default ModeratorView;
