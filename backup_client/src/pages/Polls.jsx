import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Link } from 'react-router-dom';
import { PlusIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import PollCard from '../components/PollCard';
import { pollsAPI } from '../services/pollsAPI';

const Polls = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');
  const queryClient = useQueryClient();

  const { data: polls, isLoading } = useQuery(
    ['polls', searchTerm, filter],
    () => pollsAPI.getPolls({
      search: searchTerm,
      status: filter === 'active' ? 'active' : filter === 'expired' ? 'expired' : undefined
    })
  );

  const voteMutation = useMutation(
    ({ pollId, optionIds }) => pollsAPI.votePoll(pollId, optionIds),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['polls']);
      },
      onError: (error) => {
        console.error('Error voting on poll:', error);
      }
    }
  );

  const handleVote = async (pollId, optionIds) => {
    try {
      await voteMutation.mutateAsync({ pollId, optionIds });
    } catch (error) {
      console.error('Failed to vote on poll:', error);
    }
  };

  const filteredPolls = (polls || []).filter(p => {
    if (filter === 'active') return !p.is_expired;
    if (filter === 'expired') return p.is_expired;
    return true;
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
          <h1 className="text-2xl font-bold text-gray-900">Polls</h1>
          <p className="text-gray-600">Discover and participate in community polls</p>
        </div>
        <Link
          to="/polls/create"
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Poll
        </Link>
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
              placeholder="Search polls..."
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
              <option value="all">All Polls</option>
              <option value="active">Active Polls</option>
              <option value="expired">Expired Polls</option>
            </select>
          </div>
        </div>
      </div>

      {/* Polls List */}
      <div className="space-y-4">
        {filteredPolls.map(poll => (
          <PollCard key={poll.id} poll={poll} onVote={handleVote} />
        ))}
      </div>

      {filteredPolls.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <MagnifyingGlassIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">{searchTerm ? 'No polls found matching your search.' : 'No polls available.'}</p>
          <Link
            to="/polls/create"
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create the first poll
          </Link>
        </div>
      )}
    </div>
  );
};

export default Polls;
