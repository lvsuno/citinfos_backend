import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Link } from 'react-router-dom';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';
import CommunityIcon from '../components/ui/CommunityIcon';
import CommunityForm from '../components/CommunityForm';
import CommunityCard from '../components/CommunityCard';
import { communitiesAPI } from '../services/communitiesAPI';

const Communities = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);

  const { data: communities, isLoading } = useQuery(
    ['communities', searchTerm, filter],
    () => communitiesAPI.getCommunities({
      search: searchTerm,
      filter: filter === 'joined' ? 'member' : filter === 'public' ? 'public' : undefined
    })
  );

  const joinMutation = useMutation(
    (communitySlug) => communitiesAPI.joinCommunity(communitySlug),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['communities']);
      },
      onError: (error) => {
        console.error('Error joining community:', error);
      }
    }
  );

  const handleJoinCommunity = async (communitySlug) => {
    try {
      await joinMutation.mutateAsync(communitySlug);
    } catch (error) {
      console.error('Failed to join community:', error);
    }
  };

  const createMutation = useMutation(
    (payload) => communitiesAPI.createCommunity(payload),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['communities']);
      },
      onError: (err) => console.error('Create community error', err)
    }
  );

  const handleCreateSubmit = async (payload) => {
    // backend may expect certain shape; let communitiesAPI handle it
    await createMutation.mutateAsync(payload);
  };

  const filteredCommunities = (communities || []).filter(c => {
    const matchesSearch = c.name.toLowerCase().includes(searchTerm.toLowerCase()) || c.description.toLowerCase().includes(searchTerm.toLowerCase());
    if (filter === 'joined') return c.user_is_member && matchesSearch;
    if (filter === 'public') return c.community_type === 'public' && matchesSearch;
    return matchesSearch;
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Communities</h1>
          <p className="text-gray-600">Join communities and connect with like-minded people</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Community
        </button>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search communities..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="sm:w-48">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Communities</option>
              <option value="joined">My Communities</option>
              <option value="public">Public Communities</option>
            </select>
          </div>
        </div>
      </div>

      {/* Communities Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCommunities.map(c => (
          <CommunityCard
            key={c.id}
            community={c}
            options={{
              variant: 'grid',
              showStats: true,
              showDescription: true,
              showTags: true,
              showActions: true,
              showMembershipBadge: true,
              clickable: false
            }}
            onJoin={handleJoinCommunity}
            isLoading={joinMutation.isLoading}
          />
        ))}
      </div>

      {filteredCommunities.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <CommunityIcon Icon={UserGroupIcon} color="gray" size="lg" className="mx-auto mb-4" />
          <p className="text-gray-500">{searchTerm ? 'No communities found matching your search.' : 'No communities available.'}</p>
          <button className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
            <PlusIcon className="h-4 w-4 mr-2" />
            Create the first community
          </button>
        </div>
      )}
      {showCreate && (
        <CommunityForm
          visible={showCreate}
          onClose={() => setShowCreate(false)}
          onSubmit={handleCreateSubmit}
          // include common fields; parent can customize
          fields={[
            'name',
            'description',
            'category',
            'community_type',
            'geo_restricted',
            'require_post_approval',
            'country',
            'city'
          ]}
        />
      )}
    </div>
  );
};

export default Communities;
