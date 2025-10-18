import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  ChatBubbleLeftRightIcon,
  ClockIcon,
  ChevronRightIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { socialAPI } from '../../services/social-api';

/**
 * ThreadListCompact - Compact version of ThreadList for displaying on Accueil page
 * Shows only the 5 most recent or popular threads
 *
 * Features:
 * - Shows up to 5 threads
 * - Compact display with title, post count, and timestamp
 * - "Voir tous les sujets" link to view full thread list
 * - Loading and error states
 * - Dynamic URL support (municipality/commune/city/:municipalitySlug/thread/:threadId)
 * - Public access (no authentication required)
 */
const ThreadListCompact = ({ communityId, municipalitySlug, limit = 5 }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get current URL path (municipality, commune, etc.)
  const currentUrlPath = location.pathname.split('/')[1];

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
      const allThreads = response.results || response;

      // Take only the first 'limit' threads (most recent)
      setThreads(allThreads.slice(0, limit));
    } catch (err) {
      console.error('Error fetching threads:', err);
      setError(err.message || 'Erreur lors du chargement des sujets');
    } finally {
      setLoading(false);
    }
  };

  const handleThreadClick = (thread) => {
    if (municipalitySlug && currentUrlPath) {
      navigate(`/${currentUrlPath}/${municipalitySlug}/thread/${thread.slug || thread.id}`);
    }
  };

  const handleViewAll = () => {
    if (municipalitySlug && currentUrlPath) {
      navigate(`/${currentUrlPath}/${municipalitySlug}/threads`);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <ChatBubbleLeftRightIcon className="w-5 h-5 text-purple-600" />
          Sujets de discussion
        </h3>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-100 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return null; // Silently hide on error for Accueil page
  }

  if (threads.length === 0) {
    // Show empty state when no threads exist
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <ChatBubbleLeftRightIcon className="w-5 h-5 text-purple-600" />
          Sujets de discussion
        </h3>
        <div className="text-center py-6">
          <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto text-gray-300 mb-3" />
          <p className="text-sm text-gray-500 mb-4">
            Aucun sujet de discussion pour le moment
          </p>
          <button
            onClick={handleViewAll}
            className="text-sm text-purple-600 hover:text-purple-700 font-medium"
          >
            Voir la page des sujets →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        <ChatBubbleLeftRightIcon className="w-5 h-5 text-purple-600" />
        Sujets de discussion
      </h3>

      <div className="space-y-3">
        {threads.map((thread) => (
          <div
            key={thread.id}
            onClick={() => handleThreadClick(thread)}
            className="cursor-pointer group"
          >
            <div className="flex items-start justify-between gap-3 hover:bg-gray-50 p-2 rounded-lg transition-colors">
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-gray-900 group-hover:text-purple-600 transition-colors line-clamp-1">
                  {thread.title}
                </h4>
                <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <ChatBubbleLeftRightIcon className="w-3.5 h-3.5" />
                    {thread.posts_count || 0}
                  </span>
                  <span className="flex items-center gap-1">
                    <ClockIcon className="w-3.5 h-3.5" />
                    {formatDistanceToNow(new Date(thread.updated_at || thread.created_at), {
                      addSuffix: true,
                      locale: fr
                    })}
                  </span>
                </div>
              </div>
              <ChevronRightIcon className="w-4 h-4 text-gray-400 group-hover:text-purple-600 flex-shrink-0 mt-1" />
            </div>
          </div>
        ))}
      </div>

      {/* View All Link */}
      <button
        onClick={handleViewAll}
        className="mt-3 w-full text-center text-sm text-purple-600 hover:text-purple-700 font-medium py-2 hover:bg-purple-50 rounded-lg transition-colors"
      >
        Voir tous les sujets →
      </button>
    </div>
  );
};

export default ThreadListCompact;
