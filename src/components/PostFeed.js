import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Add as AddIcon, EditNote as EditNoteIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import contentAPI from '../services/contentAPI';
import PostCard from './social/PostCard';
import RepostCard from './social/RepostCard';
import styles from './PostFeed.module.css';

/**
 * PostFeed - Component for displaying posts from a community
 * Based on the old client's SocialFeed component
 */
const PostFeed = ({ municipalityName, municipalityId = null, communityId = null, rubrique = null, onCreatePostClick }) => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [feedItems, setFeedItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);

    // Fetch feed data
    const fetchFeed = async (pageNum = 1, replace = false) => {
        try {
            setLoading(true);
            // Use getPosts with community filtering to get ALL posts in the community
            // Since there's a one-to-one relationship between division and community,
            // we use communityId which is the same as divisionId
            const response = await contentAPI.getPosts({
                page: pageNum,
                page_size: 20,
                // Use communityId (one-to-one with administrative division)
                ...(communityId && { community_id: communityId }),
                // Fallback to municipalityId if communityId not provided
                ...(!communityId && municipalityId && { community_id: municipalityId }),
                // Filter by rubrique (slug/template_type) - "accueil" shows all
                ...(rubrique && { rubrique: rubrique }),
                ordering: '-created_at', // Most recent first
            });

            // getPosts returns posts directly (not wrapped in type/data like feed endpoint)
            const posts = response.results || [];

            if (replace) {
                setFeedItems(posts);
            } else {
                setFeedItems(prev => [...prev, ...posts]);
            }

            // Check if there's a next page
            setHasMore(!!response.next);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch feed:', err);
            setError('Failed to load feed');
        } finally {
            setLoading(false);
        }
    };

    // Initial load
    useEffect(() => {
        if (municipalityName || municipalityId || communityId) {
            fetchFeed(1, true);
        } else {
            setLoading(false);
        }
    }, [municipalityName, municipalityId, communityId, rubrique]);

    // Load more posts
    const loadMore = () => {
        if (!loading && hasMore) {
            setPage(prev => prev + 1);
            fetchFeed(page + 1, false);
        }
    };

    // Refresh feed
    const refreshFeed = () => {
        setPage(1);
        fetchFeed(1, true);
    };

    // Handle post interactions - these will be managed by individual PostCard components
    const handlePostUpdate = (postId, updatedPostData) => {
        setFeedItems(prevItems =>
            prevItems.map(post =>
                post.id === postId ? { ...post, ...updatedPostData } : post
            )
        );
    };

    const handlePostDelete = (postId) => {
        setFeedItems(prevItems =>
            prevItems.filter(post => post.id !== postId)
        );
    };

    if (!municipalityName && !municipalityId) {
        return (
            <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>⚠️</div>
                <h3>Erreur de chargement</h3>
                <p>Impossible de charger les publications sans spécifier la municipalité.</p>
            </div>
        );
    }

    const handleCreatePost = () => {
        if (user) {
            // If user is logged in and onCreatePostClick callback is provided, use it
            if (onCreatePostClick) {
                onCreatePostClick();
            }
            // Otherwise the PostCreator above the feed should be visible
        } else {
            // Redirect to login page
            navigate('/login', {
                state: {
                    from: window.location.pathname,
                    message: 'Connectez-vous pour créer une publication'
                }
            });
        }
    };

    if (loading && feedItems.length === 0) {
        return (
            <div className={styles.loading}>
                <div className={styles.spinner}></div>
                <p>Chargement des publications...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.emptyState} style={{ backgroundColor: '#FEE2E2', borderColor: '#FCA5A5' }}>
                <div className={styles.emptyIcon} style={{ color: '#DC2626' }}>⚠️</div>
                <h3 style={{ color: '#DC2626' }}>Erreur de chargement</h3>
                <p>{error}</p>
                <button
                    className={styles.createPostButton}
                    onClick={refreshFeed}
                    style={{ backgroundColor: '#DC2626' }}
                >
                    Réessayer
                </button>
            </div>
        );
    }

    if (!feedItems || feedItems.length === 0) {
        const rubriqueText = rubrique ? ` dans la rubrique "${rubrique}"` : '';
        return (
            <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>
                    <EditNoteIcon style={{ fontSize: '4rem', color: '#06B6D4' }} />
                </div>
                <h3>Aucune publication pour le moment</h3>
                <p>Soyez le premier à partager quelque chose d'intéressant{rubriqueText} à <strong>{municipalityName}</strong> !</p>
                <button
                    className={styles.createPostButton}
                    onClick={handleCreatePost}
                >
                    <AddIcon />
                    {user ? 'Créer une publication' : 'Se connecter pour publier'}
                </button>
            </div>
        );
    }

    return (
        <div className={styles.postFeed}>
            {feedItems.map((post, index) => (
                <PostCard
                    key={`post-${post.id}-${index}`}
                    post={post}
                    onDelete={handlePostDelete}
                    onUpdate={handlePostUpdate}
                    context="municipalityFeed"
                />
            ))}

            {/* Load More Button */}
            {hasMore && (
                <div style={{ textAlign: 'center', padding: '1rem' }}>
                    <button
                        onClick={loadMore}
                        disabled={loading}
                        className={styles.createPostButton}
                        style={{ opacity: loading ? 0.5 : 1 }}
                    >
                        {loading ? 'Chargement...' : 'Charger plus'}
                    </button>
                </div>
            )}

            {/* End of feed */}
            {!hasMore && feedItems.length > 0 && (
                <div style={{ textAlign: 'center', padding: '1rem', color: '#6B7280' }}>
                    <p>Vous êtes à jour ! 🎉</p>
                </div>
            )}
        </div>
    );
};

export default PostFeed;