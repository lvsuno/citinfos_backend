import React from 'react'    // Mise à jour des rubriques pour les municipalités
    const rubriques = [
        { name: 'Accueil', icon: ArtIcon, count: null },
        { name: 'Art', icon: ArtIcon, count: 12 },
        { name: 'Événements', icon: CultureIcon, count: 8 },
        { name: 'Services', icon: EducationIcon, count: 15 },
        { name: 'Commerces', icon: SportIcon, count: 24 },
        { name: 'Communauté', icon: RecognitionIcon, count: 6 },
    ];  Palette as ArtIcon,
    MenuBook as LitteratureIcon,
    Create as PoesieIcon,
    CameraAlt as PhotoIcon,
    History as HistoryIcon,
    SportsFootball as SportIcon,
    TheaterComedy as CultureIcon,
    EmojiEvents as RecognitionIcon,
    Timeline as ChronologyIcon,
    School as EducationIcon,
    AccountBalance as PoliticsIcon,
    Close as CloseIcon,
} from '@mui/icons-material';
import { useMunicipality } from '../contexts/MunicipalityContext';
import MunicipalitySelector from './MunicipalitySelector';
import styles from './Sidebar.module.css';
import logo from '../assets/logo.png';

const Sidebar = ({ activeRubrique, onRubriqueChange, isOpen, onClose, municipalityName }) => {
    const { activeMunicipality } = useMunicipality();

    // Nom à afficher (priorité au prop, sinon contexte)
    const displayName = municipalityName || activeMunicipality?.nom || 'Communauté';
    const rubriques = [
        { name: 'Art', icon: ArtIcon, count: 12 },
        { name: 'Littérature', icon: LitteratureIcon, count: 9 },
        { name: 'Poésie', icon: PoesieIcon, count: 5 },
        { name: 'Photographie', icon: PhotoIcon, count: 18 },
        { name: 'Histoire', icon: HistoryIcon, count: 7 },
        { name: 'Sport', icon: SportIcon, count: 14 },
        { name: 'Culture', icon: CultureIcon, count: 10 },
        { name: 'Reconnaissance', icon: RecognitionIcon, count: 6 },
        { name: 'Chronologie', icon: ChronologyIcon, count: 0 },
        { name: 'Éducation', icon: EducationIcon, count: 0 },
        { name: 'Politique', icon: PoliticsIcon, count: 0 },
    ];

    const handleRubriqueClick = (rubrique) => {
        onRubriqueChange && onRubriqueChange(rubrique);
    };

    return (
        <>
            {/* Overlay pour mobile */}
            {isOpen && <div className={styles.overlay} onClick={onClose} />}

            <div className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
                {/* Bouton fermer pour mobile */}
                <button className={styles.closeButton} onClick={onClose}>
                    <CloseIcon />
                </button>

                {/* Header avec logo et nom */}
                <div className={styles.header}>
                    <div className={styles.logoContainer}>
                        <img
                            src={logo}
                            alt="Logo Communauté"
                            className={styles.logo}
                        />
                        <div>
                            <h1 className={styles.brandName}>Communauté</h1>
                            <p className={styles.cityName}>{activeMunicipality.name}</p>
                        </div>
                    </div>
                </div>

                {/* Sélecteur de municipalité */}
                <MunicipalitySelector />

                {/* Section rubriques */}
                <div className={styles.rubriquesSection}>
                    <h2 className={styles.sectionTitle}>Rubriques de la ville</h2>
                    <ul className={styles.rubriquesList}>
                        {rubriques.map((rubrique) => {
                            const IconComponent = rubrique.icon;
                            const isActive = activeRubrique === rubrique.name;

                            return (
                                <li key={rubrique.name} className={styles.rubriqueItem}>
                                    <div
                                        className={`${styles.rubriqueLink} ${isActive ? styles.active : ''}`}
                                        onClick={() => handleRubriqueClick(rubrique.name)}
                                    >
                                        <div className={styles.rubriqueContent}>
                                            <IconComponent className={styles.rubriqueIcon} />
                                            <span>{rubrique.name}</span>
                                        </div>
                                        <span
                                            className={`${styles.articleCount} ${rubrique.count === 0 ? styles.articleCountZero : ''
                                                }`}
                                        >
                                            {rubrique.count}
                                        </span>
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            </div>
        </>
    );
};

export default Sidebar;