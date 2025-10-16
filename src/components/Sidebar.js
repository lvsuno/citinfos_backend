import React from 'react';
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
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useMunicipality } from '../contexts/MunicipalityContext';
import { getCurrentDivision } from '../utils/divisionStorage';
import { getAdminDivisionUrlPath, isValidUrlPath } from '../config/adminDivisions';
import { getDefaultDivisionUrl } from '../utils/defaultDivisionRedirect';
import MunicipalitySelector from './MunicipalitySelector';
import styles from './Sidebar.module.css';
import logo from '../assets/logo.png';

const Sidebar = ({ activeRubrique, onRubriqueChange, isOpen, onClose, municipalityName, pageDivision }) => {
    const { user } = useAuth();
    const { activeMunicipality, getMunicipalitySlug, getAdminLabels } = useMunicipality();
    const navigate = useNavigate();
    const location = useLocation();
    const { municipalitySlug } = useParams();
    
    // État pour contrôler l'expansion des sections
    const [expandedSections, setExpandedSections] = React.useState({
        'nouvelles': false,
        'services': false,
        'culture': false,
        'economie': false,
        'art': false,
        'sports': false,
        'distinction': false,
        'photos-videos': false,
        'participation': false
    });

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

    console.log('📋 Sidebar displayName sources:', {
        pageDivision: pageDivision?.name,
        pageDivisionId: pageDivision?.id,
        municipalityName,
        activeMunicipalityNom: activeMunicipality?.nom,
        activeMunicipalityName: activeMunicipality?.name,
        activeMunicipalityId: activeMunicipality?.id,
        final: displayName
    });

    // Rubriques organisées par catégories selon votre demande
    const rubriquesSections = [
        {
            title: 'Accueil',
            key: 'accueil',
            icon: HomeIcon,
            isMain: true,
            path: 'accueil',
            description: 'Tableau de bord principal'
        },
        {
            title: 'Nouvelles',
            key: 'nouvelles',
            icon: NouvellesIcon,
            items: [
                { name: 'Actualités', path: 'actualites', description: 'Actualités locales' },
                { name: 'Annonces', path: 'annonces', description: 'Annonces officielles' }
            ]
        },
        {
            title: 'Services',
            key: 'services',
            icon: ServicesIcon,
            items: [
                { name: 'Services municipaux', path: 'services', description: 'Services publics' },
                { name: 'Transport', path: 'transport', description: 'Transport et circulation' },
                { name: 'Commerces', path: 'commerces', description: 'Commerce local' }
            ]
        },
        {
            title: 'Culture',
            key: 'culture',
            icon: CultureIcon,
            items: [
                { name: 'Événements culturels', path: 'culture', description: 'Événements culturels' },
                { name: 'Littérature', path: 'litterature', description: 'Œuvres littéraires' },
                { name: 'Poésie', path: 'poesie', description: 'Poèmes et vers' },
                { name: 'Histoire', path: 'histoire', description: 'Patrimoine local' }
            ]
        },
        {
            title: 'Économie',
            key: 'economie',
            icon: EconomieIcon,
            items: [
                { name: 'Développement économique', path: 'economie', description: 'Économie locale' },
                { name: 'Opportunités', path: 'opportunites', description: 'Opportunités d\'affaires' }
            ]
        },
        {
            title: 'Art',
            key: 'art',
            icon: ArtIcon,
            items: [
                { name: 'Créations artistiques', path: 'art', description: 'Créations artistiques' },
                { name: 'Expositions', path: 'expositions', description: 'Expositions d\'art' }
            ]
        },
        {
            title: 'Sports',
            key: 'sports',
            icon: SportsIcon,
            items: [
                { name: 'Activités sportives', path: 'sport', description: 'Activités sportives' },
                { name: 'Événements sportifs', path: 'evenements-sportifs', description: 'Compétitions et événements' }
            ]
        },
        {
            title: 'Distinction',
            key: 'distinction',
            icon: DistinctionIcon,
            items: [
                { name: 'Reconnaissances', path: 'reconnaissance', description: 'Valorisation communautaire' },
                { name: 'Prix et honneurs', path: 'prix', description: 'Prix et distinctions' }
            ]
        },
        {
            title: 'Photos et Vidéos',
            key: 'photos-videos',
            icon: PhotosVideosIcon,
            items: [
                { name: 'Galerie photos', path: 'photographie', description: 'Images et captures' },
                { name: 'Vidéos', path: 'videos', description: 'Contenu vidéo' }
            ]
        },
        {
            title: 'Participation Citoyenne',
            key: 'participation',
            icon: ParticipationIcon,
            items: [
                { name: 'Consultations', path: 'consultations', description: 'Consultations publiques' },
                { name: 'Suggestions', path: 'suggestions', description: 'Boîte à suggestions' },
                { name: 'Événements', path: 'evenements', description: 'Événements participatifs' }
            ]
        }
    ];

    const toggleSection = (sectionKey) => {
        setExpandedSections(prev => ({
            ...prev,
            [sectionKey]: !prev[sectionKey]
        }));
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

    const handleRubriqueClick = async (rubriqueOrPath) => {
        // Si c'est un objet rubrique, utiliser le path, sinon c'est déjà un path
        const path = typeof rubriqueOrPath === 'object' ? rubriqueOrPath.path : rubriqueOrPath;
        
        // Get the current slug from URL or active municipality
        const currentSlug = municipalitySlug || (activeMunicipality ? getMunicipalitySlug(activeMunicipality.nom) : null);

        if (currentSlug) {
            // Navigation vers la section de la municipalité actuelle using dynamic URL path
            navigate(`/${urlPath}/${currentSlug}/${path}`);
        } else {
            // Fallback to user's default division
            const defaultUrl = await getDefaultDivisionUrl(user, null);
            navigate(defaultUrl.replace('/accueil', `/${path}`));
        }

        // Appeler onRubriqueChange si fourni pour la compatibilité
        if (onRubriqueChange) {
            onRubriqueChange(path); // Passer le path au lieu du nom
        }
    };

    return (
        <>
            {/* Overlay pour mobile */}
            {isOpen && <div className={styles.overlay} onClick={onClose} />}

            {/* Sidebar */}
            <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
                <div className={styles.sidebarHeader}>
                    {/* Bouton fermer (mobile) */}
                    <button className={styles.closeButton} onClick={onClose}>
                        <CloseIcon />
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
                    <ul className={styles.rubriquesList}>
                        {rubriquesSections.map((section, index) => {
                            const Icon = section.icon;
                            const currentPath = activeRubrique?.toLowerCase();
                            
                            // Section principale (Accueil)
                            if (section.isMain) {
                                const isActive = currentPath === section.path.toLowerCase();
                                return (
                                    <li key={index} className={styles.rubriqueItem}>
                                        <button
                                            className={`${styles.rubriqueButton} ${isActive ? styles.active : ''}`}
                                            onClick={() => handleRubriqueClick(section.path)}
                                            title={section.description}
                                        >
                                            <Icon className={styles.rubriqueIcon} />
                                            <span className={styles.rubriqueName}>{section.title}</span>
                                        </button>
                                    </li>
                                );
                            }

                            // Sections avec sous-éléments
                            const isExpanded = expandedSections[section.key];
                            const hasActiveChild = section.items?.some(item => 
                                currentPath === item.path.toLowerCase()
                            );

                            return (
                                <li key={index} className={styles.rubriqueItem}>
                                    {/* En-tête de section */}
                                    <button
                                        className={`${styles.rubriqueButton} ${styles.sectionHeader} ${hasActiveChild ? styles.hasActiveChild : ''}`}
                                        onClick={() => toggleSection(section.key)}
                                        title={`${isExpanded ? 'Réduire' : 'Développer'} la section ${section.title}`}
                                    >
                                        <Icon className={styles.rubriqueIcon} />
                                        <span className={styles.rubriqueName}>{section.title}</span>
                                        {isExpanded ? 
                                            <ExpandLessIcon className={styles.expandIcon} /> : 
                                            <ExpandMoreIcon className={styles.expandIcon} />
                                        }
                                    </button>

                                    {/* Sous-éléments */}
                                    {isExpanded && section.items && (
                                        <ul className={styles.subItems}>
                                            {section.items.map((item, itemIndex) => {
                                                const isActive = currentPath === item.path.toLowerCase();
                                                return (
                                                    <li key={itemIndex} className={styles.subItem}>
                                                        <button
                                                            className={`${styles.subItemButton} ${isActive ? styles.active : ''}`}
                                                            onClick={() => handleRubriqueClick(item.path)}
                                                            title={item.description}
                                                        >
                                                            <span className={styles.subItemName}>{item.name}</span>
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