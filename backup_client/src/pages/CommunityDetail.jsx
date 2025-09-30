import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { EyeIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import { useJWTAuth } from '../hooks/useJWTAuth';
import communitiesAPI from '../services/communitiesAPI';

// Role-based view components
import NonMemberView from '../components/community/NonMemberView';
import MemberView from '../components/community/MemberView';
import ModeratorView from '../components/community/ModeratorView';
import AdminView from '../components/community/AdminView';
import CreatorView from '../components/community/CreatorView';

// Shared components
import CommunityHeader from '../components/community/CommunityHeader';
import CommunityStats from '../components/community/CommunityStats';
import CommunityRules from '../components/community/CommunityRules';
import CommunitySettings from '../components/community/CommunitySettings';
import GeoRestricted from '../components/community/GeoRestricted';

const CommunityDetail = () => {
  const { slug } = useParams(); // Extract slug from URL parameter
  const navigate = useNavigate();
  const { user } = useJWTAuth();
  const [community, setCommunity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [geoRestrictionError, setGeoRestrictionError] = useState(null);
  const [viewMode, setViewMode] = useState('member'); // 'member' or 'role-specific'

  useEffect(() => {
    const fetchCommunity = async () => {
      try {
        setLoading(true);
        setError(null);
        setGeoRestrictionError(null);
        console.log('🔍 Fetching community with slug:', slug);
        const data = await communitiesAPI.getCommunityBySlug(slug);
        setCommunity(data);
      } catch (err) {
        console.error('Error fetching community:', err);

        // Check if this is a geo-restriction error
        if (err.response && err.response.status === 403 &&
            err.response.data && err.response.data.error === 'geo_restricted') {
          setGeoRestrictionError(err.response.data);
        } else {
          setError('Failed to load community');
        }
      } finally {
        setLoading(false);
      }
    };

    if (slug) {
      fetchCommunity();
    }
  }, [slug]); // Update dependency to use 'slug'

  const handleJoinCommunity = async () => {
    try {
      await communitiesAPI.joinCommunity(community.id); // Use community.id for API calls
      // Refresh community data to update membership status
      const updatedData = await communitiesAPI.getCommunityBySlug(slug);
      setCommunity(updatedData);
    } catch (err) {
      console.error('Error joining community:', err);
    }
  };

  const handleLeaveCommunity = async () => {
    try {
      await communitiesAPI.leaveCommunity(community.id); // Use community.id for API calls
      // Refresh community data to update membership status
      const updatedData = await communitiesAPI.getCommunityBySlug(slug);
      setCommunity(updatedData);
    } catch (err) {
      console.error('Error leaving community:', err);
    }
  };

  const handleBrowseCommunities = () => {
    navigate('/communities');
  };

  const handleUpdateLocation = () => {
    navigate('/profile/settings');
  };

  const renderViewToggle = () => {
    if (!community?.user_is_member) return null;

    const { user_role } = community;
    const canToggle = ['moderator', 'admin', 'creator'].includes(user_role);

    if (!canToggle) return null;

    const getRoleLabel = () => {
      switch (user_role) {
        case 'creator': return 'Creator';
        case 'admin': return 'Admin';
        case 'moderator': return 'Moderator';
        default: return 'Role';
      }
    };

    const getRoleColor = () => {
      switch (user_role) {
        case 'creator': return 'orange';
        case 'admin': return 'red';
        case 'moderator': return 'purple';
        default: return 'blue';
      }
    };

    const color = getRoleColor();

    return (
      <div className="flex items-center justify-center mb-6">
        <div className="bg-white border border-gray-200 rounded-lg p-1 flex items-center space-x-1">
          <button
            onClick={() => setViewMode('member')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
              viewMode === 'member'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <EyeIcon className="h-4 w-4" />
            <span>Member View</span>
          </button>
          <button
            onClick={() => setViewMode('role-specific')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
              viewMode === 'role-specific'
                ? `bg-${color}-600 text-white`
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
            style={viewMode === 'role-specific' ? {
              backgroundColor: color === 'orange' ? '#ea580c' :
                              color === 'red' ? '#dc2626' :
                              color === 'purple' ? '#9333ea' : '#2563eb',
              color: 'white'
            } : {}}
          >
            <ShieldCheckIcon className="h-4 w-4" />
            <span>{getRoleLabel()} View</span>
          </button>
        </div>
      </div>
    );
  };

  const renderRoleBasedView = () => {
    if (!community) return null;

    const { user_is_member, user_role } = community;

    // Non-member view (for public communities)
    if (!user_is_member) {
      return (
        <NonMemberView
          community={community}
          onJoin={handleJoinCommunity}
        />
      );
    }

    // If user is moderator/admin/creator and has toggle set to member view, show member view
    const canToggle = ['moderator', 'admin', 'creator'].includes(user_role);
    if (canToggle && viewMode === 'member') {
      return (
        <MemberView
          community={community}
          onLeave={handleLeaveCommunity}
        />
      );
    }

    // Role-specific views (original logic)
    switch (user_role) {
      case 'creator':
        return (
          <CreatorView
            community={community}
            onLeave={handleLeaveCommunity}
          />
        );
      case 'admin':
        return (
          <AdminView
            community={community}
            onLeave={handleLeaveCommunity}
          />
        );
      case 'moderator':
        return (
          <ModeratorView
            community={community}
            onLeave={handleLeaveCommunity}
          />
        );
      case 'member':
      default:
        return (
          <MemberView
            community={community}
            onLeave={handleLeaveCommunity}
          />
        );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (geoRestrictionError) {
    return (
      <GeoRestricted
        error={geoRestrictionError}
        onBrowseCommunities={handleBrowseCommunities}
        onUpdateLocation={handleUpdateLocation}
      />
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error</h3>
        <p className="text-gray-600">{error}</p>
      </div>
    );
  }

  if (!community) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Community not found</h3>
        <p className="text-gray-600">The community you're looking for doesn't exist.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Shared header component */}
      <CommunityHeader
        community={community}
        onJoin={handleJoinCommunity}
        onLeave={handleLeaveCommunity}
      />

      {/* Stats and Rules layout - side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Community Stats - reduced width */}
        <div className="lg:col-span-2">
          <CommunityStats community={community} />
        </div>

        {/* Community Rules - collapsible, starts collapsed for better UX */}
        <div className="lg:col-span-1">
          <CommunityRules
            rules={community.rules}
            community={community}
            collapsible={true}
            defaultCollapsed={true}
          />
        </div>
      </div>

      {/* View toggle for moderators/admins/creators */}
      {renderViewToggle()}

      {/* Role-based content */}
      {renderRoleBasedView()}
    </div>
  );
};

export default CommunityDetail;
