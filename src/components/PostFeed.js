import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Add as AddIcon, EditNote as EditNoteIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { getPostsByMunicipality, getPostsByMunicipalityAndSection } from '../data/postsData';
import Post from './Post';
import styles from './PostFeed.module.css';

const PostFeed = ({ municipalityName, section = null, sortOrder = 'recent', onCreatePostClick }) => {
    const { user } = useAuth();
    const navigate = useNavigate();

    if (!municipalityName) {
        return (
            <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>⚠️</div>
                <h3>Erreur de chargement</h3>
                <p>Impossible de charger les publications sans spécifier la municipalité.</p>
            </div>
        );
    }

    // Filtrer les posts selon la municipalité et optionnellement la section
    let posts = section
        ? getPostsByMunicipalityAndSection(municipalityName, section)
        : getPostsByMunicipality(municipalityName);

    // Trier les posts selon l'ordre demandé
    if (posts && posts.length > 0) {
        posts = [...posts].sort((a, b) => {
            switch (sortOrder) {
                case 'featured':
                    // Priorité aux posts épinglés/featured, puis par date
                    if (a.featured && !b.featured) return -1;
                    if (!a.featured && b.featured) return 1;
                    // Si même statut featured, trier par date
                    return new Date(b.createdAt) - new Date(a.createdAt);
                
                case 'recent':
                default:
                    // Tri par date de création (plus récents en premier)
                    return new Date(b.createdAt) - new Date(a.createdAt);
            }
        });
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

    if (!posts || posts.length === 0) {
        const sectionText = section ? ` dans la section "${section}"` : '';
        return (
            <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>
                    <EditNoteIcon style={{ fontSize: '4rem', color: '#06B6D4' }} />
                </div>
                <h3>Aucune publication pour le moment</h3>
                <p>Soyez le premier à partager quelque chose d'intéressant{sectionText} à <strong>{municipalityName}</strong> !</p>
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
            {posts.map(post => (
                <Post key={post.id} post={post} />
            ))}
        </div>
    );
};

export default PostFeed;