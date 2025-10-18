import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import {
    Home as HomeIcon,
    Newspaper as NouvellesIcon,
    RoomService as ServicesIcon,
    TheaterComedy as CultureIcon,
    Business as EconomieIcon,
    Palette as ArtIcon,
    Sports as SportsIcon,
    EmojiEvents as DistinctionIcon,
    PhotoCamera as PhotosVideosIcon,
    HowToVote as ParticipationIcon,
    Map as MapIcon,
    Close as CloseIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandLess as ExpandLessIcon,
    ChevronLeft as ChevronLeftIcon,
    ChevronRight as ChevronRightIcon,
    // Child rubrique icons
    FiberNew,
    Campaign,
    AccountBalance,
    DirectionsBus,
    Storefront,
    Event,
    MenuBook,
    AutoStories,
    HistoryEdu,
    WorkOutline,
    Brush,
    Museum,
    DirectionsRun,
    CardGiftcard,
    MilitaryTech,
    PhotoLibrary,
    VideoLibrary,
    QuestionAnswer,
    Lightbulb,
    CalendarToday,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useMunicipality } from '../contexts/MunicipalityContext';
import { getCurrentDivision } from '../utils/divisionStorage';
import { getAdminDivisionUrlPath, isValidUrlPath } from '../config/adminDivisions';
import { getDefaultDivisionUrl } from '../utils/defaultDivisionRedirect';
import communityAPI from '../services/communityAPI';
import MunicipalitySelector from './MunicipalitySelector';
import styles from './Sidebar.module.css';
import logo from '../assets/logo.png';

const Sidebar = ({ activeRubrique, onRubriqueChange, isOpen, isCollapsed, onClose, onToggle, onToggleCollapse, municipalityName, pageDivision }) => {
    const { user } = useAuth();
    const { activeMunicipality, getMunicipalitySlug, getAdminLabels } = useMunicipality();
    const navigate = useNavigate();
    const location = useLocation();
    const { municipalitySlug } = useParams();

    // State for dynamic rubriques
    const [rubriques, setRubriques] = useState([]);
    const [loadingRubriques, setLoadingRubriques] = useState(true);
    const [expandedRubriques, setExpandedRubriques] = useState(new Set());

    // Detect current URL path (municipality, commune, city, etc.)
    const currentUrlPath = location.pathname.split('/')[1];
    const isCurrentPathValid = isValidUrlPath(currentUrlPath);

    // Use current URL path if valid, otherwise use default
    const urlPath = isCurrentPathValid ? currentUrlPath : getAdminDivisionUrlPath();

    // Obtenir les libellés adaptés à la division administrative
    const adminLabels = getAdminLabels();

    // Nom à afficher - PRIORITY: pageDivision from URL, then municipalityName prop, then context, then localStorage
    let displayName = pageDivision?.name || municipalityName || activeMunicipality?.nom || activeMunicipality?.name;

    // If still no name, check localStorage directly as last resort before fallback
    if (!displayName) {
        const currentDivision = getCurrentDivision();
        displayName = currentDivision?.name || adminLabels.singular;
    }

    // Material-UI icon mapping - maps backend icon names to actual icon components
    const muiIconMap = {
        // Parent section icons
        'Home': HomeIcon,
        'Newspaper': NouvellesIcon,
        'RoomService': ServicesIcon,
        'TheaterComedy': CultureIcon,
        'Business': EconomieIcon,
        'Palette': ArtIcon,
        'Sports': SportsIcon,
        'EmojiEvents': DistinctionIcon,
        'PhotoCamera': PhotosVideosIcon,
        'HowToVote': ParticipationIcon,
        // Child rubrique icons
        'FiberNew': FiberNew,
        'Campaign': Campaign,
        'AccountBalance': AccountBalance,
        'DirectionsBus': DirectionsBus,
        'Storefront': Storefront,
        'Event': Event,
        'MenuBook': MenuBook,
        'AutoStories': AutoStories,
        'HistoryEdu': HistoryEdu,
        'WorkOutline': WorkOutline,
        'Brush': Brush,
        'Museum': Museum,
        'DirectionsRun': DirectionsRun,
        'CardGiftcard': CardGiftcard,
        'MilitaryTech': MilitaryTech,
        'PhotoLibrary': PhotoLibrary,
        'VideoLibrary': VideoLibrary,
        'QuestionAnswer': QuestionAnswer,
        'Lightbulb': Lightbulb,
        'CalendarToday': CalendarToday,
    };

    // Fetch enabled rubriques for the current community
    useEffect(() => {
        const fetchRubriques = async () => {
            // Get the current community slug
            const currentSlug = municipalitySlug || (activeMunicipality ? getMunicipalitySlug(activeMunicipality.nom) : null);

            if (!currentSlug) {
                // No community selected, use default rubriques
                setRubriques(getDefaultRubriques());
                setLoadingRubriques(false);
                return;
            }

            setLoadingRubriques(true);
            try {
                const data = await communityAPI.getEnabledRubriques(currentSlug);

                // Transform API data to component format - all rubriques come from backend now
                const formattedRubriques = transformRubriquesToFormat(data.rubriques || []);

                console.log('📊 Formatted Rubriques:', formattedRubriques);
                console.log('🔍 First rubrique details:', formattedRubriques[0]);

                setRubriques(formattedRubriques);
            } catch (error) {
                console.error('Error loading rubriques:', error);
                // Fallback to default rubriques on error
                setRubriques(getDefaultRubriques());
            } finally {
                setLoadingRubriques(false);
            }
        };

        fetchRubriques();
    }, [municipalitySlug, activeMunicipality, getMunicipalitySlug]);

    // Transform API rubrique data to component format
    const transformRubriquesToFormat = (apiRubriques) => {
        console.log('🔄 Transforming rubriques:', apiRubriques);

        return apiRubriques.map(rubrique => {
            // Use the icon name from backend to get the actual MUI icon component
            const IconComponent = muiIconMap[rubrique.icon] || HomeIcon;

            const transformed = {
                id: rubrique.id,
                name: rubrique.name,
                icon: IconComponent,
                path: rubrique.template_type,
                description: rubrique.description || rubrique.name,
                depth: rubrique.depth || 0,
                required: rubrique.required || false,
                isExpandable: rubrique.isExpandable || false,
                children: rubrique.children ? transformRubriquesToFormat(rubrique.children) : []
            };

            console.log('📦 Transformed rubrique:', {
                name: transformed.name,
                isExpandable: transformed.isExpandable,
                childrenCount: transformed.children.length,
                children: transformed.children.map(c => c.name)
            });

            return transformed;
        });
    };

    // Get default rubriques (fallback)
    const getDefaultRubriques = () => {
        return [
            { name: 'Accueil', icon: HomeIcon, count: null, path: 'accueil', description: 'Tableau de bord principal', depth: 0, isExpandable: false, children: [] },
            { name: 'Actualités', icon: FiberNew, count: null, path: 'actualites', description: 'Actualités locales', depth: 0, isExpandable: false, children: [] },
            { name: 'Événements', icon: Event, count: null, path: 'evenements', description: 'Événements et festivités', depth: 0, isExpandable: false, children: [] },
            { name: 'Commerces', icon: Storefront, count: null, path: 'commerces', description: 'Commerce local', depth: 0, isExpandable: false, children: [] },
        ];
    };

    // Navigation spéciale pour la carte (au niveau global)
    const handleMapClick = () => {
        // If we're viewing a specific division, pass it as query param to show it on the map
        if (pageDivision?.id) {
            navigate(`/carte?division=${pageDivision.id}`);
        } else {
            // Otherwise, open general exploration map
            navigate('/carte-municipalites');
        }
    };

    const handleRubriqueClick = async (rubrique) => {
        // Get the current slug from URL or active municipality
        const currentSlug = municipalitySlug || (activeMunicipality ? getMunicipalitySlug(activeMunicipality.nom) : null);

        if (currentSlug) {
            // Navigation vers la section de la municipalité actuelle using dynamic URL path
            navigate(`/${urlPath}/${currentSlug}/${rubrique.path}`);
        } else {
            // Fallback to user's default division
            const defaultUrl = await getDefaultDivisionUrl(user, null);
            navigate(defaultUrl.replace('/accueil', `/${rubrique.path}`));
        }

        // Appeler onRubriqueChange si fourni pour la compatibilité
        if (onRubriqueChange) {
            onRubriqueChange(rubrique.path); // Passer le path au lieu du nom
        }
    };

    // Toggle expand/collapse for a rubrique
    const toggleRubrique = (rubriqueId) => {
        setExpandedRubriques(prev => {
            const next = new Set(prev);
            if (next.has(rubriqueId)) {
                next.delete(rubriqueId);
            } else {
                next.add(rubriqueId);
            }
            return next;
        });
    };

    return (
        <>
            {/* Overlay pour mobile */}
            {isOpen && <div className={styles.overlay} onClick={onClose} />}

            {/* Sidebar */}
            <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''} ${isCollapsed ? styles.collapsed : ''}`}>
                <div className={styles.sidebarHeader}>
                    {/* Mobile close button */}
                    <button className={`${styles.closeButton} ${styles.mobileOnly}`} onClick={onClose}>
                        <CloseIcon />
                    </button>

                    {/* Desktop collapse/expand button */}
                    <button
                        className={`${styles.collapseButton} ${styles.desktopOnly}`}
                        onClick={onToggleCollapse}
                        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        {isCollapsed ? <ChevronRightIcon /> : <ChevronLeftIcon />}
                    </button>

                    {/* Logo et titre */}
                    <div className={styles.logoContainer}>
                        <img src={logo} alt="Logo" className={styles.logo} />
                        <div className={styles.titleContainer}>
                            <h2 className={styles.mainTitle}>Communauté</h2>
                            <h3 className={styles.municipalityTitle}>{displayName}</h3>
                        </div>
                    </div>
                </div>

                {/* Sélecteur de municipalité */}
                <div className={styles.municipalitySection}>
                    <MunicipalitySelector currentPageDivision={pageDivision} />

                    {/* Bouton Carte des divisions administratives (exploration générale) */}
                    <button
                        className={`${styles.rubriqueButton} ${styles.mapButton}`}
                        onClick={handleMapClick}
                        title={`Explorer toutes les ${adminLabels.plural} sur une carte interactive`}
                    >
                        <MapIcon className={styles.rubriqueIcon} />
                        <span className={styles.rubriqueName}>{adminLabels.mapTitle}</span>
                    </button>
                </div>

                {/* Navigation des rubriques */}
                <nav className={styles.navigation}>
                    <h3 className={styles.navTitle}>Rubriques</h3>
                    {loadingRubriques ? (
                        <div className={styles.loadingContainer}>
                            <p className={styles.loadingText}>Chargement...</p>
                        </div>
                    ) : (
                        <ul className={styles.rubriquesList}>
                            {rubriques.map((rubrique, index) => {
                                const Icon = rubrique.icon;
                                const currentPath = activeRubrique?.toLowerCase();
                                const rubriquerPath = rubrique.path.toLowerCase();
                                const isActive = currentPath === rubriquerPath;
                                const isExpanded = expandedRubriques.has(rubrique.id);

                                // Debug log for first rubrique
                                if (index === 0) {
                                    console.log('🎯 First rubrique render:', {
                                        name: rubrique.name,
                                        isExpandable: rubrique.isExpandable,
                                        hasChildren: rubrique.children?.length > 0,
                                        childrenCount: rubrique.children?.length,
                                        isExpanded,
                                        expandedSet: Array.from(expandedRubriques)
                                    });
                                }

                                return (
                                    <li key={rubrique.id || index} className={styles.rubriqueItem}>
                                        <button
                                            className={`${styles.rubriqueButton} ${isActive ? styles.active : ''} ${rubrique.depth > 0 ? styles.subRubrique : ''}`}
                                            onClick={() => {
                                                if (rubrique.isExpandable) {
                                                    toggleRubrique(rubrique.id);
                                                } else {
                                                    handleRubriqueClick(rubrique);
                                                }
                                            }}
                                            title={rubrique.description}
                                        >
                                            <Icon className={styles.rubriqueIcon} />
                                            <span className={styles.rubriqueName}>
                                                {rubrique.depth > 0 && '└ '}
                                                {rubrique.name}
                                            </span>
                                            {rubrique.count && (
                                                <span className={styles.rubriqueCount}>{rubrique.count}</span>
                                            )}
                                            {rubrique.isExpandable && (
                                                <span className={styles.expandIcon}>
                                                    {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                                                </span>
                                            )}
                                        </button>

                                        {/* Render children only if expandable and expanded */}
                                        {rubrique.isExpandable && isExpanded && rubrique.children && rubrique.children.length > 0 && (
                                            <ul className={styles.subRubriquesList}>
                                                {rubrique.children.map((child, childIndex) => {
                                                    const ChildIcon = child.icon;
                                                    const childPath = child.path.toLowerCase();
                                                    const isChildActive = currentPath === childPath;

                                                    return (
                                                        <li key={child.id || childIndex} className={styles.rubriqueItem}>
                                                            <button
                                                                className={`${styles.rubriqueButton} ${styles.subRubrique} ${isChildActive ? styles.active : ''}`}
                                                                onClick={() => handleRubriqueClick(child)}
                                                                title={child.description}
                                                            >
                                                                <ChildIcon className={styles.rubriqueIcon} />
                                                                <span className={styles.rubriqueName}>
                                                                    └ {child.name}
                                                                </span>
                                                            </button>
                                                        </li>
                                                    );
                                                })}
                                            </ul>
                                        )}
                                    </li>
                                );
                            })}
                        </ul>
                    )}
                </nav>

                {/* Footer de la sidebar */}
                <div className={styles.sidebarFooter}>
                    <p className={styles.footerText}>
                        Plateforme communautaire pour {displayName}
                    </p>
                    <p className={styles.footerVersion}>v1.0.0</p>
                </div>
            </aside>
        </>
    );
};

export default Sidebar;