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
import PostCreationModal from '../components/PostCreationModal';
import InlinePostCreator from '../components/InlinePostCreator';
import ThreadListCompact from '../components/social/ThreadListCompact';
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
    const [rubriqueTemplates, setRubriqueTemplates] = useState([]); // Store rubrique templates with IDs

    // Detect current URL path (municipality, commune, city, etc.)
    const currentUrlPath = location.pathname.split('/')[1];

    // Validate that this URL path is supported
    const isCurrentPathValid = isValidUrlPath(currentUrlPath);

    // Get country configuration for this URL path
    const countryConfig = getCountryByUrlPath(currentUrlPath);

    // No redirect for unauthenticated users - allow read-only access

    // Validate URL path and redirect if invalid
    useEffect(() => {
        if (!isCurrentPathValid && currentUrlPath !== 'municipality') {
            // Invalid URL path detected - redirect to proper format
            const defaultUrlPath = getAdminDivisionUrlPath();
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
                // Redirect to default division instead of dashboard
                const defaultUrl = await getDefaultDivisionUrl(user, null);
                navigate(defaultUrl, { replace: true });
                return;
            }

            // Check if this division is already the current active one
            const currentDivision = getCurrentDivision();
            if (currentDivision &&
                currentDivision.slug === municipalitySlug &&
                currentDivision.country === countryISO3 &&
                currentDivision.community_id) { // Only use cache if it has community_id

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
                // Fetch division data from API at country's default level
                const result = await geolocationService.getDivisionBySlug(
                    municipalitySlug,
                    countryISO3
                );

                if (result.success && result.division) {
                    // Add slug to division data
                    const divisionWithSlug = {
                        ...result.division,
                        slug: municipalitySlug,
                        country: countryISO3
                    };

                    console.log('MunicipalityDashboard - Division data:', divisionWithSlug);
                    console.log('MunicipalityDashboard - Has community_id?', divisionWithSlug.community_id);

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
                    // Division not found - redirect to default division
                    const defaultUrl = await getDefaultDivisionUrl(user, null);
                    navigate(defaultUrl, { replace: true });
                }
            } catch (error) {
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

    // Helper function to get rubrique template ID from section name
    const getRubriqueTemplateId = (sectionName) => {
        console.log('getRubriqueTemplateId called with:', sectionName);
        console.log('Available rubrique templates:', rubriqueTemplates);

        if (!sectionName || !rubriqueTemplates.length) {
            console.log('Early return: no section name or templates');
            return null;
        }

        const sectionLower = sectionName.toLowerCase();

        // Find rubrique by template_type (matches section name)
        // Try exact match first, then check if template_type starts with section name,
        // or if name matches
        const rubrique = rubriqueTemplates.find(r => {
            const templateTypeLower = r.template_type?.toLowerCase() || '';
            const nameLower = r.name?.toLowerCase() || '';
            const defaultNameLower = r.default_name?.toLowerCase() || '';

            return templateTypeLower === sectionLower ||
                   nameLower === sectionLower ||
                   defaultNameLower === sectionLower ||
                   templateTypeLower.startsWith(sectionLower + '_') ||
                   templateTypeLower.endsWith('_' + sectionLower);
        });

        console.log('Found rubrique:', rubrique);
        return rubrique?.id || null;
    };

    // Fetch rubrique templates from community when municipality changes
    useEffect(() => {
        const fetchRubriqueTemplates = async () => {
            if (!municipalitySlug) {
                return;
            }

            try {
                // Fetch rubriques enabled for this community (same as Sidebar does)
                const communityAPI = (await import('../services/communityAPI')).default;
                const data = await communityAPI.getEnabledRubriques(municipalitySlug);

                console.log('Rubrique templates from community API:', data);

                if (data.rubriques && Array.isArray(data.rubriques)) {
                    // Flatten the hierarchy to get all rubriques (parent + children)
                    const flattenRubriques = (rubriques) => {
                        let flat = [];
                        rubriques.forEach(r => {
                            flat.push(r);
                            if (r.children && r.children.length > 0) {
                                flat = flat.concat(flattenRubriques(r.children));
                            }
                        });
                        return flat;
                    };

                    const allRubriques = flattenRubriques(data.rubriques);
                    console.log('Flattened rubriques:', allRubriques);
                    setRubriqueTemplates(allRubriques);
                } else {
                    console.warn('No rubriques in response:', data);
                }
            } catch (error) {
                console.error('Error fetching rubrique templates:', error);
            }
        };

        fetchRubriqueTemplates();
    }, [municipalitySlug]); // Fetch when municipality changes

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
        >
            <div className={styles.sectionContent}>
                {renderSectionContent(activeRubrique, municipality, handlePostCreated, posts, user, navigate, pageDivision, handleOpenPostCreationModal, municipalitySlug, getRubriqueTemplateId)}
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
const renderSectionContent = (section, municipality, onPostCreated, posts, user, navigate, pageDivision, onOpenPostCreationModal, municipalitySlug, getRubriqueTemplateId) => {
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
                        {/* Grid layout: Posts on left, Threads on right (sidebar) */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '20px', alignItems: 'start' }}>
                            {/* Main feed */}
                            <div>
                                <PostFeed
                                    municipalityName={divisionName}
                                    municipalityId={pageDivision?.id}
                                    rubrique="accueil"
                                    onCreatePostClick={onOpenPostCreationModal}
                                />
                            </div>

                            {/* Sidebar: Recent threads */}
                            <div style={{ position: 'sticky', top: '20px' }}>
                                <ThreadListCompact
                                    communityId={pageDivision?.community_id || pageDivision?.id}
                                    municipalitySlug={municipalitySlug}
                                    limit={5}
                                />
                            </div>
                        </div>
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
                            <InlinePostCreator
                                division={pageDivision}
                                section={sectionLower}
                                rubriqueTemplateId={getRubriqueTemplateId(sectionLower)}
                                community={pageDivision?.community_id ? { id: pageDivision.community_id } : pageDivision}
                                municipalitySlug={municipality?.slug || municipalitySlug}
                                onPostCreated={onPostCreated}
                                placeholder={`Quoi de neuf dans ${getSectionDisplayName(sectionLower)} ?`}
                            />
                        )}
                        {/* Old modal post creator - REPLACED WITH INLINE
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
                        )} */}
                        <PostFeed
                            municipalityName={municipality.nom}
                            municipalityId={pageDivision?.id}
                            rubrique={sectionLower}
                            onCreatePostClick={onOpenPostCreationModal}
                        />
                    </div>
                </div>
            );
    }
};

export default MunicipalityDashboard;