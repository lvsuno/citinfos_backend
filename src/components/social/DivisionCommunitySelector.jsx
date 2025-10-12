import React, { useState, useEffect } from 'react';
import {
  MapPinIcon,
  UserGroupIcon,
  ChevronRightIcon,
  GlobeAltIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { socialAPI } from '../../services/social-api';
import { useAuth } from '../../contexts/AuthContext';

/**
 * DivisionCommunitySelector - Browse and select communities by division
 *
 * Features:
 * - Filter communities by division
 * - Show all communities or filter by user's division
 * - Display community cards with metadata
 * - Handle null divisions gracefully
 */
const DivisionCommunitySelector = ({ onCommunitySelect, selectedCommunityId }) => {
  const { user } = useAuth();
  const [communities, setCommunities] = useState([]);
  const [divisions, setDivisions] = useState([]);
  const [selectedDivisionId, setSelectedDivisionId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch divisions on mount
  useEffect(() => {
    fetchDivisions();
  }, []);

  // Fetch communities when division changes
  useEffect(() => {
    fetchCommunities();
  }, [selectedDivisionId]);

  const fetchDivisions = async () => {
    try {
      // Fetch divisions from the auth/geolocation API
      const response = await socialAPI.get('/auth/divisions/');
      setDivisions(response.results || response || []);
    } catch (err) {
      console.error('Failed to fetch divisions:', err);
      // Continue without divisions - communities can still be browsed
    }
  };

  const fetchCommunities = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await socialAPI.communities.list(selectedDivisionId);
      setCommunities(response || []);
    } catch (err) {
      console.error('Failed to fetch communities:', err);
      setError('Impossible de charger les communautés');
    } finally {
      setLoading(false);
    }
  };

  const handleCommunityClick = (community) => {
    if (onCommunitySelect) {
      onCommunitySelect(community);
    }
  };

  const handleDivisionChange = (divisionId) => {
    setSelectedDivisionId(divisionId);
    setSearchTerm(''); // Clear search when changing division
  };

  // Filter communities by search term
  const filteredCommunities = communities.filter(community =>
    community.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    community.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get user's division
  const userDivisionId = user?.profile?.division?.id;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      {/* Header */}
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Communautés
        </h2>

        {/* Division Filter Tabs */}
        <div className="flex gap-2 mb-3">
          <button
            onClick={() => handleDivisionChange(null)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedDivisionId === null
                ? 'bg-blue-100 text-blue-700 border-2 border-blue-300'
                : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
            }`}
          >
            <GlobeAltIcon className="w-4 h-4" />
            Toutes
          </button>

          {userDivisionId && (
            <button
              onClick={() => handleDivisionChange(userDivisionId)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedDivisionId === userDivisionId
                  ? 'bg-green-100 text-green-700 border-2 border-green-300'
                  : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
              }`}
            >
              <MapPinIcon className="w-4 h-4" />
              Ma division
            </button>
          )}
        </div>

        {/* Search Bar */}
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher une communauté..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-gray-50 rounded-lg p-4 animate-pulse">
              <div className="h-5 bg-gray-300 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-300 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm mb-2">{error}</p>
          <button
            onClick={fetchCommunities}
            className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
          >
            Réessayer
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filteredCommunities.length === 0 && (
        <div className="text-center py-8">
          <UserGroupIcon className="w-12 h-12 mx-auto text-gray-400 mb-2" />
          <p className="text-gray-600 text-sm">
            {searchTerm
              ? 'Aucune communauté ne correspond à votre recherche'
              : 'Aucune communauté disponible'}
          </p>
        </div>
      )}

      {/* Communities List */}
      {!loading && !error && filteredCommunities.length > 0 && (
        <div className="space-y-2 max-h-[600px] overflow-y-auto">
          {filteredCommunities.map((community) => (
            <div
              key={community.id}
              onClick={() => handleCommunityClick(community)}
              className={`rounded-lg p-4 cursor-pointer transition-all group ${
                selectedCommunityId === community.id
                  ? 'bg-blue-50 border-2 border-blue-300 shadow-md'
                  : 'bg-gray-50 border-2 border-transparent hover:border-blue-200 hover:shadow-md'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Community Name */}
                  <div className="flex items-center gap-2 mb-1">
                    <UserGroupIcon className="w-5 h-5 text-blue-600 flex-shrink-0" />
                    <h3 className={`font-semibold ${
                      selectedCommunityId === community.id
                        ? 'text-blue-700'
                        : 'text-gray-900 group-hover:text-blue-600'
                    }`}>
                      {community.name}
                    </h3>
                  </div>

                  {/* Community Description */}
                  {community.description && (
                    <p className="text-gray-600 text-sm line-clamp-2 mb-2 ml-7">
                      {community.description}
                    </p>
                  )}

                  {/* Metadata */}
                  <div className="flex items-center gap-4 text-xs text-gray-500 ml-7">
                    {/* Division */}
                    {community.division_info && (
                      <div className="flex items-center gap-1">
                        <MapPinIcon className="w-3.5 h-3.5" />
                        <span>{community.division_info.name}</span>
                      </div>
                    )}

                    {/* Member Count */}
                    {community.members_count !== undefined && (
                      <div className="flex items-center gap-1">
                        <UserGroupIcon className="w-3.5 h-3.5" />
                        <span>
                          {community.members_count} {community.members_count === 1 ? 'membre' : 'membres'}
                        </span>
                      </div>
                    )}

                    {/* Post Count */}
                    {community.posts_count !== undefined && (
                      <div className="flex items-center gap-1">
                        <span>📝</span>
                        <span>
                          {community.posts_count} {community.posts_count === 1 ? 'post' : 'posts'}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Public Access Badge */}
                  {community.public_access && (
                    <div className="mt-2 ml-7">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                        🌐 Public
                      </span>
                    </div>
                  )}
                </div>

                {/* Arrow Icon */}
                <ChevronRightIcon className={`w-5 h-5 flex-shrink-0 transition-colors ${
                  selectedCommunityId === community.id
                    ? 'text-blue-600'
                    : 'text-gray-400 group-hover:text-blue-600'
                }`} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Results Count */}
      {!loading && !error && filteredCommunities.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500 text-center">
          {filteredCommunities.length} {filteredCommunities.length === 1 ? 'communauté' : 'communautés'}
          {searchTerm && ` trouvée(s) pour "${searchTerm}"`}
        </div>
      )}
    </div>
  );
};

export default DivisionCommunitySelector;
