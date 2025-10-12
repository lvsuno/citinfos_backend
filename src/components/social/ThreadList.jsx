import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChatBubbleLeftRightIcon,
  ClockIcon,
  UserIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { socialAPI } from '../../services/social-api';

/**
 * ThreadList - Component for displaying threads in a community
 *
 * Features:
 * - Lists all threads in a community
 * - Shows thread title, post count, creator, last activity
 * - Click to navigate to thread view
 * - Loading and error states
 */
const ThreadList = ({ communityId, onThreadSelect }) => {
  const navigate = useNavigate();
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (communityId) {
      fetchThreads();
    }
  }, [communityId]);

  const fetchThreads = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await socialAPI.threads.list(communityId);
      setThreads(response.results || response);
    } catch (err) {
      console.error('Failed to fetch threads:', err);
      setError('Impossible de charger les sujets');
    } finally {
      setLoading(false);
    }
  };

  const handleThreadClick = (thread) => {
    if (onThreadSelect) {
      onThreadSelect(thread);
    } else {
      // Default navigation (can be customized based on routing structure)
      navigate(`/community/${communityId}/thread/${thread.id}`);
    }
  };

  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 animate-pulse">
            <div className="h-5 bg-gray-300 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-300 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700 text-sm">{error}</p>
        <button
          onClick={fetchThreads}
          className="mt-2 px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
        >
          Réessayer
        </button>
      </div>
    );
  }

  if (threads.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto text-gray-400 mb-2" />
        <h3 className="text-gray-700 font-medium mb-1">Aucun sujet</h3>
        <p className="text-gray-500 text-sm">
          Aucun sujet de discussion n'a été créé dans cette communauté.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {threads.map((thread) => (
        <div
          key={thread.id}
          onClick={() => handleThreadClick(thread)}
          className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {/* Thread Title */}
              <div className="flex items-start gap-2 mb-2">
                <ChatBubbleLeftRightIcon className="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" />
                <h3 className="text-gray-900 font-semibold group-hover:text-blue-600 transition-colors">
                  {thread.title}
                </h3>
              </div>

              {/* Thread Body Preview */}
              {thread.body && (
                <p className="text-gray-600 text-sm line-clamp-2 mb-3 ml-7">
                  {thread.body}
                </p>
              )}

              {/* Thread Metadata */}
              <div className="flex items-center gap-4 text-xs text-gray-500 ml-7">
                {/* Post Count */}
                <div className="flex items-center gap-1">
                  <ChatBubbleLeftRightIcon className="w-4 h-4" />
                  <span>{thread.posts_count || 0} {(thread.posts_count || 0) === 1 ? 'post' : 'posts'}</span>
                </div>

                {/* Creator */}
                {thread.creator && (
                  <div className="flex items-center gap-1">
                    <UserIcon className="w-4 h-4" />
                    <span>
                      par {thread.creator.display_name || thread.creator.username}
                    </span>
                  </div>
                )}

                {/* Last Activity */}
                {thread.updated_at && (
                  <div className="flex items-center gap-1">
                    <ClockIcon className="w-4 h-4" />
                    <span>
                      {formatDistanceToNow(new Date(thread.updated_at), {
                        addSuffix: true,
                        locale: fr
                      })}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Arrow Icon */}
            <ChevronRightIcon className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors flex-shrink-0" />
          </div>

          {/* Thread Stats Bar (Optional - can show engagement metrics) */}
          {thread.view_count > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>{thread.view_count} vues</span>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default ThreadList;
