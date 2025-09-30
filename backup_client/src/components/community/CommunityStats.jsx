import React from 'react';
import { UserGroupIcon, DocumentTextIcon, QueueListIcon, CalendarIcon } from '@heroicons/react/24/outline';

/**
 * CommunityStats - Displays community statistics and basic information
 * Shows member count, posts, threads, creation date, etc.
 */
const CommunityStats = ({ community }) => {
  const {
    membership_count,
    posts_count,
    threads_count,
    community_type,
    created_at
  } = community;

  const formatCount = (count) => {
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M`;
    } else if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    }
    return count?.toString() || '0';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const stats = [
    {
      label: 'Members',
      value: formatCount(membership_count),
      icon: UserGroupIcon,
      color: 'text-blue-600 bg-blue-50'
    },
    {
      label: 'Posts',
      value: formatCount(posts_count),
      icon: DocumentTextIcon,
      color: 'text-green-600 bg-green-50'
    },
    {
      label: 'Threads',
      value: formatCount(threads_count),
      icon: QueueListIcon,
      color: 'text-purple-600 bg-purple-50'
    },
    {
      label: 'Created',
      value: formatDate(created_at),
      icon: CalendarIcon,
      color: 'text-gray-600 bg-gray-50'
    }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Community Overview</h2>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {stats.map((stat, index) => {
          const IconComponent = stat.icon;
          return (
            <div key={index} className="bg-gray-50 rounded-lg p-4 border border-gray-100">
              <div className="flex items-center justify-between mb-2">
                <div className={`p-2 rounded-lg ${stat.color}`}>
                  <IconComponent className="h-5 w-5" />
                </div>
              </div>
              <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">
                {stat.label}
              </p>
              <p className="mt-1 text-xl font-bold text-gray-900">
                {stat.value}
              </p>
            </div>
          );
        })}
      </div>

      {/* Community type badge */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">Community Type:</span>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            community_type === 'public'
              ? 'bg-green-100 text-green-800'
              : community_type === 'private'
              ? 'bg-red-100 text-red-800'
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            {community_type.charAt(0).toUpperCase() + community_type.slice(1)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default CommunityStats;
