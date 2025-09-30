import React from 'react';
import {
  EyeIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  LockClosedIcon
} from '@heroicons/react/24/outline';

/**
 * NonMemberView - View for users who are not members of the community
 * Shows limited information and encourages joining for public communities
 */
const NonMemberView = ({ community, onJoin }) => {
  const { community_type, rules } = community;

  if (community_type === 'private') {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
            <LockClosedIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Private Community</h3>
            <p className="text-gray-600 mb-6">
              This is a private community. You need an invitation to join and view its content.
            </p>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mr-2 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-800">
                  <p className="font-medium">Invitation Required</p>
                  <p className="mt-1">
                    Contact a community member or administrator to request access.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">About Privacy</h3>
            <p className="text-sm text-gray-600">
              Private communities protect member privacy and maintain exclusive content.
              Only invited members can view posts, participate in discussions, and access community resources.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2 space-y-6">
        {/* Preview content for public communities */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Community Preview</h2>
            <div className="flex items-center space-x-2">
              <EyeIcon className="h-4 w-4 text-gray-400" />
              <span className="text-xs text-gray-500 font-medium bg-gray-100 px-2 py-1 rounded">READ ONLY</span>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex">
              <InformationCircleIcon className="h-5 w-5 text-blue-400 mr-2 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-medium">Read-Only Access</p>
                <p className="mt-1">
                  You can view public content but cannot post, comment, or vote. Join to participate!
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-md font-medium text-gray-900">What you can do as a member:</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <span className="flex-shrink-0 w-1.5 h-1.5 bg-blue-600 rounded-full mt-2 mr-2"></span>
                Create posts and start discussion threads
              </li>
              <li className="flex items-start">
                <span className="flex-shrink-0 w-1.5 h-1.5 bg-blue-600 rounded-full mt-2 mr-2"></span>
                Comment on posts and reply to other members
              </li>
              <li className="flex items-start">
                <span className="flex-shrink-0 w-1.5 h-1.5 bg-blue-600 rounded-full mt-2 mr-2"></span>
                Vote on posts and comments to show appreciation
              </li>
              <li className="flex items-start">
                <span className="flex-shrink-0 w-1.5 h-1.5 bg-blue-600 rounded-full mt-2 mr-2"></span>
                Report inappropriate content to moderators
              </li>
              <li className="flex items-start">
                <span className="flex-shrink-0 w-1.5 h-1.5 bg-red-500 rounded-full mt-2 mr-2"></span>
                <span className="text-red-600">Currently: Read-only access - viewing content only</span>
              </li>
            </ul>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={onJoin}
              className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Join Community Now
            </button>
          </div>
        </div>

        {/* Read-only content area placeholder */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Community Posts</h3>
            <span className="text-xs text-orange-600 font-medium bg-orange-100 px-2 py-1 rounded">
              VIEW ONLY
            </span>
          </div>

          <div className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center">
            <EyeIcon className="h-8 w-8 text-gray-400 mx-auto mb-3" />
            <h4 className="text-sm font-medium text-gray-900 mb-1">Public Content Preview</h4>
            <p className="text-xs text-gray-500 mb-3">
              Community posts and threads will appear here in read-only mode
            </p>
            <p className="text-xs text-red-600 font-medium">
              ⚠️ Cannot post, comment, or vote without membership
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* About Privacy section for private communities */}
        {community_type === 'private' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">About Privacy</h3>
            <p className="text-sm text-gray-600">
              Private communities protect member privacy and maintain exclusive content.
              Only invited members can view posts, participate in discussions, and access community resources.
            </p>
          </div>
        )}

        {/* Call to action for public and restricted communities */}
        {community_type !== 'private' && (
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg shadow-sm p-6 text-white">
            <h3 className="text-lg font-semibold mb-2">Ready to join?</h3>
            <p className="text-blue-100 text-sm mb-4">
              Become part of this community and start engaging with like-minded members.
            </p>
            <button
              onClick={onJoin}
              className="w-full bg-white text-blue-600 px-4 py-2 rounded-lg font-medium hover:bg-blue-50 transition-colors"
            >
              {community_type === 'restricted' ? 'Request to Join' : 'Join Now'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default NonMemberView;
