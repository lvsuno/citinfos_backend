import React, { useState } from 'react';
import {
  PlusIcon,
  QueueListIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  StarIcon
} from '@heroicons/react/24/outline';

/**
 * MemberView - View for regular community members
 *
 * Member Permissions (from backend role creation):
 * ✅ can_post: True - Can create posts within threads
 * ✅ can_comment: True - Can comment on posts
 * ✅ can_vote: True - Can vote on posts and comments
 * ✅ can_report: True - Can report inappropriate content
 * ❌ can_moderate: False - Cannot moderate content
 * ❌ can_manage_members: False - Cannot manage members
 * ❌ can_manage_community: False - Cannot manage community settings
 *
 * Shows threads, allows creating posts within threads, basic community interaction
 */
const MemberView = ({ community, onLeave }) => {
  const [activeTab, setActiveTab] = useState('threads');

  const tabs = [
    { id: 'threads', name: 'Threads', icon: QueueListIcon },
    { id: 'posts', name: 'Recent Posts', icon: DocumentTextIcon },
    { id: 'activity', name: 'Activity', icon: ChatBubbleLeftRightIcon }
  ];

  const renderThreads = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Discussion Threads</h3>
        <button className="inline-flex items-center px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors">
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Thread
        </button>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> All posts must be created within threads. Thread authors can pin important posts and vote for the best comments in their own threads.
        </p>
      </div>

      {/* Thread list placeholder */}
      <div className="space-y-3">
        {/* Sample Thread 1 - Pinned by Creator */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <h4 className="font-medium text-gray-900">Welcome & Community Guidelines</h4>
                <StarIcon className="h-4 w-4 text-yellow-500" title="Pinned by thread creator" />
              </div>
              <p className="text-sm text-gray-600 mb-2">
                Please read our community guidelines and introduce yourself to other members...
              </p>
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>15 posts</span>
                <span>8 contributors</span>
                <span>Created by @moderator</span>
                <span>1 day ago</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full">Pinned</span>
              <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">Active</span>
            </div>
          </div>
        </div>

        {/* Sample Thread 2 - Regular Thread */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="font-medium text-gray-900 mb-1">Tips & Tricks Discussion</h4>
              <p className="text-sm text-gray-600 mb-2">
                Share your best tips and tricks with the community. What works for you?
              </p>
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>8 posts</span>
                <span>5 contributors</span>
                <span>Created by @user123</span>
                <span>2 hours ago</span>
              </div>
              <div className="flex items-center space-x-2 mt-2">
                <span className="text-xs text-blue-600">💎 Best comment by @expert_user</span>
                <span className="text-xs text-gray-400">- voted by thread author</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">Active</span>
            </div>
          </div>
        </div>

        {/* Sample Thread 3 - Your Thread */}
        <div className="bg-white border border-blue-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <h4 className="font-medium text-gray-900">Equipment Recommendations</h4>
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">Your Thread</span>
              </div>
              <p className="text-sm text-gray-600 mb-2">
                Looking for equipment recommendations? Share what you need and get suggestions...
              </p>
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>3 posts</span>
                <span>2 contributors</span>
                <span>Created by you</span>
                <span>5 hours ago</span>
              </div>
              <div className="flex items-center space-x-3 mt-2 text-xs">
                <span className="text-blue-600 font-medium">As thread author, you can:</span>
                <span className="text-yellow-600">📌 Pin posts</span>
                <span className="text-purple-600">💎 Vote best comments</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">Manage</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderRecentPosts = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Recent Posts</h3>

      {/* Posts list placeholder */}
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-gray-300 rounded-full"></div>
              </div>
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="font-medium text-gray-900">User {i}</span>
                  <span className="text-xs text-gray-500">in Thread Name</span>
                  <span className="text-xs text-gray-500">•</span>
                  <span className="text-xs text-gray-500">3 hours ago</span>
                </div>
                <p className="text-gray-700 mb-3">
                  This is a sample post content that shows how posts appear in the community feed...
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

  const renderActivity = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Community Activity</h3>

      <div className="space-y-3">
        {[
          { type: 'join', text: '3 new members joined today', icon: UserGroupIcon, color: 'text-green-600' },
          { type: 'post', text: '15 new posts in the last 24 hours', icon: DocumentTextIcon, color: 'text-blue-600' },
          { type: 'thread', text: '2 new threads started this week', icon: QueueListIcon, color: 'text-purple-600' },
          { type: 'comment', text: '45 comments posted today', icon: ChatBubbleLeftRightIcon, color: 'text-orange-600' }
        ].map((activity, index) => {
          const IconComponent = activity.icon;
          return (
            <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              <IconComponent className={`h-5 w-5 ${activity.color}`} />
              <span className="text-sm text-gray-700">{activity.text}</span>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'threads':
        return renderThreads();
      case 'posts':
        return renderRecentPosts();
      case 'activity':
        return renderActivity();
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
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
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
        {/* Quick actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button className="w-full text-left p-3 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 transition-colors">
              Create New Thread
            </button>
            <button className="w-full text-left p-3 rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-700 transition-colors">
              Browse All Threads
            </button>
            <button className="w-full text-left p-3 rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-700 transition-colors">
              View My Posts
            </button>
          </div>
        </div>

        {/* Member privileges */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Privileges</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-green-600 rounded-full mt-2 mr-2"></span>
              Create discussion threads
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-green-600 rounded-full mt-2 mr-2"></span>
              Post in existing threads
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-green-600 rounded-full mt-2 mr-2"></span>
              Comment and engage
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-1.5 h-1.5 bg-green-600 rounded-full mt-2 mr-2"></span>
              Vote on best comments
            </li>
          </ul>
        </div>

        {/* Leave community */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Membership</h3>
          <p className="text-sm text-gray-600 mb-4">
            You're currently a member of this community.
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

export default MemberView;
