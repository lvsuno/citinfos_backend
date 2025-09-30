import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getAllMunicipalities, getMunicipalityBySlug, getUserRedirectUrl } from '../data/municipalitiesUtils';
import Layout from '../components/Layout';
import MunicipalitiesMap from '../components/MunicipalitiesMap';
import styles from './MapPage.module.css';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import PeopleIcon from '@mui/icons-material/People';
import BusinessIcon from '@mui/icons-material/Business';
import HomeIcon from '@mui/icons-material/Home';
import CloseIcon from '@mui/icons-material/Close';
import TuneIcon from '@mui/icons-material/Tune';
import ViewListIcon from '@mui/icons-material/ViewList';
import MapIcon from '@mui/icons-material/Map';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ExploreIcon from '@mui/icons-material/Explore';

const MapPage = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const mapRef = useRef(null);

    // États pour l'interface
    const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');
    const [selectedRegion, setSelectedRegion] = useState(searchParams.get('region') || '');
    const [selectedMunicipality, setSelectedMunicipality] = useState(null);
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [viewMode, setViewMode] = useState('map'); // 'map' ou 'list'
    const [sortBy, setSortBy] = useState('name');
    const [sortOrder, setSortOrder] = useState('asc');
    const [showSearchResults, setShowSearchResults] = useState(false);

    // Données des municipalités
    const municipalities = getAllMunicipalities();

    // Régions uniques pour le filtre
    const regions = useMemo(() => {
        const uniqueRegions = [...new Set(municipalities.map(m => m.region).filter(Boolean))];
        return uniqueRegions.sort();
    }, [municipalities]);

    // Municipalités filtrées
    const filteredMunicipalities = useMemo(() => {
        let filtered = municipalities;

        // Filtre par terme de recherche
        if (searchTerm) {
            filtered = filtered.filter(municipality =>
                (municipality.name && municipality.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
                (municipality.region && municipality.region.toLowerCase().includes(searchTerm.toLowerCase()))
            );
        }

        // Filtre par région
        if (selectedRegion) {
            filtered = filtered.filter(municipality => municipality.region === selectedRegion);
        }

        // Tri
        filtered.sort((a, b) => {
            let aValue, bValue;

            switch (sortBy) {
                case 'population':
                    aValue = a.population || 0;
                    bValue = b.population || 0;
                    break;
                case 'region':
                    aValue = a.region || '';
                    bValue = b.region || '';
                    break;
                default:
                    aValue = a.name || '';
                    bValue = b.name || '';
            }

            if (typeof aValue === 'string') {
                return sortOrder === 'asc'
                    ? aValue.localeCompare(bValue)
                    : bValue.localeCompare(aValue);
            } else {
                return sortOrder === 'asc'
                    ? aValue - bValue
                    : bValue - aValue;
            }
        });

        return filtered;
    }, [municipalities, searchTerm, selectedRegion, sortBy, sortOrder]);

    // Résultats de recherche pour l'autocomplétion
    const searchResults = useMemo(() => {
        if (!searchTerm || searchTerm.length < 2) return [];
        return filteredMunicipalities.slice(0, 8);
    }, [searchTerm, filteredMunicipalities]);

    // Statistiques calculées
    const stats = useMemo(() => {
        const totalPopulation = filteredMunicipalities.reduce((sum, m) => sum + (m.population || 0), 0);
        const totalMunicipalities = filteredMunicipalities.length;
        const regionsCount = new Set(filteredMunicipalities.map(m => m.region).filter(Boolean)).size;
        const averagePopulation = totalMunicipalities > 0 ? Math.round(totalPopulation / totalMunicipalities) : 0;
        
        return {
            totalMunicipalities,
            totalPopulation,
            regionsCount,
            averagePopulation
        };
    }, [filteredMunicipalities]);

    // Top municipalités par population
    const topMunicipalities = useMemo(() => {
        return [...municipalities]
            .filter(m => m.population && m.population > 0)
            .sort((a, b) => (b.population || 0) - (a.population || 0))
            .slice(0, 5);
    }, [municipalities]);

    // Gestion des événements
    useEffect(() => {
        const municipalitySlug = searchParams.get('municipality');
        if (municipalitySlug) {
            const municipality = getMunicipalityBySlug(municipalitySlug);
            if (municipality) {
                setSelectedMunicipality(municipality);
            }
        }
    }, [searchParams]);

    useEffect(() => {
        const newParams = new URLSearchParams();
        if (searchTerm) newParams.set('search', searchTerm);
        if (selectedRegion) newParams.set('region', selectedRegion);
        if (selectedMunicipality) newParams.set('municipality', selectedMunicipality.slug);
        setSearchParams(newParams);
    }, [searchTerm, selectedRegion, selectedMunicipality, setSearchParams]);

    const handleMunicipalityClick = (municipality) => {
        setSelectedMunicipality(municipality);
        setShowSearchResults(false);
        if (mapRef.current && mapRef.current.focusOnMunicipality) {
            mapRef.current.focusOnMunicipality(municipality);
        }
    };

    const handleMunicipalitySelect = (municipality) => {
        if (user) {
            const redirectUrl = getUserRedirectUrl(municipality, user);
            navigate(redirectUrl);
        } else {
            navigate(`/municipality/${municipality.slug}`);
        }
    };

    const clearFilters = () => {
        setSearchTerm('');
        setSelectedRegion('');
        setSelectedMunicipality(null);
        setIsFilterOpen(false);
        setShowSearchResults(false);
    };

    const formatNumber = (num) => {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
        return num.toString();
    };

    return (
        <Layout>
            <div className={styles.modernMapPage}>
                {/* Hero Section */}
                <div className={styles.heroSection}>
                    <div className={styles.heroContent}>
                        <div className={styles.heroTitle}>
                            <ExploreIcon className={styles.heroIcon} />
                            <div>
                                <h1>Explorez le Québec</h1>
                                <p>Découvrez les municipalités et leurs communautés</p>
                            </div>
                        </div>
                        
                        {/* Recherche avancée */}
                        <div className={styles.searchContainer}>
                            <div className={styles.searchBox}>
                                <SearchIcon className={styles.searchIcon} />
                                <input
                                    type="text"
                                    placeholder="Rechercher une municipalité..."
                                    value={searchTerm}
                                    onChange={(e) => {
                                        setSearchTerm(e.target.value);
                                        setShowSearchResults(e.target.value.length >= 2);
                                    }}
                                    onFocus={() => setShowSearchResults(searchTerm.length >= 2)}
                                    className={styles.searchInput}
                                />
                                {searchTerm && (
                                    <button 
                                        onClick={() => {
                                            setSearchTerm('');
                                            setShowSearchResults(false);
                                        }}
                                        className={styles.clearSearchButton}
                                    >
                                        <CloseIcon />
                                    </button>
                                )}
                                
                                {/* Résultats de recherche */}
                                {showSearchResults && searchResults.length > 0 && (
                                    <div className={styles.searchDropdown}>
                                        {searchResults.map((municipality, index) => (
                                            <div
                                                key={municipality.id || index}
                                                className={styles.searchResultItem}
                                                onClick={() => handleMunicipalityClick(municipality)}
                                            >
                                                <LocationOnIcon className={styles.resultIcon} />
                                                <div className={styles.resultInfo}>
                                                    <span className={styles.resultName}>{municipality.name}</span>
                                                    <span className={styles.resultRegion}>{municipality.region}</span>
                                                    {municipality.population && (
                                                        <span className={styles.resultPop}>
                                                            {formatNumber(municipality.population)} hab.
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                            
                            <button
                                onClick={() => setIsFilterOpen(!isFilterOpen)}
                                className={`${styles.filterToggle} ${isFilterOpen ? styles.active : ''}`}
                            >
                                <TuneIcon />
                                Filtres
                            </button>
                        </div>

                        {/* Panel de filtres */}
                        {isFilterOpen && (
                            <div className={styles.filtersPanel}>
                                <div className={styles.filtersGrid}>
                                    <div className={styles.filterGroup}>
                                        <label>Région</label>
                                        <select
                                            value={selectedRegion}
                                            onChange={(e) => setSelectedRegion(e.target.value)}
                                            className={styles.filterSelect}
                                        >
                                            <option value="">Toutes les régions</option>
                                            {regions.map(region => (
                                                <option key={region} value={region}>{region}</option>
                                            ))}
                                        </select>
                                    </div>
                                    
                                    <div className={styles.filterGroup}>
                                        <label>Vue</label>
                                        <div className={styles.viewToggle}>
                                            <button
                                                onClick={() => setViewMode('map')}
                                                className={`${styles.viewButton} ${viewMode === 'map' ? styles.active : ''}`}
                                            >
                                                <MapIcon />
                                                Carte
                                            </button>
                                            <button
                                                onClick={() => setViewMode('list')}
                                                className={`${styles.viewButton} ${viewMode === 'list' ? styles.active : ''}`}
                                            >
                                                <ViewListIcon />
                                                Liste
                                            </button>
                                        </div>
                                    </div>

                                    {(searchTerm || selectedRegion) && (
                                        <div className={styles.filterGroup}>
                                            <button onClick={clearFilters} className={styles.clearFilters}>
                                                <CloseIcon />
                                                Effacer
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Statistiques rapides */}
                        <div className={styles.quickStats}>
                            <div className={styles.statCard}>
                                <LocationOnIcon />
                                <div>
                                    <span className={styles.statNumber}>{stats.totalMunicipalities}</span>
                                    <span className={styles.statLabel}>Municipalités</span>
                                </div>
                            </div>
                            <div className={styles.statCard}>
                                <PeopleIcon />
                                <div>
                                    <span className={styles.statNumber}>{formatNumber(stats.totalPopulation)}</span>
                                    <span className={styles.statLabel}>Habitants</span>
                                </div>
                            </div>
                            <div className={styles.statCard}>
                                <BusinessIcon />
                                <div>
                                    <span className={styles.statNumber}>{stats.regionsCount}</span>
                                    <span className={styles.statLabel}>Régions</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Contenu principal */}
                <div className={styles.mainContent}>
                    <div className={styles.contentGrid}>
                        {/* Zone principale - Carte ou Liste */}
                        <div className={styles.primaryContent}>
                            {viewMode === 'map' ? (
                                <div className={styles.mapWrapper}>
                                    <MunicipalitiesMap
                                        ref={mapRef}
                                        municipalities={filteredMunicipalities}
                                        selectedMunicipality={selectedMunicipality}
                                        onMunicipalityClick={handleMunicipalityClick}
                                        searchTerm={searchTerm}
                                    />
                                </div>
                            ) : (
                                <div className={styles.listView}>
                                    <div className={styles.listHeader}>
                                        <h3>Municipalités ({filteredMunicipalities.length})</h3>
                                    </div>
                                    <div className={styles.municipalitiesList}>
                                        {filteredMunicipalities.map((municipality, index) => (
                                            <div 
                                                key={municipality.id || index}
                                                className={styles.municipalityCard}
                                                onClick={() => handleMunicipalityClick(municipality)}
                                            >
                                                <div className={styles.cardHeader}>
                                                    <LocationOnIcon />
                                                    <div>
                                                        <h4>{municipality.name}</h4>
                                                        <p>{municipality.region}</p>
                                                    </div>
                                                </div>
                                                {municipality.population && (
                                                    <div className={styles.cardStats}>
                                                        <PeopleIcon />
                                                        <span>{formatNumber(municipality.population)} hab.</span>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Sidebar */}
                        <div className={styles.sidebar}>
                            {/* Top municipalités */}
                            <div className={styles.sidebarCard}>
                                <div className={styles.cardTitle}>
                                    <TrendingUpIcon />
                                    <h3>Plus populaires</h3>
                                </div>
                                <div className={styles.topMunicipalities}>
                                    {topMunicipalities.map((municipality, index) => (
                                        <div 
                                            key={municipality.id || index}
                                            className={styles.topMunicipalityItem}
                                            onClick={() => handleMunicipalityClick(municipality)}
                                        >
                                            <div className={styles.rank}>#{index + 1}</div>
                                            <div className={styles.municipalityInfo}>
                                                <span className={styles.name}>{municipality.name}</span>
                                                <span className={styles.population}>
                                                    {formatNumber(municipality.population)} hab.
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Municipalité sélectionnée */}
                            {selectedMunicipality && (
                                <div className={styles.selectedCard}>
                                    <div className={styles.selectedHeader}>
                                        <h3>{selectedMunicipality.name}</h3>
                                        <button
                                            onClick={() => setSelectedMunicipality(null)}
                                            className={styles.closeButton}
                                        >
                                            <CloseIcon />
                                        </button>
                                    </div>
                                    
                                    <div className={styles.selectedDetails}>
                                        <p className={styles.region}>{selectedMunicipality.region}</p>
                                        
                                        <div className={styles.selectedStats}>
                                            {selectedMunicipality.population && (
                                                <div className={styles.selectedStat}>
                                                    <PeopleIcon />
                                                    <div>
                                                        <span>{selectedMunicipality.population.toLocaleString()}</span>
                                                        <span>habitants</span>
                                                    </div>
                                                </div>
                                            )}
                                            {selectedMunicipality.dwellings && (
                                                <div className={styles.selectedStat}>
                                                    <HomeIcon />
                                                    <div>
                                                        <span>{selectedMunicipality.dwellings.toLocaleString()}</span>
                                                        <span>logements</span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        
                                        <button
                                            onClick={() => handleMunicipalitySelect(selectedMunicipality)}
                                            className={styles.visitButton}
                                        >
                                            <LocationOnIcon />
                                            Visiter la communauté
                                        </button>
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

export default MapPage;

    // Régions uniques pour le filtre
    const regions = useMemo(() => {
        const uniqueRegions = [...new Set(municipalities.map(m => m.region).filter(Boolean))];
        return uniqueRegions.sort();
    }, [municipalities]);

    // Municipalités filtrées
    const filteredMunicipalities = useMemo(() => {
        let filtered = municipalities;

        // Filtre par terme de recherche
        if (searchTerm) {
            filtered = filtered.filter(municipality =>
                (municipality.name && municipality.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
                (municipality.region && municipality.region.toLowerCase().includes(searchTerm.toLowerCase()))
            );
        }

        // Filtre par région
        if (selectedRegion) {
            filtered = filtered.filter(municipality => municipality.region === selectedRegion);
        }

        // Tri
        filtered.sort((a, b) => {
            let aValue, bValue;

            switch (sortBy) {
                case 'population':
                    aValue = a.population || 0;
                    bValue = b.population || 0;
                    break;
                case 'region':
                    aValue = a.region || '';
                    bValue = b.region || '';
                    break;
                default:
                    aValue = a.name || '';
                    bValue = b.name || '';
            }

            if (typeof aValue === 'string') {
                return sortOrder === 'asc'
                    ? aValue.localeCompare(bValue)
                    : bValue.localeCompare(aValue);
            } else {
                return sortOrder === 'asc'
                    ? aValue - bValue
                    : bValue - aValue;
            }
        });

        return filtered;
    }, [municipalities, searchTerm, selectedRegion, sortBy, sortOrder]);

    // Statistiques calculées
    const stats = useMemo(() => {
        const totalPopulation = filteredMunicipalities.reduce((sum, m) => sum + (m.population || 0), 0);
        const totalMunicipalities = filteredMunicipalities.length;
        const regionsCount = new Set(filteredMunicipalities.map(m => m.region).filter(Boolean)).size;

        return {
            totalMunicipalities,
            totalPopulation,
            regionsCount,
            averagePopulation: totalMunicipalities > 0 ? Math.round(totalPopulation / totalMunicipalities) : 0
        };
    }, [filteredMunicipalities]);

    // Gestion de la municipalité sélectionnée
    useEffect(() => {
        const municipalitySlug = searchParams.get('municipality');
        if (municipalitySlug) {
            const municipality = getMunicipalityBySlug(municipalitySlug);
            if (municipality) {
                setSelectedMunicipality(municipality);
            }
        }
    }, [searchParams]);

    // Gestion des paramètres URL
    useEffect(() => {
        const newParams = new URLSearchParams();

        if (searchTerm) newParams.set('search', searchTerm);
        if (selectedRegion) newParams.set('region', selectedRegion);
        if (selectedMunicipality) newParams.set('municipality', selectedMunicipality.slug);

        setSearchParams(newParams);
    }, [searchTerm, selectedRegion, selectedMunicipality, setSearchParams]);

    // Gestionnaires d'événements
    const handleMunicipalityClick = (municipality) => {
        setSelectedMunicipality(municipality);
        if (mapRef.current && mapRef.current.focusOnMunicipality) {
            mapRef.current.focusOnMunicipality(municipality);
        }
    };

    const handleMunicipalitySelect = (municipality) => {
        if (user) {
            const redirectUrl = getUserRedirectUrl(municipality, user);
            navigate(redirectUrl);
        } else {
            navigate(`/municipality/${municipality.slug}`);
        }
    };

    const clearFilters = () => {
        setSearchTerm('');
        setSelectedRegion('');
        setSelectedMunicipality(null);
        setIsFilterOpen(false);
    };

    const toggleSort = (field) => {
        if (sortBy === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(field);
            setSortOrder('asc');
        }
    };

    const formatNumber = (num) => {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'k';
        }
        return num.toString();
    };

    return (
        <Layout>
            <div className={styles.mapPage}>
                {/* Header avec recherche et filtres */}
                <div className={styles.header}>
                    <div className={styles.headerContent}>
                        <div className={styles.searchSection}>
                            <div className={styles.searchBox}>
                                <SearchIcon className={styles.searchIcon} />
                                <input
                                    type="text"
                                    placeholder="Rechercher une municipalité ou région..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className={styles.searchInput}
                                />
                            </div>

                            <button
                                onClick={() => setIsFilterOpen(!isFilterOpen)}
                                className={`${styles.filterButton} ${isFilterOpen ? styles.active : ''}`}
                            >
                                <FilterListIcon />
                                Filtres
                            </button>
                        </div>

                        {/* Filtres avancés */}
                        {isFilterOpen && (
                            <div className={styles.filterPanel}>
                                <div className={styles.filterContent}>
                                    <div className={styles.filterGroup}>
                                        <label>Région</label>
                                        <select
                                            value={selectedRegion}
                                            onChange={(e) => setSelectedRegion(e.target.value)}
                                            className={styles.regionSelect}
                                        >
                                            <option value="">Toutes les régions</option>
                                            {regions.map(region => (
                                                <option key={region} value={region}>{region}</option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className={styles.filterGroup}>
                                        <label>Trier par</label>
                                        <div className={styles.sortButtons}>
                                            <button
                                                onClick={() => toggleSort('name')}
                                                className={`${styles.sortButton} ${sortBy === 'name' ? styles.active : ''}`}
                                            >
                                                Nom
                                                {sortBy === 'name' && (
                                                    sortOrder === 'asc' ? <ArrowUpwardIcon /> : <ArrowDownwardIcon />
                                                )}
                                            </button>
                                            <button
                                                onClick={() => toggleSort('population')}
                                                className={`${styles.sortButton} ${sortBy === 'population' ? styles.active : ''}`}
                                            >
                                                Population
                                                {sortBy === 'population' && (
                                                    sortOrder === 'asc' ? <ArrowUpwardIcon /> : <ArrowDownwardIcon />
                                                )}
                                            </button>
                                            <button
                                                onClick={() => toggleSort('region')}
                                                className={`${styles.sortButton} ${sortBy === 'region' ? styles.active : ''}`}
                                            >
                                                Région
                                                {sortBy === 'region' && (
                                                    sortOrder === 'asc' ? <ArrowUpwardIcon /> : <ArrowDownwardIcon />
                                                )}
                                            </button>
                                        </div>
                                    </div>

                                    <button
                                        onClick={clearFilters}
                                        className={styles.clearButton}
                                    >
                                        <CloseIcon />
                                        Effacer les filtres
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Statistiques compactes */}
                        <div className={styles.statsBar}>
                            <div className={styles.statItem}>
                                <LocationOnIcon />
                                <span>{stats.totalMunicipalities} municipalités</span>
                            </div>
                            <div className={styles.statItem}>
                                <PeopleIcon />
                                <span>{formatNumber(stats.totalPopulation)} habitants</span>
                            </div>
                            <div className={styles.statItem}>
                                <BusinessIcon />
                                <span>{stats.regionsCount} régions</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Contenu principal avec carte */}
                <div className={styles.mainContent}>
                    {/* Carte */}
                    <div className={styles.mapContainer}>
                        <MunicipalitiesMap
                            ref={mapRef}
                            municipalities={filteredMunicipalities}
                            selectedMunicipality={selectedMunicipality}
                            onMunicipalityClick={handleMunicipalityClick}
                            searchTerm={searchTerm}
                        />

                        {/* Panneau de détails de la municipalité sélectionnée */}
                        {selectedMunicipality && (
                            <div className={styles.municipalityPanel}>
                                <div className={styles.municipalityHeader}>
                                    <div className={styles.municipalityInfo}>
                                        <h3>{selectedMunicipality.name}</h3>
                                        <p>{selectedMunicipality.region}</p>
                                    </div>
                                    <button
                                        onClick={() => setSelectedMunicipality(null)}
                                        className={styles.closePanel}
                                    >
                                        <CloseIcon />
                                    </button>
                                </div>

                                <div className={styles.municipalityStats}>
                                    <div className={styles.stat}>
                                        <PeopleIcon />
                                        <div>
                                            <span className={styles.statValue}>
                                                {selectedMunicipality.population?.toLocaleString() || 'N/A'}
                                            </span>
                                            <span className={styles.statLabel}>habitants</span>
                                        </div>
                                    </div>
                                    <div className={styles.stat}>
                                        <HomeIcon />
                                        <div>
                                            <span className={styles.statValue}>
                                                {selectedMunicipality.dwellings?.toLocaleString() || 'N/A'}
                                            </span>
                                            <span className={styles.statLabel}>logements</span>
                                        </div>
                                    </div>
                                </div>

                                <button
                                    onClick={() => handleMunicipalitySelect(selectedMunicipality)}
                                    className={styles.visitButton}
                                >
                                    <LocationOnIcon />
                                    Visiter la municipalité
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default MapPage;