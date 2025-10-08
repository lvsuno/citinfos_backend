import React from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import {
    Home as HomeIcon,
    Palette as ArtIcon,
    MenuBook as LitteratureIcon,
    Create as PoesieIcon,
    PhotoCamera as PhotoIcon,
    History as HistoireIcon,
    Sports as SportIcon,
    TheaterComedy as CultureIcon,
    EmojiEvents as ReconnaissanceIcon,
    Timeline as ChronologieIcon,
    Event as EventIcon,
    DirectionsBus as TransportIcon,
    Business as CommerceIcon,
    LocationCity as CentreVilleIcon,
    Map as MapIcon,
    MyLocation as MyLocationIcon,
    Close as CloseIcon,
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

    // Rubriques pour la communauté - mix culturel et pratique
    const rubriques = [
        { name: 'Accueil', icon: HomeIcon, count: null, path: 'accueil', description: 'Tableau de bord principal' },
        { name: 'Actualités', icon: CentreVilleIcon, count: null, path: 'actualites', description: 'Actualités locales' },
        { name: 'Événements', icon: EventIcon, count: null, path: 'evenements', description: 'Événements et festivités' },
        { name: 'Transport', icon: TransportIcon, count: null, path: 'transport', description: 'Transport et circulation' },
        { name: 'Commerces', icon: CommerceIcon, count: null, path: 'commerces', description: 'Commerce local' },
        { name: 'Art', icon: ArtIcon, count: null, path: 'art', description: 'Créations artistiques' },
        { name: 'Littérature', icon: LitteratureIcon, count: null, path: 'litterature', description: 'Œuvres littéraires' },
        { name: 'Poésie', icon: PoesieIcon, count: null, path: 'poesie', description: 'Poèmes et vers' },
        { name: 'Photographie', icon: PhotoIcon, count: null, path: 'photographie', description: 'Images et captures' },
        { name: 'Histoire', icon: HistoireIcon, count: null, path: 'histoire', description: 'Patrimoine local' },
        { name: 'Sport', icon: SportIcon, count: null, path: 'sport', description: 'Activités sportives' },
        { name: 'Culture', icon: CultureIcon, count: null, path: 'culture', description: 'Événements culturels' },
        { name: 'Reconnaissance', icon: ReconnaissanceIcon, count: null, path: 'reconnaissance', description: 'Valorisation communautaire' },
        { name: 'Chronologie', icon: ChronologieIcon, count: null, path: 'chronologie', description: 'Timeline des événements' },
    ];

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
                        {rubriques.map((rubrique, index) => {
                            const Icon = rubrique.icon;
                            // Logique améliorée pour comparer les rubriques actives
                            const currentPath = activeRubrique?.toLowerCase();
                            const rubriquerPath = rubrique.path.toLowerCase();
                            const isActive = currentPath === rubriquerPath;

                            return (
                                <li key={index} className={styles.rubriqueItem}>
                                    <button
                                        className={`${styles.rubriqueButton} ${isActive ? styles.active : ''}`}
                                        onClick={() => handleRubriqueClick(rubrique)}
                                        title={rubrique.description}
                                    >
                                        <Icon className={styles.rubriqueIcon} />
                                        <span className={styles.rubriqueName}>{rubrique.name}</span>
                                        {rubrique.count && (
                                            <span className={styles.rubriqueCount}>{rubrique.count}</span>
                                        )}
                                    </button>
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