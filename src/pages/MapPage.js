import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMunicipality } from '../contexts/MunicipalityContext';
import { getMunicipalitiesStats, searchMunicipalities } from '../data/municipalitiesUtils';
import Layout from '../components/Layout';
import MunicipalitiesMap from '../components/MunicipalitiesMap';
import {
    Search as SearchIcon,
    LocationOn as LocationIcon,
    People as PeopleIcon,
    Public as PublicIcon,
    TrendingUp as TrendingUpIcon,
    FilterAlt as FilterIcon,
    ArrowForward as ArrowForwardIcon,
    AutoAwesome as AutoAwesomeIcon,
    Explore as ExploreIcon
} from '@mui/icons-material';
import styles from './MapPage.module.css';

const MapPage = () => {
    const { activeMunicipality, getMunicipalitySlug, switchMunicipality } = useMunicipality();
    const [selectedMunicipality, setSelectedMunicipality] = useState(activeMunicipality);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [selectedRegion, setSelectedRegion] = useState('');
    const [stats, setStats] = useState(null);
    const [isVisible, setIsVisible] = useState(false);
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
    const searchInputRef = useRef(null);
    const navigate = useNavigate();

    // Animation d'apparition et suivi de la souris
    useEffect(() => {
        setIsVisible(true);

        const handleMouseMove = (e) => {
            setMousePosition({
                x: (e.clientX / window.innerWidth) * 100,
                y: (e.clientY / window.innerHeight) * 100
            });
        };

        window.addEventListener('mousemove', handleMouseMove);
        return () => window.removeEventListener('mousemove', handleMouseMove);
    }, []);

    // Charger les données statistiques
    useEffect(() => {
        const loadData = () => {
            const municipalitiesStats = getMunicipalitiesStats();
            setStats(municipalitiesStats);
        };

        loadData();
    }, []);

    // Gérer la recherche
    useEffect(() => {
        if (searchQuery.trim()) {
            const results = searchMunicipalities(searchQuery, 5);
            setSearchResults(results);
        } else {
            setSearchResults([]);
        }
    }, [searchQuery]);

    const handleMunicipalitySelect = (municipality) => {
        setSelectedMunicipality(municipality);
        setSearchQuery('');
        setSearchResults([]);
    };

    const handleSearchResultClick = (municipality) => {
        setSelectedMunicipality(municipality);
        setSearchQuery(municipality.nom);
        setSearchResults([]);
    };

    const handleVisitMunicipality = () => {
        if (selectedMunicipality) {
            switchMunicipality(selectedMunicipality.nom);
            const slug = getMunicipalitySlug(selectedMunicipality.nom);
            navigate(`/municipality/${slug}`);
        }
    };

    const handleRegionFilter = (region) => {
        setSelectedRegion(region === selectedRegion ? '' : region);
    };

    const clearSearch = () => {
        setSearchQuery('');
        setSearchResults([]);
        setSelectedMunicipality(null);
    };

    const title = "Explorez le Québec";
    const subtitle = "Découvrez les municipalités du Québec";

    return (
        <Layout
            title={title}
            subtitle={subtitle}
            activeRubrique="carte"
        >
            {/* Arrière-plan animé */}
            <div
                className={styles.animatedBackground}
                style={{
                    background: `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(132, 204, 22, 0.08) 0%, rgba(6, 182, 212, 0.05) 50%, transparent 100%)`
                }}
            />

            <div className={`${styles.mapPageContainer} ${isVisible ? styles.visible : ''}`}>
                {/* Header compact avec recherche intégrée */}
                <div className={styles.compactHeader}>
                    <div className={styles.headerRow}>
                        <div className={styles.titleSection}>
                            <div className={styles.iconContainer}>
                                <ExploreIcon className={styles.titleIcon} />
                            </div>
                            <div className={styles.titleContent}>
                                <h1 className={styles.pageTitle}>Carte Interactive du Québec</h1>
                                <p className={styles.pageSubtitle}>
                                    {stats?.totalMunicipalities || '1100+'} municipalités • {stats?.regions?.length || '17'} régions
                                </p>
                            </div>
                        </div>
                    </div>

                </div>

                {/* Interface principale en grid */}
                <div className={styles.mainInterface}>
                    {/* Section principale avec carte et infos */}
                    <div className={styles.mapArea}>
                        <div className={styles.mapContainer}>
                            <MunicipalitiesMap
                                selectedMunicipality={selectedMunicipality}
                                onMunicipalitySelect={handleMunicipalitySelect}
                                height="500px"
                            />

                            {/* Overlay avec informations */}
                            {selectedMunicipality && (
                                <div className={styles.mapOverlay}>
                                    <div className={styles.quickInfo}>
                                        <div className={styles.quickInfoHeader}>
                                            <LocationIcon className={styles.quickIcon} />
                                            <span className={styles.quickTitle}>{selectedMunicipality.nom}</span>
                                        </div>
                                        <button
                                            className={styles.quickVisitButton}
                                            onClick={handleVisitMunicipality}
                                        >
                                            Visiter
                                            <ArrowForwardIcon className={styles.quickButtonIcon} />
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Panneau latéral compact */}
                    <div className={styles.compactSidebar}>
                        {/* Stats compactes */}
                        {stats && (
                            <div className={styles.compactStatsCard}>
                                <div className={styles.compactCardHeader}>
                                    <TrendingUpIcon className={styles.compactCardIcon} />
                                    <span className={styles.compactCardTitle}>Statistiques</span>
                                </div>
                                <div className={styles.compactStatsGrid}>
                                    <div className={styles.compactStatItem}>
                                        <PublicIcon className={styles.compactStatIcon} />
                                        <div>
                                            <div className={styles.compactStatNumber}>{stats.totalMunicipalities}</div>
                                            <div className={styles.compactStatLabel}>Municipalités</div>
                                        </div>
                                    </div>
                                    <div className={styles.compactStatItem}>
                                        <PeopleIcon className={styles.compactStatIcon} />
                                        <div>
                                            <div className={styles.compactStatNumber}>{(stats.totalPopulation / 1000000).toFixed(1)}M</div>
                                            <div className={styles.compactStatLabel}>Population</div>
                                        </div>
                                    </div>
                                    <div className={styles.compactStatItem}>
                                        <LocationIcon className={styles.compactStatIcon} />
                                        <div>
                                            <div className={styles.compactStatNumber}>{stats.regions.length}</div>
                                            <div className={styles.compactStatLabel}>Régions</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Sélection actuelle */}
                        {selectedMunicipality && (
                            <div className={styles.compactSelectedCard}>
                                <div className={styles.compactCardHeader}>
                                    <LocationIcon className={styles.compactCardIcon} />
                                    <span className={styles.compactCardTitle}>Sélectionné</span>
                                </div>
                                <div className={styles.compactSelectedContent}>
                                    <div className={styles.compactMunicipalityInfo}>
                                        <h4 className={styles.compactMunicipalityName}>{selectedMunicipality.nom}</h4>
                                        <p className={styles.compactMunicipalityRegion}>📍 {selectedMunicipality.region}</p>
                                        {selectedMunicipality.population && (
                                            <p className={styles.compactMunicipalityPop}>
                                                👥 {selectedMunicipality.population.toLocaleString('fr-CA')}
                                            </p>
                                        )}
                                    </div>
                                    <button
                                        className={styles.compactVisitButton}
                                        onClick={handleVisitMunicipality}
                                    >
                                        Explorer
                                        <ArrowForwardIcon className={styles.compactButtonIcon} />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
    {/* Header avec recherche */ }
    <div className={styles.pageHeader}>
        <div className={styles.headerContent}>
            <div className={styles.titleSection}>
                <div className={styles.iconContainer}>
                    <ExploreIcon className={styles.titleIcon} />
                </div>
                <div>
                    <h1 className={styles.pageTitle}>Carte Interactive du Québec</h1>
                    <p className={styles.pageSubtitle}>
                        Explorez {stats?.totalMunicipalities || '1100+'} municipalités
                        réparties dans {stats?.regions?.length || '17'} régions
                    </p>
                </div>
            </div>

            {/* Barre de recherche moderne */}
            <div className={styles.searchSection}>
                <div className={styles.searchWrapper}>
                    <SearchIcon className={styles.searchIcon} />
                    <input
                        ref={searchInputRef}
                        type="text"
                        className={styles.searchInput}
                        placeholder="Rechercher une municipalité..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    {searchQuery && (
                        <button
                            className={styles.clearButton}
                            onClick={clearSearch}
                        >
                            ×
                        </button>
                    )}

                    {/* Résultats de recherche */}
                    {searchResults.length > 0 && (
                        <div className={styles.searchResults}>
                            {searchResults.map((municipality, index) => (
                                <div
                                    key={municipality.nom}
                                    className={styles.searchResultItem}
                                    onClick={() => handleSearchResultClick(municipality)}
                                    style={{ animationDelay: `${index * 0.05}s` }}
                                >
                                    <LocationIcon className={styles.resultIcon} />
                                    <div className={styles.resultInfo}>
                                        <span className={styles.resultName}>{municipality.nom}</span>
                                        <span className={styles.resultRegion}>{municipality.region}</span>
                                    </div>
                                    {municipality.population && (
                                        <span className={styles.resultPopulation}>
                                            {municipality.population.toLocaleString('fr-CA')}
                                        </span>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Filtres par région */}
                {stats?.regions && (
                    <div className={styles.filtersSection}>
                        <FilterIcon className={styles.filterIcon} />
                        <div className={styles.regionFilters}>
                            {stats.regions.slice(0, 6).map((region) => (
                                <button
                                    key={region}
                                    className={`${styles.regionFilter} ${selectedRegion === region ? styles.active : ''}`}
                                    onClick={() => handleRegionFilter(region)}
                                >
                                    {region}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    </div>

    {/* Contenu principal */ }
    <div className={styles.mainContent}>
        {/* Section carte */}
        <div className={styles.mapSection}>
            <div className={styles.mapContainer}>
                <MunicipalitiesMap
                    selectedMunicipality={selectedMunicipality}
                    onMunicipalitySelect={handleMunicipalitySelect}
                    height="600px"
                />

                {/* Overlay avec informations */}
                {selectedMunicipality && (
                    <div className={styles.mapOverlay}>
                        <div className={styles.quickInfo}>
                            <div className={styles.quickInfoHeader}>
                                <LocationIcon className={styles.quickIcon} />
                                <span className={styles.quickTitle}>{selectedMunicipality.nom}</span>
                            </div>
                            <button
                                className={styles.quickVisitButton}
                                onClick={handleVisitMunicipality}
                            >
                                Visiter
                                <ArrowForwardIcon className={styles.quickButtonIcon} />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>

        {/* Sidebar avec statistiques */}
        <div className={styles.sidebarSection}>
            {/* Statistiques générales */}
            {stats && (
                <div className={styles.statsCard}>
                    <div className={styles.cardHeader}>
                        <TrendingUpIcon className={styles.cardIcon} />
                        <h3 className={styles.cardTitle}>Statistiques du Québec</h3>
                    </div>
                    <div className={styles.statsGrid}>
                        <div className={styles.statItem}>
                            <div className={styles.statIcon}>
                                <PublicIcon />
                            </div>
                            <div className={styles.statContent}>
                                <span className={styles.statNumber}>
                                    {stats.totalMunicipalities}
                                </span>
                                <span className={styles.statLabel}>Municipalités</span>
                            </div>
                        </div>
                        <div className={styles.statItem}>
                            <div className={styles.statIcon}>
                                <PeopleIcon />
                            </div>
                            <div className={styles.statContent}>
                                <span className={styles.statNumber}>
                                    {(stats.totalPopulation / 1000000).toFixed(1)}M
                                </span>
                                <span className={styles.statLabel}>Population</span>
                            </div>
                        </div>
                        <div className={styles.statItem}>
                            <div className={styles.statIcon}>
                                <LocationIcon />
                            </div>
                            <div className={styles.statContent}>
                                <span className={styles.statNumber}>
                                    {stats.regions.length}
                                </span>
                                <span className={styles.statLabel}>Régions</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Plus grandes villes */}
            {stats?.largestCities && (
                <div className={styles.topCitiesCard}>
                    <div className={styles.cardHeader}>
                        <AutoAwesomeIcon className={styles.cardIcon} />
                        <h3 className={styles.cardTitle}>Principales Villes</h3>
                    </div>
                    <div className={styles.citiesList}>
                        {stats.largestCities.slice(0, 5).map((city, index) => (
                            <div
                                key={city.nom}
                                className={styles.cityItem}
                                style={{ animationDelay: `${index * 0.1}s` }}
                                onClick={() => handleSearchResultClick(city)}
                            >
                                <div className={styles.cityRank}>#{index + 1}</div>
                                <div className={styles.cityInfo}>
                                    <span className={styles.cityName}>{city.nom}</span>
                                    <span className={styles.cityRegion}>{city.region}</span>
                                </div>
                                <div className={styles.cityPopulation}>
                                    {city.population.toLocaleString('fr-CA')}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Municipalité sélectionnée */}
            {selectedMunicipality && (
                <div className={styles.selectedCard}>
                    <div className={styles.cardHeader}>
                        <LocationIcon className={styles.cardIcon} />
                        <h3 className={styles.cardTitle}>Sélection Actuelle</h3>
                    </div>
                    <div className={styles.selectedContent}>
                        <div className={styles.selectedMunicipality}>
                            <h4 className={styles.municipalityName}>
                                {selectedMunicipality.nom}
                            </h4>
                            <p className={styles.municipalityRegion}>
                                📍 {selectedMunicipality.region}
                            </p>
                            {selectedMunicipality.population && (
                                <p className={styles.municipalityPopulation}>
                                    👥 {selectedMunicipality.population.toLocaleString('fr-CA')} habitants
                                </p>
                            )}
                        </div>
                        <button
                            className={styles.visitButton}
                            onClick={handleVisitMunicipality}
                        >
                            <span>Explorer {selectedMunicipality.nom}</span>
                            <ArrowForwardIcon className={styles.buttonIcon} />
                        </button>
                    </div>
                </div>
            )}

            {/* Guide d'utilisation */}
            <div className={styles.guideCard}>
                <div className={styles.cardHeader}>
                    <ExploreIcon className={styles.cardIcon} />
                    <h3 className={styles.cardTitle}>Guide d'Exploration</h3>
                </div>
                <div className={styles.guideList}>
                    <div className={styles.guideItem}>
                        <span className={styles.guideEmoji}>🔍</span>
                        <span className={styles.guideText}>Utilisez la barre de recherche</span>
                    </div>
                    <div className={styles.guideItem}>
                        <span className={styles.guideEmoji}>📍</span>
                        <span className={styles.guideText}>Cliquez sur les marqueurs</span>
                    </div>
                    <div className={styles.guideItem}>
                        <span className={styles.guideEmoji}>🌿</span>
                        <span className={styles.guideText}>Filtrez par région</span>
                    </div>
                    <div className={styles.guideItem}>
                        <span className={styles.guideEmoji}>🖱️</span>
                        <span className={styles.guideText}>Naviguez avec la souris</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
};

export default MapPage;