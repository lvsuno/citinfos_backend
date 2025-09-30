import React from 'react';
import { PlusIcon, MinusIcon, CogIcon } from '@heroicons/react/24/outline';
import { DEFAULT_COVER_IMAGE, DEFAULT_AVATAR_IMAGE } from '../../constants/defaultImages';

/**
 * CommunityHeader - Displays community title, description, and main action buttons
 * Adapts based on user membership and role
 */
const CommunityHeader = ({ community, onJoin, onLeave }) => {
  const {
    name,
    description,
    user_is_member,
    user_role,
    community_type,
    cover_media,
    avatar
  } = community;

  // Determine if user can see media based on community type and membership
  const canViewMedia = () => {
    if (community_type === 'public') return true;
    return user_is_member;
  };

  // Default images for when access is restricted
  const getDefaultCover = () => DEFAULT_COVER_IMAGE;
  const getDefaultAvatar = () => DEFAULT_AVATAR_IMAGE;

  const displayCover = canViewMedia() && cover_media ? cover_media : getDefaultCover();
  const displayAvatar = canViewMedia() && avatar ? avatar : getDefaultAvatar();

  const renderActionButton = () => {
    // Non-member of public community can join
    if (!user_is_member && community_type === 'public') {
      return (
        <button
          onClick={onJoin}
          className="inline-flex items-center px-4 py-2 rounded-md text-white bg-blue-600 hover:bg-blue-700 text-sm font-medium shadow-sm transition-colors"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Join Community
        </button>
      );
    }

    // Member can leave (except creators might have different flow)
    if (user_is_member) {
      return (
        <div className="flex items-center space-x-3">
          {/* Settings button for admins and creators */}
          {(user_role === 'admin' || user_role === 'creator') && (
            <button className="inline-flex items-center px-4 py-2 rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 text-sm font-medium shadow-sm transition-colors">
              <CogIcon className="h-4 w-4 mr-2" />
              Settings
            </button>
          )}

          {/* Leave button (creators might need confirmation) */}
          {user_role !== 'creator' && (
            <button
              onClick={onLeave}
              className="inline-flex items-center px-4 py-2 rounded-md text-red-700 bg-red-50 hover:bg-red-100 text-sm font-medium shadow-sm transition-colors"
            >
              <MinusIcon className="h-4 w-4 mr-2" />
              Leave
            </button>
          )}
        </div>
      );
    }

    return null;
  };

  const getRoleBadge = () => {
    if (!user_is_member) return null;

    const roleConfig = {
      creator: { color: 'bg-yellow-100 text-yellow-800', label: 'Creator' },
      admin: { color: 'bg-red-100 text-red-800', label: 'Admin' },
      moderator: { color: 'bg-purple-100 text-purple-800', label: 'Moderator' },
      member: { color: 'bg-green-100 text-green-800', label: 'Member' }
    };

    const config = roleConfig[user_role] || roleConfig.member;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Cover Media */}
      <div className="relative h-48 bg-gradient-to-r from-blue-400 to-purple-500">
        <img
          src={displayCover}
          alt={`${name} cover`}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.src = getDefaultCover();
          }}
        />

        {/* Restriction overlay for non-members of private/restricted communities */}
        {!canViewMedia() && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="text-center text-white">
              <div className="text-2xl mb-2">🔒</div>
              <div className="text-sm font-medium">Join to view community media</div>
            </div>
          </div>
        )}

        {/* Privacy badge overlay */}
        <div className="absolute top-4 right-4">
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium text-white ${
            community_type === 'public' ? 'bg-green-500' :
            community_type === 'private' ? 'bg-red-500' : 'bg-yellow-500'
          }`}>
            {community_type === 'public' ? '🌐 Public' :
             community_type === 'private' ? '🔒 Private' : '🛡️ Restricted'}
          </span>
        </div>
      </div>

      {/* Content with Avatar */}
      <div className="relative p-6">
        {/* Avatar positioned over cover */}
        <div className="absolute -top-12 left-6">
          <div className="relative">
            <img
              src={displayAvatar}
              alt={`${name} avatar`}
              className="w-24 h-24 rounded-full border-4 border-white shadow-lg object-cover"
              onError={(e) => {
                e.target.src = getDefaultAvatar();
              }}
            />
            {/* Avatar restriction overlay for non-members */}
            {!canViewMedia() && (
              <div className="absolute inset-0 bg-black bg-opacity-50 rounded-full flex items-center justify-center">
                <span className="text-white text-xl">🔒</span>
              </div>
            )}
          </div>
        </div>

        {/* Community name positioned next to avatar */}
        <div className="absolute -top-1 left-36 flex items-center gap-3">
          <h1 className="text-3xl font-bold text-gray-900">{name}</h1>
          {getRoleBadge()}
        </div>

        {/* Content area with proper spacing for avatar and title */}
        <div className="pt-12">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="flex-1">
              {/* Show description for public communities or members, and for restricted communities to non-members */}
              {(community_type === 'public' || user_is_member || community_type === 'restricted') && (
                <p className="text-gray-600 text-lg leading-relaxed">{description}</p>
              )}

              {/* Private community description only for members */}
              {community_type === 'private' && !user_is_member && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600 italic">
                    🔒 Community description is only visible to members of private communities.
                  </p>
                </div>
              )}
            </div>

            <div className="flex-shrink-0">
              {renderActionButton()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommunityHeader;
