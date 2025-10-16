import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useMunicipality } from '../contexts/MunicipalityContext';
import { getMunicipalityBySlug } from '../data/municipalitiesUtils';
import { isValidUrlPath, getCountryByUrlPath, getAdminDivisionUrlPath, getCountryISO3ByUrlPath } from '../config/adminDivisions';
import geolocationService from '../services/geolocationService';
import { getCurrentDivision, setCurrentDivision, cleanupOldDivisionKeys } from '../utils/divisionStorage';
import { trackPageVisit } from '../utils/navigationTracker';
import { getDefaultDivisionUrl } from '../utils/defaultDivisionRedirect';
import Layout from '../components/Layout';
import PostFeed from '../components/PostFeed';
import HomeNavigation from '../components/HomeNavigation';
import PostCreationModal from '../components/PostCreationModal';
import VerifyAccount from '../components/VerifyAccount';
import apiService from '../services/apiService';
import contentAPI from '../services/contentAPI';
import styles from './MunicipalityDashboard.module.css';

const MunicipalityDashboard = () => {
    const { municipalitySlug, section = 'accueil' } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const { user, loading: authLoading } = useAuth();
    const { switchMunicipality } = useMunicipality();

    // Separate state for page division (from URL) vs legacy municipality data
    const [pageDivision, setPageDivision] = useState(null);
    const [municipality, setMunicipality] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeRubrique, setActiveRubrique] = useState(section || 'accueil');
    const [posts, setPosts] = useState([]);
    const [showVerificationModal, setShowVerificationModal] = useState(false);
    const [verificationMessage, setVerificationMessage] = useState('');
    const [showPostCreationModal, setShowPostCreationModal] = useState(false);
    const [homeSortOrder, setHomeSortOrder] = useState('recent'); // État pour le tri des posts dans l'accueil

    // Detect current URL path (municipality, commune, city, etc.)
    const currentUrlPath = location.pathname.split('/')[1];

    // Validate that this URL path is supported
    const isCurrentPathValid = isValidUrlPath(currentUrlPath);

    // Get country configuration for this URL path
    const countryConfig = getCountryByUrlPath(currentUrlPath);

    // TEST: Make an API call to verify middleware is working
    useEffect(() => {
        console.log('🧪 [TEST] Municipality page mounted - testing API call');
        const testApiCall = async () => {
            try {
                console.log('🧪 [TEST] Making test API call to /auth/user-info/');
                const response = await apiService.get('/auth/user-info/');
                console.log('🧪 [TEST] API call successful:', response.data);
            } catch (error) {
                console.log('🧪 [TEST] API call failed (expected if not logged in):', error.response?.status, error.response?.data);
            }
        };
        testApiCall();
    }, []);

    // No redirect for unauthenticated users - allow read-only access

    // Validate URL path and redirect if invalid
    useEffect(() => {
        if (!isCurrentPathValid && currentUrlPath !== 'municipality') {
            // Invalid URL path detected - redirect to proper format
            const defaultUrlPath = getAdminDivisionUrlPath();
            console.log(`⚠️ Invalid URL path '${currentUrlPath}', redirecting to '${defaultUrlPath}'`);
            navigate(`/${defaultUrlPath}/${municipalitySlug}${section ? `/${section}` : ''}`, { replace: true });
            return;
        }
    }, [currentUrlPath, municipalitySlug, section, navigate, isCurrentPathValid]);

    // Charger la municipalité basée sur le slug de l'URL
    // Clean up old localStorage keys on mount
    useEffect(() => {
        cleanupOldDivisionKeys();
    }, []);

    // CRITICAL: Fetch division data from API using URL slug, not from user profile
    useEffect(() => {
        const loadPageDivision = async () => {
            if (!municipalitySlug || !currentUrlPath) {
                setLoading(false);
                return;
            }

            // Get country ISO3 code from URL path (municipality->CAN, commune->BEN)
            const countryISO3 = getCountryISO3ByUrlPath(currentUrlPath);

            if (!countryISO3) {
                console.error('❌ Could not determine country from URL path:', currentUrlPath);
                // Redirect to default division instead of dashboard
                const defaultUrl = await getDefaultDivisionUrl(user, null);
                navigate(defaultUrl, { replace: true });
                return;
            }

            // Check if this division is already the current active one
            const currentDivision = getCurrentDivision();
            if (currentDivision &&
                currentDivision.slug === municipalitySlug &&
                currentDivision.country === countryISO3) {

                console.log('� Division already loaded from single storage:', currentDivision.name);
                setPageDivision(currentDivision);
                switchMunicipality(
                    currentDivision.name,
                    currentDivision.id,
                    {
                        country: currentDivision.country,
                        boundary_type: currentDivision.boundary_type,
                        admin_level: currentDivision.admin_level,
                        level_1_id: currentDivision.level_1_id
                    }
                );

                // Create municipality object
                const foundMunicipality = getMunicipalityBySlug(municipalitySlug);
                if (foundMunicipality) {
                    setMunicipality({ ...foundMunicipality, ...currentDivision });
                } else {
                    setMunicipality({
                        id: currentDivision.id,
                        nom: currentDivision.name,
                        name: currentDivision.name,
                        region: currentDivision.parent?.name,
                        fromApi: true,
                        ...currentDivision
                    });
                }

                setLoading(false);
                return;
            }

            // Need to fetch new division from API
            setLoading(true);

            try {
                console.log('🔍 Loading division from URL:', {
                    slug: municipalitySlug,
                    urlPath: currentUrlPath,
                    countryISO3
                });

                // Fetch division data from API at country's default level
                const result = await geolocationService.getDivisionBySlug(
                    municipalitySlug,
                    countryISO3
                );

                if (result.success && result.division) {
                    console.log('✅ Page division loaded:', result.division.name);

                    // Add slug to division data
                    const divisionWithSlug = {
                        ...result.division,
                        slug: municipalitySlug,
                        country: countryISO3
                    };

                    setPageDivision(divisionWithSlug);

                    // Store as THE current active division (single source of truth)
                    setCurrentDivision(divisionWithSlug);

                    // Track this page visit for smart redirect
                    trackPageVisit(location.pathname, {
                        id: divisionWithSlug.id,
                        name: divisionWithSlug.name,
                        slug: municipalitySlug,
                        country: countryISO3
                    });

                    // Also update context with full division data
                    switchMunicipality(
                        divisionWithSlug.name,
                        divisionWithSlug.id,
                        {
                            country: countryISO3,
                            boundary_type: divisionWithSlug.boundary_type,
                            admin_level: divisionWithSlug.admin_level,
                            level_1_id: divisionWithSlug.level_1_id
                        }
                    );

                    // Try to find in local data for legacy support
                    const foundMunicipality = getMunicipalityBySlug(municipalitySlug);
                    if (foundMunicipality) {
                        setMunicipality({ ...foundMunicipality, ...divisionWithSlug });
                    } else {
                        // Create municipality object from API data
                        setMunicipality({
                            id: divisionWithSlug.id,
                            nom: divisionWithSlug.name,
                            name: divisionWithSlug.name,
                            region: divisionWithSlug.parent?.name,
                            fromApi: true,
                            ...divisionWithSlug
                        });
                    }
                } else {
                    console.error('❌ Division not found:', municipalitySlug);
                    // Division not found - redirect to default division
                    const defaultUrl = await getDefaultDivisionUrl(user, null);
                    navigate(defaultUrl, { replace: true });
                }
            } catch (error) {
                console.error('❌ Error loading division:', error);
                // Error loading - redirect to default division
                const defaultUrl = await getDefaultDivisionUrl(user, null);
                navigate(defaultUrl, { replace: true });
            } finally {
                setLoading(false);
            }
        };

        loadPageDivision();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [municipalitySlug, currentUrlPath]); // Reload when URL changes

    // Mettre à jour la rubrique active quand la section change
    useEffect(() => {
        const currentSection = section || 'accueil';
        setActiveRubrique(currentSection);
    }, [section]);

    // Handle verification modal display from login navigation
    useEffect(() => {
        if (location.state?.showVerificationModal) {
            setShowVerificationModal(true);
            setVerificationMessage(location.state.verificationMessage || '');

            // Clear the state to prevent modal showing on refresh
            navigate(location.pathname, { replace: true, state: {} });
        }
    }, [location.state, navigate, location.pathname]);

    const handleRubriqueChange = (rubriquePathOrName) => {
        // Si c'est déjà un path (venant du Sidebar), l'utiliser directement
        // Sinon, c'est peut-être un nom, donc on essaie de le convertir
        const newSection = rubriquePathOrName.toLowerCase();
        setActiveRubrique(newSection);

        // Use the current URL path or default to 'municipality' for backward compatibility
        const urlPath = isCurrentPathValid ? currentUrlPath : 'municipality';
        navigate(`/${urlPath}/${municipalitySlug}/${newSection}`);
    };

    const handlePostCreated = (newPost) => {
        setPosts(prevPosts => [newPost, ...prevPosts]);
    };

    const handleOpenPostCreationModal = () => {
        setShowPostCreationModal(true);
    };

    const handleClosePostCreationModal = () => {
        setShowPostCreationModal(false);
    };

    const handlePostSubmit = async (postData) => {
        try {
            // Submit the post to the API
            const createdPost = await contentAPI.createPost(postData);

            // Add the new post to the local state
            handlePostCreated(createdPost);

            // Close the modal
            setShowPostCreationModal(false);
        } catch (error) {
            console.error('Failed to create post:', error);
            throw error; // Let the modal handle the error display
        }
    };

    const handleVerificationSuccess = () => {
        setShowVerificationModal(false);
        // Optionally refresh user data or show success message
    };

    const handleVerificationClose = () => {
        setShowVerificationModal(false);
    };

    if (loading) {
        return (
            <div className={styles.loading}>
                <div className={styles.spinner}></div>
                <p>Chargement de {municipalitySlug}...</p>
            </div>
        );
    }

    // Afficher un spinner pendant le chargement de l'authentification
    if (authLoading) {
        return (
            <Layout>
                <div className={styles.loading}>
                    <div className={styles.spinner}></div>
                    <p>Chargement...</p>
                </div>
            </Layout>
        );
    }

    // Allow access even without user authentication (read-only mode)

    if (!municipality) {
        return (
            <div className={styles.error}>
                <h2>Municipalité non trouvée</h2>
                <p>La municipalité "{municipalitySlug}" n'a pas été trouvée.</p>
                <button onClick={async () => {
                    const defaultUrl = await getDefaultDivisionUrl(user, null);
                    navigate(defaultUrl, { replace: true });
                }}>
                    Retour à votre division
                </button>
            </div>
        );
    }

    return (
        <Layout
            activeRubrique={activeRubrique}
            onRubriqueChange={handleRubriqueChange}
            municipalityName={pageDivision?.name || municipality.nom}
            pageDivision={pageDivision}
            initialChatUser={location.state?.openChatWithUser}
        >
            <div className={styles.sectionContent}>
                {renderSectionContent(activeRubrique, municipality, handlePostCreated, posts, user, navigate, pageDivision, handleOpenPostCreationModal, homeSortOrder, setHomeSortOrder)}
            </div>

            {/* Post Creation Modal */}
            <PostCreationModal
                isOpen={showPostCreationModal}
                onClose={handleClosePostCreationModal}
                onSubmit={handlePostSubmit}
            />

            {/* Verification Modal - shows after login if verification required */}
            {showVerificationModal && user && (
                <VerifyAccount
                    show={showVerificationModal}
                    onHide={handleVerificationClose}
                    onSuccess={handleVerificationSuccess}
                    userEmail={user.email}
                    message={verificationMessage}
                />
            )}
        </Layout>
    );
};

// Helper function to get user initials (same as TopBar)
const getUserInitials = (user) => {
    if (!user) return 'U';

    if (user.firstName && user.lastName) {
        return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();
    }
    if (user.username) {
        return user.username.substring(0, 2).toUpperCase();
    }
    return 'U';
};

// Fonction pour rendre le contenu spécifique à chaque section
const renderSectionContent = (section, municipality, onPostCreated, posts, user, navigate, pageDivision, onOpenPostCreationModal, homeSortOrder, setHomeSortOrder) => {
    const sectionLower = section.toLowerCase();

    // Fonction pour obtenir le nom d'affichage de la section
    const getSectionDisplayName = (sectionKey) => {
        const sectionNames = {
            'accueil': 'Accueil',
            'actualites': 'Actualités',
            'evenements': 'Événements',
            'transport': 'Transport',
            'commerces': 'Commerces',
            'art': 'Art',
            'litterature': 'Littérature',
            'poesie': 'Poésie',
            'photographie': 'Photographie',
            'histoire': 'Histoire',
            'sport': 'Sport',
            'culture': 'Culture',
            'reconnaissance': 'Reconnaissance',
            'chronologie': 'Chronologie'
        };
        return sectionNames[sectionKey] || sectionKey;
    };

    // Fonction pour obtenir la description de chaque section
    const getSectionDescription = (sectionKey) => {
        const sectionDescriptions = {
            'actualites': 'Partagez les dernières nouvelles, découvertes et moments marquants de votre quotidien local.',
            'evenements': 'Découvrez et annoncez les événements, festivals, spectacles et activités communautaires.',
            'transport': 'Informez-vous sur la circulation, les travaux, les transports en commun et la mobilité urbaine.',
            'commerces': 'Mettez en avant les commerces locaux, leurs nouveautés, promotions et initiatives.',
            'art': 'Exposez vos créations artistiques, découvrez les talents locaux et les expositions.',
            'litterature': 'Partagez vos écrits, recommandations de lecture et discussions littéraires.',
            'poesie': 'Exprimez-vous en vers, partagez vos poèmes et découvrez la poésie locale.',
            'photographie': 'Capturez et partagez la beauté de votre région à travers vos images.',
            'histoire': 'Explorez le patrimoine, les récits historiques et la mémoire collective.',
            'sport': 'Suivez les équipes locales, partagez vos exploits sportifs et événements athlétiques.',
            'culture': 'Célébrez la richesse culturelle locale, traditions et expressions artistiques.',
            'reconnaissance': 'Mettez en lumière les contributions remarquables de votre communauté.',
            'chronologie': 'Retracez l\'évolution et les moments clés de votre municipalité.'
        };
        return sectionDescriptions[sectionKey] || 'Participez aux discussions et partagez vos contributions dans cette section.';
    };

    switch (sectionLower) {
        case 'accueil':
            const divisionName = pageDivision?.name || municipality.nom;
            return (
                <div className={styles.sectionWrapper}>
                    <div className={styles.sectionCover}>
                        <div className={styles.coverContent}>
                            <h1 className={styles.sectionTitle}>Accueil - {divisionName}</h1>
                            <p className={styles.sectionDescription}>
                                Découvrez l'activité de votre communauté, connectez-vous avec vos concitoyens et restez informés de tout ce qui se passe à <strong>{divisionName}</strong>.
                            </p>
                        </div>
                    </div>

                    <div className={styles.postsSection}>
                        {user && (
                            <div
                                onClick={onOpenPostCreationModal}
                                style={{
                                    padding: '16px',
                                    marginBottom: '20px',
                                    backgroundColor: 'white',
                                    borderRadius: '8px',
                                    border: '1px solid #e1e8ed',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease',
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.borderColor = '#1da1f2';
                                    e.currentTarget.style.backgroundColor = '#f7f9fa';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.borderColor = '#e1e8ed';
                                    e.currentTarget.style.backgroundColor = 'white';
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div
                                        style={{
                                            width: '40px',
                                            height: '40px',
                                            borderRadius: '50%',
                                            backgroundColor: '#1E293B',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            overflow: 'hidden',
                                            flexShrink: 0
                                        }}
                                    >
                                        {user.profile?.profile_picture || user.avatar ? (
                                            <img
                                                src={user.profile?.profile_picture || user.avatar}
                                                alt="Your avatar"
                                                style={{
                                                    width: '100%',
                                                    height: '100%',
                                                    objectFit: 'cover'
                                                }}
                                                onError={(e) => {
                                                    e.target.style.display = 'none';
                                                    const fallback = e.target.parentElement.querySelector('.fallback-initials');
                                                    if (fallback) fallback.style.display = 'flex';
                                                }}
                                            />
                                        ) : null}
                                        <span
                                            className="fallback-initials"
                                            style={{
                                                color: 'white',
                                                fontWeight: 'bold',
                                                fontSize: '16px',
                                                display: (user.profile?.profile_picture || user.avatar) ? 'none' : 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                width: '100%',
                                                height: '100%'
                                            }}
                                        >
                                            {getUserInitials(user)}
                                        </span>
                                    </div>
                                    <div
                                        style={{
                                            flex: 1,
                                            padding: '10px 16px',
                                            backgroundColor: '#f0f2f5',
                                            borderRadius: '20px',
                                            color: '#65676b',
                                            fontSize: '15px'
                                        }}
                                    >
                                        Quoi de neuf, {user.first_name || user.firstName || user.username} ?
                                    </div>
                                </div>
                            </div>
                        )}
                        
                        {/* Navigation pour trier les posts dans l'accueil */}
                        <HomeNavigation 
                            activeSort={homeSortOrder}
                            onSortChange={setHomeSortOrder}
                        />
                        
                        <PostFeed
                            municipalityName={divisionName}
                            sortOrder={homeSortOrder}
                            onCreatePostClick={onOpenPostCreationModal}
                        />
                    </div>
                </div>
            );

        default:
            return (
                <div className={styles.sectionWrapper}>
                    <div className={styles.sectionCover}>
                        <div className={styles.coverContent}>
                            <h1 className={styles.sectionTitle}>{getSectionDisplayName(sectionLower)}</h1>
                            <p className={styles.sectionDescription}>
                                {getSectionDescription(sectionLower)}
                            </p>
                        </div>
                    </div>

                    <div className={styles.postsSection}>
                        {user && (
                            <div
                                onClick={onOpenPostCreationModal}
                                style={{
                                    padding: '16px',
                                    marginBottom: '20px',
                                    backgroundColor: 'white',
                                    borderRadius: '8px',
                                    border: '1px solid #e1e8ed',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease',
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.borderColor = '#1da1f2';
                                    e.currentTarget.style.backgroundColor = '#f7f9fa';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.borderColor = '#e1e8ed';
                                    e.currentTarget.style.backgroundColor = 'white';
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div
                                        style={{
                                            width: '40px',
                                            height: '40px',
                                            borderRadius: '50%',
                                            backgroundColor: '#1E293B',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            overflow: 'hidden',
                                            flexShrink: 0
                                        }}
                                    >
                                        {user.profile?.profile_picture || user.avatar ? (
                                            <img
                                                src={user.profile?.profile_picture || user.avatar}
                                                alt="Your avatar"
                                                style={{
                                                    width: '100%',
                                                    height: '100%',
                                                    objectFit: 'cover'
                                                }}
                                                onError={(e) => {
                                                    e.target.style.display = 'none';
                                                    const fallback = e.target.parentElement.querySelector('.fallback-initials');
                                                    if (fallback) fallback.style.display = 'flex';
                                                }}
                                            />
                                        ) : null}
                                        <span
                                            className="fallback-initials"
                                            style={{
                                                color: 'white',
                                                fontWeight: 'bold',
                                                fontSize: '16px',
                                                display: (user.profile?.profile_picture || user.avatar) ? 'none' : 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                width: '100%',
                                                height: '100%'
                                            }}
                                        >
                                            {getUserInitials(user)}
                                        </span>
                                    </div>
                                    <div
                                        style={{
                                            flex: 1,
                                            padding: '10px 16px',
                                            backgroundColor: '#f0f2f5',
                                            borderRadius: '20px',
                                            color: '#65676b',
                                            fontSize: '15px'
                                        }}
                                    >
                                        Quoi de neuf, {user.first_name || user.firstName || user.username} ?
                                    </div>
                                </div>
                            </div>
                        )}
                        <PostFeed
                            municipalityName={municipality.nom}
                            section={getSectionDisplayName(sectionLower)}
                            onCreatePostClick={onOpenPostCreationModal}
                        />
                    </div>
                </div>
            );
    }
};

export default MunicipalityDashboard;