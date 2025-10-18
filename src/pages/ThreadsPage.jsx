import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  ChatBubbleLeftRightIcon,
  ClockIcon,
  UserIcon,
  ChevronRightIcon,
  ArrowLeftIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { socialAPI } from '../services/social-api';
import Layout from '../components/Layout';
import geolocationService from '../services/geolocationService';
import { getCountryISO3ByUrlPath } from '../config/adminDivisions';

/**
 * ThreadsPage - Full page view of all threads in a community with infinite scroll
 *
 * Features:
 * - Infinite scroll pagination
 * - Shows all threads in a community
 * - Create new thread button
 * - Back navigation
 * - Loading states
 * - Dynamic URL support (municipality/commune/city/:municipalitySlug/threads)
 */
const ThreadsPage = () => {
  const { municipalitySlug } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [threads, setThreads] = useState([]);
  const [division, setDivision] = useState(null);
  const [community, setCommunity] = useState(null);
  const [loading, setLoading] = useState(true);  // Start with true to show loading initially
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Get current URL path (municipality, commune, etc.)
  const currentUrlPath = location.pathname.split('/')[1];

  // Intersection observer ref for infinite scroll
  const observerTarget = useRef(null);

  // Fetch division data from URL slug
  useEffect(() => {
    const loadDivision = async () => {
      if (!municipalitySlug || !currentUrlPath) {
        setLoading(false);
        return;
      }

      const countryISO3 = getCountryISO3ByUrlPath(currentUrlPath);
      if (!countryISO3) {
        navigate('/', { replace: true });
        return;
      }

      try {
        setLoading(true);
        const result = await geolocationService.getDivisionBySlug(
          municipalitySlug,
          countryISO3
        );

        if (result.success && result.division) {
          const divisionData = {
            ...result.division,
            slug: municipalitySlug,
            country: countryISO3
          };
          setDivision(divisionData);

          // Use the community_id from division data
          if (divisionData.community_id) {
            setCommunity({
              id: divisionData.community_id,
              name: divisionData.name,
              slug: divisionData.community_slug || municipalitySlug
            });
          } else {
            console.error('No community_id found for division:', divisionData);
            setError('Communauté introuvable pour cette division');
          }
        } else {
          navigate('/', { replace: true });
        }
      } catch (error) {
        console.error('Error loading division:', error);
        navigate('/', { replace: true });
      }
      // Note: Don't set loading to false here - let fetchThreads() handle it
      // so we don't get a flash of empty state between loading division and loading threads
    };

    loadDivision();
  }, [municipalitySlug, currentUrlPath, navigate]);

  // Fetch threads when community is loaded
  useEffect(() => {
    if (community?.id) {
      fetchThreads(1, true);
    }
  }, [community?.id]);

  // Infinite scroll observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading && !loadingMore) {
          loadMoreThreads();
        }
      },
      { threshold: 0.1 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => {
      if (observerTarget.current) {
        observer.unobserve(observerTarget.current);
      }
    };
  }, [hasMore, loading, loadingMore, page]);

  const fetchThreads = async (pageNum = 1, reset = false) => {
    if (!community?.id) return;

    try {
      if (pageNum === 1) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }

      setError(null);

      const response = await socialAPI.threads.list(community.id);
      const allThreads = response.results || response;

      // Simulate pagination (API might return all at once)
      const pageSize = 20;
      const startIdx = (pageNum - 1) * pageSize;
      const endIdx = startIdx + pageSize;
      const pageThreads = allThreads.slice(startIdx, endIdx);

      if (reset) {
        setThreads(pageThreads);
      } else {
        setThreads(prev => [...prev, ...pageThreads]);
      }

      // Check if there are more threads
      setHasMore(endIdx < allThreads.length);
    } catch (err) {
      console.error('Error fetching threads:', err);
      setError(err.message || 'Erreur lors du chargement des sujets');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const loadMoreThreads = useCallback(() => {
    if (!loadingMore && hasMore) {
      const nextPage = page + 1;
      setPage(nextPage);
      fetchThreads(nextPage, false);
    }
  }, [page, loadingMore, hasMore]);

  const handleThreadClick = (thread) => {
    // Use the same dynamic URL pattern with slug
    navigate(`/${currentUrlPath}/${municipalitySlug}/thread/${thread.slug || thread.id}`);
  };

  const handleBack = () => {
    navigate(-1);
  };

  if (loading && threads.length === 0) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto p-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-8 bg-gray-200 rounded w-1/3"></div>
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="border-b border-gray-200 pb-4">
                  <div className="h-5 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-gray-100 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (error && threads.length === 0) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-800 mb-4">{error}</p>
            <button
              onClick={() => fetchThreads(1, true)}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Réessayer
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeftIcon className="w-5 h-5" />
            Retour
          </button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <ChatBubbleLeftRightIcon className="w-8 h-8 text-purple-600" />
                Sujets de discussion
              </h1>
              {community && (
                <p className="text-gray-600 mt-2">
                  {community.name} • {threads.length} sujet{threads.length !== 1 ? 's' : ''}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Threads List */}
        {threads.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <ChatBubbleLeftRightIcon className="w-16 h-16 mx-auto text-gray-400 mb-3" />
            <h3 className="text-lg font-medium text-gray-700 mb-2">Aucun sujet</h3>
            <p className="text-gray-500">
              Aucun sujet de discussion n'a été créé dans cette communauté.
            </p>
            <p className="text-sm text-gray-400 mt-2">
              Les sujets peuvent être créés depuis les différentes rubriques.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            {threads.map((thread, index) => (
              <div
                key={thread.id}
                onClick={() => handleThreadClick(thread)}
                className={`cursor-pointer hover:bg-gray-50 transition-colors p-6 ${
                  index !== threads.length - 1 ? 'border-b border-gray-200' : ''
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-gray-900 hover:text-purple-600 transition-colors mb-2">
                      {thread.title}
                    </h3>

                    {thread.body && (
                      <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                        {thread.body}
                      </p>
                    )}

                    <div className="flex items-center gap-4 text-sm text-gray-500 flex-wrap">
                      {/* Rubrique/Section */}
                      {thread.section_name && (
                        <span className="flex items-center gap-1.5 px-2 py-1 bg-purple-50 text-purple-700 rounded-md">
                          <TagIcon className="w-4 h-4" />
                          {thread.section_name}
                        </span>
                      )}

                      <span className="flex items-center gap-1.5">
                        <ChatBubbleLeftRightIcon className="w-4 h-4" />
                        {thread.posts_count || 0} {(thread.posts_count || 0) !== 1 ? 'réponses' : 'réponse'}
                      </span>

                      {thread.creator && (
                        <span className="flex items-center gap-1.5">
                          <UserIcon className="w-4 h-4" />
                          {thread.creator_name || thread.creator.username}
                        </span>
                      )}

                      <span className="flex items-center gap-1.5">
                        <ClockIcon className="w-4 h-4" />
                        {formatDistanceToNow(new Date(thread.updated_at || thread.created_at), {
                          addSuffix: true,
                          locale: fr
                        })}
                      </span>
                    </div>
                  </div>

                  <ChevronRightIcon className="w-5 h-5 text-gray-400 flex-shrink-0 mt-1" />
                </div>
              </div>
            ))}

            {/* Infinite scroll loading indicator */}
            {loadingMore && (
              <div className="p-6 text-center border-t border-gray-200">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                <p className="text-gray-500 text-sm mt-2">Chargement...</p>
              </div>
            )}

            {/* Intersection observer target */}
            {hasMore && !loadingMore && (
              <div ref={observerTarget} className="h-20"></div>
            )}

            {/* End of list message */}
            {!hasMore && threads.length > 0 && (
              <div className="p-6 text-center border-t border-gray-200">
                <p className="text-gray-500 text-sm">
                  Vous avez vu tous les sujets
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default ThreadsPage;
