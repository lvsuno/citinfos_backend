import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  ArrowLeftIcon,
  ChatBubbleLeftRightIcon,
  UserIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { socialAPI } from '../../services/social-api';
import { useAuth } from '../../contexts/AuthContext';
import PostCard from './PostCard';
import InlinePostCreator from '../InlinePostCreator';
import Breadcrumb from '../common/Breadcrumb';
import Layout from '../Layout';
import geolocationService from '../../services/geolocationService';
import { getCountryISO3ByUrlPath } from '../../config/adminDivisions';

/**
 * ThreadDetail - Component for displaying a single thread and its posts
 *
 * Features:
 * - Shows thread title, body, creator, and metadata
 * - Lists all posts within the thread (sorted: pinned → best → votes → date)
 * - Allows creating new posts in the thread
 * - Thread creator can edit/delete thread (menu in ThreadList)
 * - Loading and error states
 * - Dynamic URL support (municipality/commune/city/:municipalitySlug/thread/:threadId)
 */
const ThreadDetail = () => {
  const { municipalitySlug, threadId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // Get current URL path (municipality, commune, etc.)
  const currentUrlPath = location.pathname.split('/')[1];

  const [thread, setThread] = useState(null);
  const [posts, setPosts] = useState([]);
  const [division, setDivision] = useState(null);
  const [community, setCommunity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [postsLoading, setPostsLoading] = useState(false);

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
            setLoading(false);
          }
        } else {
          navigate('/', { replace: true });
        }
      } catch (error) {
        console.error('Error loading division:', error);
        navigate('/', { replace: true });
      }
      // Note: Don't set loading to false here - let fetchThread() handle it
      // so we don't get a flash of error state between loading division and loading thread
    };

    loadDivision();
  }, [municipalitySlug, currentUrlPath, navigate]);

  useEffect(() => {
    if (threadId && community?.id) {
      fetchThread();
      fetchPosts();
    }
  }, [threadId, community?.id]);

  const fetchThread = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await socialAPI.threads.get(threadId);
      setThread(response);
      setLoading(false); // Clear loading after thread is set
    } catch (err) {
      console.error('Error fetching thread:', err);
      setError('Impossible de charger le sujet');
      setLoading(false); // Clear loading on error too
    }
  };

  const fetchPosts = async () => {
    try {
      setPostsLoading(true);
      console.log('Fetching posts for thread:', threadId);
      const response = await socialAPI.threads.posts(threadId);
      console.log('Posts API response:', response);

      // Handle both paginated and non-paginated responses
      const postsData = response.results || response;
      console.log('Extracted posts data:', postsData);

      // Ensure postsData is an array
      if (Array.isArray(postsData)) {
        setPosts(postsData);
        console.log(`Successfully loaded ${postsData.length} posts`);
      } else {
        console.warn('Posts data is not an array:', postsData);
        setPosts([]);
      }
    } catch (err) {
      console.error('Error fetching thread posts:', err);
      console.error('Error details:', err.response?.data || err.message);
      setPosts([]); // Set empty array on error
    } finally {
      setPostsLoading(false);
    }
  };

  const handleBack = () => {
    // Navigate back to the threads list page using dynamic URL
    if (municipalitySlug && currentUrlPath) {
      navigate(`/${currentUrlPath}/${municipalitySlug}/threads`);
    } else {
      navigate(-1);
    }
  };

  const handlePostCreated = (newPost) => {
    // Add new post to the list
    setPosts(prev => [newPost, ...prev]);

    // Update thread post count
    if (thread) {
      setThread(prev => ({
        ...prev,
        posts_count: (prev.posts_count || 0) + 1
      }));
    }
  };

  const handlePostDeleted = (postId) => {
    setPosts(prev => prev.filter(p => p.id !== postId));

    // Update thread post count
    if (thread) {
      setThread(prev => ({
        ...prev,
        posts_count: Math.max(0, (prev.posts_count || 0) - 1)
      }));
    }
  };

  const handlePostUpdated = (updatedPost) => {
    setPosts(prev => prev.map(p => p.id === updatedPost.id ? updatedPost : p));
  };

  if (loading) {
    return (
      <Layout>
        <div className="max-w-5xl mx-auto p-4">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-300 rounded w-1/4 mb-4"></div>
            <div className="h-6 bg-gray-300 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-300 rounded w-1/2 mb-6"></div>
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-300 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (error || !thread) {
    return (
      <Layout>
        <div className="max-w-5xl mx-auto p-4">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeftIcon className="h-5 w-5" />
            Retour
          </button>

          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-700 font-medium mb-2">
              {error || 'Sujet introuvable'}
            </p>
            <button
              onClick={fetchThread}
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Réessayer
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  const isThreadCreator = user?.profile?.id === thread.creator?.id;

  return (
    <Layout>
      <div className="max-w-5xl mx-auto p-4">
        {/* Breadcrumb Navigation */}
        {(division || community) && (
          <div className="mb-4">
            <Breadcrumb
              division={division}
              community={community}
              thread={thread}
            />
          </div>
        )}

      {/* Back Button */}
      <button
        onClick={handleBack}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6 transition-colors"
      >
        <ArrowLeftIcon className="h-5 w-5" />
        Retour à la communauté
      </button>

      {/* Thread Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-start gap-3 mb-4">
          <ChatBubbleLeftRightIcon className="w-8 h-8 text-purple-500 flex-shrink-0" />
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {thread.title}
            </h1>

            {thread.body && (
              <p className="text-gray-700 whitespace-pre-wrap mb-4">
                {thread.body}
              </p>
            )}

            {/* Thread Metadata */}
            <div className="flex items-center gap-4 text-sm text-gray-500">
              {thread.creator && (
                <div className="flex items-center gap-1">
                  <UserIcon className="w-4 h-4" />
                  <span>
                    {thread.creator.display_name || thread.creator.username}
                    {isThreadCreator && (
                      <span className="ml-1 text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                        Créateur
                      </span>
                    )}
                  </span>
                </div>
              )}

              {thread.created_at && (
                <div className="flex items-center gap-1">
                  <ClockIcon className="w-4 h-4" />
                  <span>
                    {formatDistanceToNow(new Date(thread.created_at), {
                      addSuffix: true,
                      locale: fr
                    })}
                  </span>
                </div>
              )}

              <div className="flex items-center gap-1">
                <ChatBubbleLeftRightIcon className="w-4 h-4" />
                <span>
                  {thread.posts_count || 0} {(thread.posts_count || 0) === 1 ? 'post' : 'posts'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Post Creator */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">
          Répondre dans ce sujet
        </h2>
        <InlinePostCreator
          division={division}
          community={community}
          threadId={threadId}
          onPostCreated={handlePostCreated}
          placeholder="Partagez votre réponse..."
          showThreadOption={false}
        />
      </div>

      {/* Posts List */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">
          {posts.length > 0 ? `${posts.length} réponse${posts.length > 1 ? 's' : ''}` : 'Aucune réponse'}
        </h2>

        {postsLoading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg p-4 shadow-sm border animate-pulse">
                <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-300 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : posts.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto text-gray-400 mb-3" />
            <p className="text-gray-600 mb-2">Aucune réponse pour le moment</p>
            <p className="text-sm text-gray-500">
              Soyez le premier à répondre à ce sujet !
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {posts.map((post) => (
              <PostCard
                key={post.id}
                post={post}
                onDelete={() => handlePostDeleted(post.id)}
                onUpdate={handlePostUpdated}
              />
            ))}
          </div>
        )}
      </div>
    </div>
    </Layout>
  );
};

export default ThreadDetail;
