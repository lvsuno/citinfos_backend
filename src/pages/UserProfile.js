import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';
import PostCreationModal from '../components/PostCreationModal';
import Post from '../components/Post';
import {
    Person as PersonIcon,
    LocationOn as LocationIcon,
    CalendarToday as CalendarIcon,
    Email as EmailIcon,
    Edit as EditIcon,
    Add as AddIcon
} from '@mui/icons-material';
import styles from './UserProfile.module.css';

const UserProfile = () => {
    const { user } = useAuth();
    const [userPosts, setUserPosts] = useState([]);
    const [isEditing, setIsEditing] = useState(false);
    const [showPostCreationModal, setShowPostCreationModal] = useState(false);

    // Obtenir les initiales du nom d'utilisateur
    const getUserInitials = () => {
        if (user?.firstName && user?.lastName) {
            return `${user.firstName[0]}${user.lastName[0]}`;
        }
        if (user?.email) {
            return user.email.substring(0, 2).toUpperCase();
        }
        return 'U';
    };

    // Gérer les posts de l'utilisateur
    useEffect(() => {
        // Pour l'instant, l'utilisateur n'a pas encore de posts existants
        // Les posts seront ajoutés uniquement quand l'utilisateur en crée
        setUserPosts([]);
    }, [user]);

    const handlePostCreated = (newPost) => {
        // Ajouter le nouveau post avec les informations de l'utilisateur
        const postWithUser = {
            ...newPost,
            id: Date.now(),
            user: {
                id: user.id,
                name: `${user.firstName || ''} ${user.lastName || ''}`.trim() || user.email?.split('@')[0] || 'Utilisateur',
                avatar: user.avatar,
                role: user.roleDisplay || 'Utilisateur'
            },
            timestamp: new Date().toISOString(),
            reactions: { like: 0, love: 0, laugh: 0, wow: 0, sad: 0, angry: 0 },
            comments: []
        };

        setUserPosts([postWithUser, ...userPosts]);
    };

    // Gestion du modal de création de posts
    const handlePostSubmit = async (postData) => {
        try {
            // Créer un nouveau post basé sur les données du modal
            const newPost = {
                id: Date.now(),
                content: postData.content.article || 'Nouveau post',
                type: postData.type,
                author: {
                    id: user.id,
                    name: `${user.firstName || ''} ${user.lastName || ''}`.trim() || user.email?.split('@')[0] || 'Utilisateur',
                    avatar: user.avatar,
                    initials: getUserInitials()
                },
                timestamp: new Date(),
                reactions: { like: 0, love: 0, haha: 0, wow: 0, sad: 0, angry: 0 },
                comments: [],
                visibility: postData.visibility,
                section: 'Mon Profil',
                municipality: user.location?.city || 'Ma Ville'
            };

            // Ajouter le poll si c'est un sondage
            if (postData.type === 'poll' && postData.content.poll) {
                newPost.poll = {
                    question: postData.content.poll.question,
                    options: postData.content.poll.options.map((option, index) => ({
                        id: index,
                        text: option,
                        votes: 0
                    })),
                    allowMultiple: postData.content.poll.allowMultiple,
                    totalVotes: 0
                };
            }

            // Ajouter les médias si c'est un post média
            if (postData.type === 'media' && postData.content.media) {
                newPost.attachments = postData.content.media;
            }

            setUserPosts([newPost, ...userPosts]);
            setShowPostCreationModal(false);
        } catch (error) {
            console.error('Erreur lors de la création du post:', error);
        }
    };

    const handleImageUpload = async (file) => {
        // Simuler l'upload d'image
        return {
            url: URL.createObjectURL(file),
            alt: file.name
        };
    };

    const handleVideoUpload = async (file) => {
        // Simuler l'upload de vidéo
        return {
            url: URL.createObjectURL(file),
            title: file.name
        };
    };

    const handleAudioUpload = async (file) => {
        // Simuler l'upload d'audio
        return {
            url: URL.createObjectURL(file),
            title: file.name
        };
    };

    const formatJoinDate = () => {
        // Pour la démo, utilisons une date fixe
        const joinDate = new Date('2024-01-15');
        return joinDate.toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'long'
        });
    };

    if (!user) {
        return (
            <Layout>
                <div className={styles.authRequired}>
                    <h2>Profil utilisateur</h2>
                    <p>Connectez-vous pour voir votre profil</p>
                    <button onClick={() => window.location.href = '/login'} className={styles.loginButton}>
                        Se connecter
                    </button>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className={styles.profileContainer}>
                {/* En-tête du profil */}
                <div className={styles.profileHeader}>
                    <div className={styles.coverPhoto}>
                        {/* Image de couverture (optionnelle pour plus tard) */}
                    </div>

                    <div className={styles.profileInfo}>
                        <div className={styles.avatarSection}>
                            <div className={styles.avatarContainer}>
                                {user.avatar ? (
                                    <img
                                        src={user.avatar}
                                        alt="Avatar"
                                        className={styles.avatar}
                                        onError={(e) => {
                                            e.target.style.display = 'none';
                                            e.target.parentElement.querySelector('.fallback-avatar').style.display = 'flex';
                                        }}
                                    />
                                ) : null}
                                <div
                                    className={`fallback-avatar ${styles.avatarFallback}`}
                                    style={{ display: user.avatar ? 'none' : 'flex' }}
                                >
                                    {getUserInitials()}
                                </div>
                            </div>

                            <button
                                className={styles.editButton}
                                onClick={() => setIsEditing(!isEditing)}
                                title="Modifier le profil"
                            >
                                <EditIcon />
                            </button>
                        </div>

                        <div className={styles.userDetails}>
                            <h1 className={styles.userName}>
                                {user.firstName && user.lastName
                                    ? `${user.firstName} ${user.lastName}`
                                    : user.email?.split('@')[0] || 'Utilisateur'
                                }
                            </h1>

                            <div className={styles.userMeta}>
                                <div className={styles.metaItem}>
                                    <PersonIcon className={styles.metaIcon} />
                                    <span>{user.roleDisplay || 'Utilisateur'}</span>
                                </div>

                                {user.location && (
                                    <div className={styles.metaItem}>
                                        <LocationIcon className={styles.metaIcon} />
                                        <span>{user.location.city}, {user.location.province}</span>
                                    </div>
                                )}

                                <div className={styles.metaItem}>
                                    <EmailIcon className={styles.metaIcon} />
                                    <span>{user.email}</span>
                                </div>

                                <div className={styles.metaItem}>
                                    <CalendarIcon className={styles.metaIcon} />
                                    <span>Membre depuis {formatJoinDate()}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Stats du profil */}
                <div className={styles.profileStats}>
                    <div className={styles.statItem}>
                        <span className={styles.statNumber}>{userPosts.length}</span>
                        <span className={styles.statLabel}>Publications</span>
                    </div>
                    <div className={styles.statItem}>
                        <span className={styles.statNumber}>
                            {userPosts.reduce((sum, post) =>
                                sum + Object.values(post.reactions || {}).reduce((a, b) => a + b, 0), 0
                            )}
                        </span>
                        <span className={styles.statLabel}>Réactions</span>
                    </div>
                    <div className={styles.statItem}>
                        <span className={styles.statNumber}>
                            {userPosts.reduce((sum, post) => sum + (post.comments?.length || 0), 0)}
                        </span>
                        <span className={styles.statLabel}>Commentaires</span>
                    </div>
                </div>

                {/* Section des publications */}
                <div className={styles.postsSection}>
                    <div className={styles.sectionHeader}>
                        <h2>Mes Publications</h2>
                    </div>

                    {/* Bouton de création de posts - seulement si authentifié */}
                    {user && (
                        <div className={styles.postCreatorPlaceholder}>
                            <div className={styles.postCreatorContent}>
                                <div className={styles.userAvatar}>
                                    {user?.avatar ? (
                                        <img src={user.avatar} alt="Avatar" />
                                    ) : (
                                        <span>{getUserInitials()}</span>
                                    )}
                                </div>
                                <button
                                    className={styles.postCreatorButton}
                                    onClick={() => setShowPostCreationModal(true)}
                                >
                                    <span className={styles.postCreatorPlaceholderText}>
                                        Quoi de neuf dans votre profil ?
                                    </span>
                                </button>
                                <button
                                    className={styles.addPostButton}
                                    onClick={() => setShowPostCreationModal(true)}
                                >
                                    <AddIcon />
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Feed des posts de l'utilisateur */}
                    {userPosts.length > 0 ? (
                        <div className={styles.userPostsFeed}>
                            {userPosts.map((post) => (
                                <Post
                                    key={post.id}
                                    post={post}
                                />
                            ))}
                        </div>
                    ) : (
                        <div className={styles.noPosts}>
                            <div className={styles.noPostsIcon}>📝</div>
                            <h3>Aucune publication pour le moment</h3>
                            <p>Commencez à partager vos idées et expériences avec la communauté !</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Modal de création de posts */}
            <PostCreationModal
                isOpen={showPostCreationModal}
                onClose={() => setShowPostCreationModal(false)}
                onSubmit={handlePostSubmit}
                onImageUpload={handleImageUpload}
                onVideoUpload={handleVideoUpload}
                onAudioUpload={handleAudioUpload}
            />
        </Layout>
    );
};

export default UserProfile;