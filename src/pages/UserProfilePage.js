import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    ArrowBack as ArrowBackIcon,
    LocationOn as LocationIcon,
    Email as EmailIcon,
    CalendarToday as CalendarIcon,
    PersonAdd as PersonAddIcon,
    Chat as ChatIcon,
    MoreVert as MoreIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';
import styles from './UserProfilePage.module.css';

const UserProfilePage = () => {
    const { username } = useParams();
    const navigate = useNavigate();
    const { user: currentUser } = useAuth();
    const [userProfile, setUserProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadUserProfile();
    }, [username]);

    const loadUserProfile = async () => {
        try {
            setLoading(true);
            // TODO: Remplacer par un vrai appel API
            // Simulation d'un profil utilisateur
            const mockProfile = {
                id: Math.floor(Math.random() * 1000),
                username: username,
                full_name: `Utilisateur ${username}`,
                email: `${username}@example.com`,
                avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(username)}&background=random&size=200`,
                municipality: 'Sherbrooke',
                join_date: '2024-01-15',
                bio: 'Passionné par ma communauté et toujours prêt à aider !',
                is_online: Math.random() > 0.5,
                profile: {
                    interests: ['Culture', 'Photographie', 'Sport'],
                    achievements: ['Contributeur actif', 'Nouveau membre']
                }
            };
            
            setUserProfile(mockProfile);
        } catch (err) {
            console.error('Erreur lors du chargement du profil:', err);
            setError('Impossible de charger le profil utilisateur');
        } finally {
            setLoading(false);
        }
    };

    const handleBackClick = () => {
        navigate(-1); // Retour à la page précédente
    };

    const handleStartConversation = () => {
        // Naviguer vers le dashboard de l'utilisateur avec l'instruction d'ouvrir le chat
        if (currentUser) {
            // Aller vers le dashboard par défaut de l'utilisateur connecté
            navigate('/dashboard', { 
                state: { 
                    openChatWithUser: {
                        id: userProfile.id,
                        username: userProfile.username,
                        full_name: userProfile.full_name,
                        avatar: userProfile.avatar,
                        email: userProfile.email,
                        municipality: userProfile.municipality
                    }
                }
            });
        } else {
            // Si pas connecté, rediriger vers login
            navigate('/login', {
                state: {
                    from: window.location.pathname,
                    message: 'Connectez-vous pour envoyer un message'
                }
            });
        }
    };

    const handleConnect = () => {
        // TODO: Intégrer avec le système de connexions
        console.log('Connecter avec', userProfile.username);
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('fr-CA', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    if (loading) {
        return (
            <Layout>
                <div className={styles.loadingContainer}>
                    <div className={styles.spinner}></div>
                    <p>Chargement du profil...</p>
                </div>
            </Layout>
        );
    }

    if (error || !userProfile) {
        return (
            <Layout>
                <div className={styles.errorContainer}>
                    <h2>Erreur</h2>
                    <p>{error || 'Profil utilisateur non trouvé'}</p>
                    <button className={styles.backButton} onClick={handleBackClick}>
                        <ArrowBackIcon />
                        Retour
                    </button>
                </div>
            </Layout>
        );
    }

    const isOwnProfile = currentUser?.username === userProfile.username;

    return (
        <Layout>
            <div className={styles.userProfilePage}>
                {/* Header avec bouton retour */}
                <div className={styles.header}>
                    <button className={styles.backButton} onClick={handleBackClick}>
                        <ArrowBackIcon />
                        Retour
                    </button>
                    <h1 className={styles.pageTitle}>Profil utilisateur</h1>
                </div>

                {/* Profil principal */}
                <div className={styles.profileContainer}>
                    <div className={styles.profileCard}>
                        {/* Section avatar et infos principales */}
                        <div className={styles.profileHeader}>
                            <div className={styles.avatarSection}>
                                <div className={styles.avatarContainer}>
                                    <img
                                        src={userProfile.avatar}
                                        alt={userProfile.full_name}
                                        className={styles.avatar}
                                        onError={(e) => {
                                            e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile.full_name)}&background=random&size=200`;
                                        }}
                                    />
                                    {userProfile.is_online && (
                                        <div className={styles.onlineIndicator}>
                                            <span className={styles.onlineDot}></span>
                                            <span className={styles.onlineText}>En ligne</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className={styles.profileInfo}>
                                <h2 className={styles.fullName}>{userProfile.full_name}</h2>
                                <p className={styles.username}>@{userProfile.username}</p>
                                
                                {userProfile.bio && (
                                    <p className={styles.bio}>{userProfile.bio}</p>
                                )}

                                <div className={styles.profileDetails}>
                                    <div className={styles.detailItem}>
                                        <LocationIcon className={styles.detailIcon} />
                                        <span>{userProfile.municipality}</span>
                                    </div>
                                    <div className={styles.detailItem}>
                                        <CalendarIcon className={styles.detailIcon} />
                                        <span>Membre depuis {formatDate(userProfile.join_date)}</span>
                                    </div>
                                </div>

                                {/* Actions */}
                                {!isOwnProfile && (
                                    <div className={styles.actions}>
                                        <button 
                                            className={styles.primaryAction}
                                            onClick={handleConnect}
                                        >
                                            <PersonAddIcon />
                                            Connecter
                                        </button>
                                        <button 
                                            className={styles.secondaryAction}
                                            onClick={handleStartConversation}
                                        >
                                            <ChatIcon />
                                            Message
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Sections additionnelles */}
                        <div className={styles.profileSections}>
                            {/* Centres d'intérêt */}
                            {userProfile.profile?.interests && userProfile.profile.interests.length > 0 && (
                                <div className={styles.section}>
                                    <h3 className={styles.sectionTitle}>Centres d'intérêt</h3>
                                    <div className={styles.interests}>
                                        {userProfile.profile.interests.map((interest, index) => (
                                            <span key={index} className={styles.interestTag}>
                                                {interest}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Réalisations */}
                            {userProfile.profile?.achievements && userProfile.profile.achievements.length > 0 && (
                                <div className={styles.section}>
                                    <h3 className={styles.sectionTitle}>Réalisations</h3>
                                    <div className={styles.achievements}>
                                        {userProfile.profile.achievements.map((achievement, index) => (
                                            <div key={index} className={styles.achievement}>
                                                🏆 {achievement}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default UserProfilePage;