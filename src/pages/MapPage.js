import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useMunicipality } from '../contexts/MunicipalityContext';
import { getMunicipalitiesStats, searchMunicipalities } from '../data/municipalitiesUtils';
import { getCurrentDivision } from '../utils/divisionStorage';
import { getPreferredCountry, setPreferredCountry } from '../utils/countryPreference';
import { getUrlPathByISO3 } from '../config/adminDivisions';
import Layout from '../components/Layout';
import MunicipalitiesMap from '../components/MunicipalitiesMap';
import ShareMapCard from '../components/ShareMapCard';
import geolocationService from '../services/geolocationService';
import {
    LocationOn as LocationIcon,
    LocationOn,
    People as PeopleIcon,
    Public as PublicIcon,
    TrendingUp as TrendingUpIcon,
    Explore as ExploreIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandMore,
    Check,
    ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import styles from './MapPage.module.css';

const MapPage = () => {
    const [searchParams] = useSearchParams();
    const divisionIdFromUrl = searchParams.get('division'); // Read ?division={id} from URL

    console.log('🔗 MapPage mounted - URL params:', {
        divisionIdFromUrl,
        fullUrl: window.location.href,
        searchParams: searchParams.toString()
    });

    const { activeMunicipality, getMunicipalitySlug, switchMunicipality, getAdminLabels } = useMunicipality();
    const [selectedMunicipality, setSelectedMunicipality] = useState(activeMunicipality);
    const [searchQuery, setSearchQuery] = useState('');

    // Country and division selection state
    const [countries, setCountries] = useState([]);
    const [selectedCountry, setSelectedCountry] = useState(null);
    const [level1Divisions, setLevel1Divisions] = useState([]);
    const [selectedLevel1, setSelectedLevel1] = useState(null);
    const [defaultLevelDivisions, setDefaultLevelDivisions] = useState([]);
    const [selectedDefaultDivision, setSelectedDefaultDivision] = useState(null);
    const [municipalitySearchTerm, setMunicipalitySearchTerm] = useState('');
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [loadingCountries, setLoadingCountries] = useState(true);
    const [loadingLevel1, setLoadingLevel1] = useState(false);
    const [loadingDefault, setLoadingDefault] = useState(false);

    // Store the full division hierarchy from API
    const [divisionHierarchy, setDivisionHierarchy] = useState(null);
    const [loadingDivisionHierarchy, setLoadingDivisionHierarchy] = useState(false);

    // Obtenir les libellés adaptés à la division administrative
    const adminLabels = getAdminLabels();

    const [stats, setStats] = useState(null);
    const [isVisible, setIsVisible] = useState(false);
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
    const navigate = useNavigate();
    const { user, anonymousLocation } = useAuth();

    // Helper to get effective location (priority: activeMunicipality > current division > user > anonymous)
    const getEffectiveLocation = () => {
        console.log('🔍 MapPage - Getting effective location...');
        console.log('🔍 MapPage - Selected country:', selectedCountry?.iso3);

        // PRIORITY 1: Use activeMunicipality from context (the division chosen in left menu)
        // But validate it matches the selected country
        if (activeMunicipality?.id) {
            const municipalityCountry = activeMunicipality.country?.iso3 || activeMunicipality.country;

            // If no country selected yet, or if municipality matches selected country, use it
            if (!selectedCountry || municipalityCountry === selectedCountry.iso3) {
                console.log('📍 MapPage - Using activeMunicipality from context:', activeMunicipality.name);
                return {
                    country: municipalityCountry || selectedCountry?.iso3,
                    division_id: activeMunicipality.id,
                    level_1_id: activeMunicipality.level_1_id || user?.location?.level_1_id,
                    city: activeMunicipality.name || activeMunicipality.nom
                };
            } else {
                console.log('⚠️ MapPage - activeMunicipality country mismatch:', municipalityCountry, 'vs', selectedCountry.iso3);
            }
        }

        // PRIORITY 2: Use current active division from single storage
        // But validate it matches the selected country
        const currentDivision = getCurrentDivision();
        console.log('📍 MapPage - localStorage check:', currentDivision ? currentDivision.name : 'NOT FOUND');

        if (currentDivision) {
            // If no country selected yet, or if division matches selected country, use it
            if (!selectedCountry || currentDivision.country === selectedCountry.iso3) {
                console.log('✅ MapPage - Using current division from localStorage:', currentDivision.name);
                return {
                    country: currentDivision.country,
                    division_id: currentDivision.id,
                    level_1_id: currentDivision.level_1_id,
                    city: currentDivision.name
                };
            } else {
                console.log('⚠️ MapPage - localStorage division country mismatch:', currentDivision.country, 'vs', selectedCountry.iso3);
                // Don't use stored division if it's from a different country
            }
        }

        // PRIORITY 3: Use user's location (if it matches selected country)
        if (user?.location || user?.profile?.administrative_division) {
            const userCountry = user.location?.country;

            if (!selectedCountry || userCountry === selectedCountry.iso3 || userCountry === selectedCountry.name) {
                console.log('📍 MapPage - Using user profile location');
                return {
                    country: user.location?.country,
                    division_id: user.location?.division_id || user.profile?.administrative_division?.division_id,
                    level_1_id: user.location?.level_1_id,
                    city: user.location?.city || user.municipality
                };
            }
        }

        // PRIORITY 4: Use anonymous location (if it matches selected country)
        if (anonymousLocation?.location) {
            const anonCountry = anonymousLocation.country?.name;

            if (!selectedCountry || anonCountry === selectedCountry.iso3 || anonCountry === selectedCountry.name) {
                console.log('📍 MapPage - Using anonymous location');
                return {
                    country: anonymousLocation.country?.name,
                    division_id: anonymousLocation.location?.administrative_division_id,
                    level_1_id: null,
                    city: anonymousLocation.location?.division_name
                };
            }
        }

        console.log('⚠️ MapPage - No location found matching selected country');
        return null;
    };    // Animation d'apparition et suivi de la souris
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

    // Update selectedMunicipality when activeMunicipality changes (from left menu dropdown)
    useEffect(() => {
        if (activeMunicipality) {
            console.log('📍 MapPage: activeMunicipality changed, updating map selection:', activeMunicipality);
            setSelectedMunicipality(activeMunicipality);
        }
    }, [activeMunicipality]);

    // Load countries on mount
    useEffect(() => {
        const loadCountries = async () => {
            setLoadingCountries(true);
            const result = await geolocationService.getCountries();

            if (result.success) {
                setCountries(result.countries);
            }
            setLoadingCountries(false);
        };

        loadCountries();
    }, []); // Load countries only once on mount

    // Listen for country preference changes from other components (e.g., left menu)
    useEffect(() => {
        const handleCountryPreferenceChange = (event) => {
            const newCountryISO3 = event.detail;
            console.log('🔄 MapPage - Country preference changed from another component:', newCountryISO3);

            // Find the new country in our countries list and select it
            if (countries && countries.length > 0) {
                const newCountry = countries.find(c => c.iso3 === newCountryISO3);
                if (newCountry && newCountry.id !== selectedCountry?.id) {
                    console.log('✅ MapPage - Syncing to new country:', newCountry.name);
                    setSelectedCountry(newCountry);
                    // Clear related state when country changes from external source
                    setSelectedLevel1(null);
                    setDefaultLevelDivisions([]);
                    setSelectedDefaultDivision(null);
                    setDivisionHierarchy(null);
                    setMunicipalitySearchTerm('');
                    setDropdownOpen(false);
                }
            }
        };

        window.addEventListener('countryPreferenceChanged', handleCountryPreferenceChange);
        return () => window.removeEventListener('countryPreferenceChanged', handleCountryPreferenceChange);
    }, [countries, selectedCountry]); // React to countries being loaded or selectedCountry changing

    // Fetch division details and auto-select country based on URL param, activeMunicipality, or stored division
    // This calls the API to get full division hierarchy (country + level 1 parent)
    useEffect(() => {
        if (!countries || countries.length === 0) {
            return; // Wait for countries to load
        }

        const loadDivisionHierarchy = async () => {
            let divisionId = null;

            // PRIORITY 0: Use division ID from URL query param (?division={id})
            if (divisionIdFromUrl) {
                // Don't reload if we already have this division loaded
                if (divisionHierarchy?.id === divisionIdFromUrl) {
                    console.log('⏭️ MapPage - Division already loaded from URL, skipping reload');
                    return;
                }
                divisionId = divisionIdFromUrl;
                console.log('🔗 MapPage - Using division ID from URL:', divisionId);
            }
            // PRIORITY 1: Use activeMunicipality ID
            else if (activeMunicipality?.id) {
                // Don't reload if we already have this division loaded
                if (divisionHierarchy?.id === activeMunicipality.id) {
                    console.log('⏭️ MapPage - Division already loaded from context, skipping reload');
                    return;
                }
                divisionId = activeMunicipality.id;
                console.log('🔍 MapPage - Using activeMunicipality ID:', divisionId);
            }
            // PRIORITY 2: Use current division from localStorage
            else {
                const currentDivision = getCurrentDivision();
                if (currentDivision?.id) {
                    // Don't reload if we already have this division loaded
                    if (divisionHierarchy?.id === currentDivision.id) {
                        console.log('⏭️ MapPage - Division already loaded from storage, skipping reload');
                        return;
                    }
                    divisionId = currentDivision.id;
                    console.log('🔍 MapPage - Using localStorage division ID:', divisionId);
                }
            }

            // If we have a division ID, fetch its full hierarchy via neighbors endpoint
            if (divisionId) {
                console.log('📡 MapPage - Fetching division hierarchy from API...', { divisionId });
                setLoadingDivisionHierarchy(true);
                const result = await geolocationService.getDivisionNeighbors(divisionId, 0);

                console.log('📡 MapPage - API response:', result);

                if (result.success && result.division) {
                    const division = result.division;
                    console.log('✅ MapPage - Division hierarchy loaded:', division);

                    // Extract country from division response
                    if (division.country) {
                        const countryToSelect = countries.find(c => c.iso3 === division.country.iso3);
                        if (countryToSelect) {
                            console.log('✅ MapPage - Country detected from API:', countryToSelect.name);

                            // CRITICAL: Batch all state updates together using React 18 automatic batching
                            // This prevents multiple re-renders and zoom animations
                            console.log('📍 MapPage - Batching state updates for division:', {
                                id: division.id,
                                name: division.name,
                                country: division.country?.iso3
                            });

                            // Set all states in sequence - React 18 will batch them automatically
                            setDivisionHierarchy(division);
                            setSelectedCountry(countryToSelect);
                            setSelectedDefaultDivision(division);
                            setSelectedMunicipality(division);
                            setLoadingDivisionHierarchy(false);
                            return; // Done!
                        } else {
                            console.error('❌ MapPage - Country not found in countries list:', division.country.iso3);
                        }
                    } else {
                        console.error('❌ MapPage - No country in division response');
                    }
                } else {
                    console.error('❌ MapPage - API call failed or no division:', result);
                }
                setLoadingDivisionHierarchy(false);
            } else {
                console.log('⚠️ MapPage - No division ID to load');
            }

            // FALLBACK: Try other detection methods if API call failed
            let countryToSelect = null;

            // PRIORITY 1: Check country preference from localStorage (set by left menu)
            const preferredCountryISO3 = getPreferredCountry(user);
            if (preferredCountryISO3) {
                console.log('🌍 MapPage - Checking country preference from localStorage:', preferredCountryISO3);
                countryToSelect = countries.find(c => c.iso3 === preferredCountryISO3);
                if (countryToSelect) {
                    console.log('✅ MapPage - Using preferred country:', countryToSelect.name);
                }
            }

            // PRIORITY 2: Try activeMunicipality country property
            if (!countryToSelect && activeMunicipality?.country) {
                const municipalityCountry = activeMunicipality.country?.iso3 || activeMunicipality.country;
                console.log('🌍 MapPage - Detecting country from activeMunicipality property:', municipalityCountry);
                countryToSelect = countries.find(c => c.iso3 === municipalityCountry);
            }

            // PRIORITY 3: Try localStorage division country
            if (!countryToSelect) {
                const currentDivision = getCurrentDivision();
                if (currentDivision?.country) {
                    console.log('🌍 MapPage - Detecting country from localStorage:', currentDivision.country);
                    countryToSelect = countries.find(c => c.iso3 === currentDivision.country);
                }
            }

            // PRIORITY 4: Try user location
            if (!countryToSelect) {
                const effectiveLocation = getEffectiveLocation();
                if (effectiveLocation?.country) {
                    console.log('🌍 MapPage - Detecting country from user location:', effectiveLocation.country);
                    countryToSelect = countries.find(c =>
                        c.name === effectiveLocation.country ||
                        c.iso2 === effectiveLocation.country ||
                        c.iso3 === effectiveLocation.country
                    );
                } else if (anonymousLocation?.country) {
                    console.log('🌍 MapPage - Detecting country from anonymous location');
                    countryToSelect = countries.find(c =>
                        c.name === anonymousLocation.country.name ||
                        c.iso3 === anonymousLocation.country.iso3
                    );
                }
            }

            // FALLBACK: Default to Canada only if no country detected at all
            if (!countryToSelect) {
                console.log('🌍 MapPage - No country detected, defaulting to Canada');
                countryToSelect = countries.find(c => c.iso3 === 'CAN');
            }

            if (countryToSelect) {
                console.log('✅ MapPage - Selected country:', countryToSelect.name, countryToSelect.iso3);
                setSelectedCountry(countryToSelect);
            }
        };

        loadDivisionHierarchy();
    }, [countries, activeMunicipality, user, anonymousLocation, divisionIdFromUrl]); // React to URL param, activeMunicipality changes

    // Load level 1 divisions when country is selected
    useEffect(() => {
        const loadLevel1Divisions = async () => {
            if (!selectedCountry) {
                setLevel1Divisions([]);
                setSelectedLevel1(null);
                setDefaultLevelDivisions([]); // Clear default divisions when country changes
                setSelectedDefaultDivision(null); // Clear selected division
                return;
            }

            // CRITICAL: Clear level1 divisions immediately when country changes
            // This prevents showing old country's data while loading
            console.log('🔄 MapPage - Loading level 1 divisions for:', selectedCountry.name);
            setLevel1Divisions([]); // Clear first
            setSelectedLevel1(null); // Clear selection

            setLoadingLevel1(true);
            const result = await geolocationService.getDivisionsByLevel(
                selectedCountry.id,
                1, // Level 1
                null,
                100
            );

            if (result.success) {
                setLevel1Divisions(result.divisions);

                // Try to auto-select level 1 division from hierarchy API or user location
                // BUT ONLY if the hierarchy matches the current country
                let level1ToSelect = null;

                // PRIORITY 1: Use level_1_parent from division hierarchy API (only if country matches)
                if (divisionHierarchy?.level_1_parent && divisionHierarchy?.country?.iso3 === selectedCountry.iso3) {
                    console.log('📍 MapPage - Auto-selecting level 1 from hierarchy:', divisionHierarchy.level_1_parent.name);
                    level1ToSelect = result.divisions.find(d => d.id === divisionHierarchy.level_1_parent.id);
                }

                // PRIORITY 2: Try effectiveLocation level_1_id (only if country matches)
                if (!level1ToSelect) {
                    const effectiveLocation = getEffectiveLocation();
                    const userCountryMatches = effectiveLocation?.country === selectedCountry.iso3 ||
                                              effectiveLocation?.country === selectedCountry.iso2 ||
                                              effectiveLocation?.country === selectedCountry.name;

                    if (userCountryMatches && effectiveLocation?.level_1_id) {
                        level1ToSelect = result.divisions.find(d => d.id === effectiveLocation.level_1_id);
                    } else if (userCountryMatches && user?.profile?.administrative_division?.admin_level === 1) {
                        level1ToSelect = result.divisions.find(d => d.id === effectiveLocation?.division_id);
                    }
                }

                // Don't auto-select first division when exploring
                // Only auto-select if we have a valid reason (hierarchy or user location match)
                // Fallback to first division ONLY if hierarchy exists and matches
                if (!level1ToSelect && divisionHierarchy?.country?.iso3 === selectedCountry.iso3 && result.divisions.length > 0) {
                    console.log('📍 MapPage - Auto-selecting first level 1 division from hierarchy context');
                    level1ToSelect = result.divisions[0];
                }

                if (level1ToSelect) {
                    setSelectedLevel1(level1ToSelect);
                } else {
                    console.log('🗺️ MapPage - No auto-selection, user should manually select level 1');
                }
            }
            setLoadingLevel1(false);
        };

        loadLevel1Divisions();
    }, [selectedCountry, divisionHierarchy, user, anonymousLocation, activeMunicipality]);

    // Load default level divisions when level 1 is selected
    useEffect(() => {
        const loadDefaultDivisions = async () => {
            if (!selectedCountry || !selectedLevel1) {
                setDefaultLevelDivisions([]);
                setSelectedDefaultDivision(null);
                return;
            }

            // CRITICAL: If hierarchy exists but country doesn't match, clear and return
            // This prevents loading old country data when switching countries
            if (divisionHierarchy && divisionHierarchy.country?.iso3 !== selectedCountry.iso3) {
                console.log('⚠️ MapPage - Country mismatch detected, clearing divisions:', {
                    hierarchyCountry: divisionHierarchy.country?.iso3,
                    selectedCountry: selectedCountry.iso3
                });
                setDefaultLevelDivisions([]);
                setSelectedDefaultDivision(null);
                return; // Don't load - wait for hierarchy to be cleared
            }

            setLoadingDefault(true);

            // Get division ID - only use hierarchy if it matches the selected country
            let divisionId = null;

            // PRIORITY 1: Use division from hierarchy API ONLY if country matches
            if (divisionHierarchy?.id && divisionHierarchy?.country?.iso3 === selectedCountry.iso3) {
                divisionId = divisionHierarchy.id;
            }
            // CRITICAL: If hierarchy exists but doesn't match OR is null, don't use any division
            // This ensures we load alphabetically when switching countries
            else {
                divisionId = null;
            }

            // Load only 10 divisions (user's + 9 closest) if division available
            // Otherwise load first 10 alphabetically
            const result = await geolocationService.getDivisionsByLevel(
                selectedCountry.id,
                selectedCountry.default_admin_level,
                selectedLevel1.id,
                10,
                divisionId  // Pass division to get closest ones (null if country changed)
            );            if (result.success) {
                setDefaultLevelDivisions(result.divisions);

                // Auto-select the division ONLY if hierarchy matches current country
                let defaultToSelect = null;

                if (divisionId && divisionHierarchy?.country?.iso3 === selectedCountry.iso3) {
                    defaultToSelect = result.divisions.find(d => d.id === divisionId);
                }

                // If not found by ID, try by name from hierarchy (only if country matches)
                if (!defaultToSelect && divisionHierarchy?.name && divisionHierarchy?.country?.iso3 === selectedCountry.iso3) {
                    defaultToSelect = result.divisions.find(d =>
                        d.name.toLowerCase() === divisionHierarchy.name.toLowerCase()
                    );
                }

                // Don't auto-select if country was changed - let user choose
                if (defaultToSelect) {
                    setSelectedDefaultDivision(defaultToSelect);
                    setSelectedMunicipality(defaultToSelect);
                }
            }
            setLoadingDefault(false);
        };

        loadDefaultDivisions();
    }, [selectedCountry, selectedLevel1, divisionHierarchy, user, anonymousLocation, activeMunicipality]);

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
            searchMunicipalities(searchQuery, 5);
        }
    }, [searchQuery]);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            // Check if click is outside the dropdown
            const dropdownElements = document.querySelectorAll('[class*="divisionSelectorWrapper"]');
            let isOutside = true;

            dropdownElements.forEach(element => {
                if (element.contains(event.target)) {
                    isOutside = false;
                }
            });

            if (isOutside && dropdownOpen) {
                setDropdownOpen(false);
                setMunicipalitySearchTerm('');
            }
        };

        if (dropdownOpen) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [dropdownOpen]);

    const handleMunicipalitySelect = (municipality) => {
        setSelectedMunicipality(municipality);
        setSelectedDefaultDivision(municipality);
        setSearchQuery('');
    };

    const handleVisitMunicipality = () => {
        if (selectedMunicipality) {
            switchMunicipality(selectedMunicipality.name || selectedMunicipality.nom, selectedMunicipality.id);
            const slug = getMunicipalitySlug(selectedMunicipality.name || selectedMunicipality.nom);

            // Get URL path based on country
            const countryISO3 = selectedMunicipality.country?.iso3 ||
                               selectedCountry?.iso3 ||
                               getPreferredCountry();
            const urlPath = getUrlPathByISO3(countryISO3);

            console.log('🔗 MapPage navigation:', { slug, countryISO3, urlPath });
            navigate(`/${urlPath}/${slug}/accueil`);
        }
    };

    const handleDefaultDivisionChange = (divisionId) => {
        const division = defaultLevelDivisions.find(d => d.id === divisionId);
        if (division) {
            setSelectedDefaultDivision(division);
            setSelectedMunicipality(division);
        }
    };

    const title = "Explorez le Québec";
    const subtitle = `Découvrez les ${adminLabels.plural} du Québec`;

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
                                <h1 className={styles.pageTitle}>Carte Interactive</h1>
                                <p className={styles.pageSubtitle}>
                                    Explorez les divisions administratives par pays
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Division selection filters */}
                    <div className={styles.selectionFilters}>
                        {/* Country selector */}
                        <div className={styles.filterGroup}>
                            <label className={styles.filterLabel}>Pays</label>
                            <select
                                className={styles.filterSelect}
                                value={selectedCountry?.id || ''}
                                onChange={(e) => {
                                    const country = countries.find(c => c.id === e.target.value);
                                    setSelectedCountry(country);
                                    // Map is for exploration - don't save preference to avoid disrupting left menu context
                                    console.log('�️ MapPage - Exploring country:', country?.name);
                                    setSelectedLevel1(null);
                                    setDefaultLevelDivisions([]);
                                    setSelectedDefaultDivision(null); // Clear selected division when country changes
                                    setDivisionHierarchy(null); // Clear hierarchy - we're browsing a different country now
                                    setMunicipalitySearchTerm(''); // Clear search term
                                    setDropdownOpen(false); // Close the dropdown to force re-render
                                }}
                                disabled={loadingCountries}
                            >
                                {loadingCountries ? (
                                    <option>Chargement...</option>
                                ) : (
                                    <>
                                        <option value="">Sélectionner un pays</option>
                                        {countries.map(country => (
                                            <option key={country.id} value={country.id}>
                                                {country.name} ({country.iso3})
                                            </option>
                                        ))}
                                    </>
                                )}
                            </select>
                        </div>

                        {/* Level 1 selector */}
                        {selectedCountry && level1Divisions.length > 0 && (
                            <div className={styles.filterGroup}>
                                <label className={styles.filterLabel}>
                                    {selectedCountry.admin_levels?.[1] || 'Niveau 1'}
                                </label>
                                <select
                                    className={styles.filterSelect}
                                    value={selectedLevel1?.id || ''}
                                    onChange={(e) => {
                                        const division = level1Divisions.find(d => d.id === e.target.value);
                                        setSelectedLevel1(division);
                                        setSelectedDefaultDivision(null);
                                        setSelectedMunicipality(null);
                                        setDefaultLevelDivisions([]); // Clear the list when level 1 changes
                                        setMunicipalitySearchTerm(''); // Clear search term
                                    }}
                                    disabled={loadingLevel1}
                                >
                                    {loadingLevel1 ? (
                                        <option>Chargement...</option>
                                    ) : (
                                        <>
                                            <option value="">Sélectionner...</option>
                                            {level1Divisions.map(division => (
                                                <option key={division.id} value={division.id}>
                                                    {division.name}
                                                </option>
                                            ))}
                                        </>
                                    )}
                                </select>
                            </div>
                        )}

                        {/* Default level selector (e.g., municipalities) */}
                        {selectedCountry && selectedLevel1 && (
                            <div className={styles.filterGroup}>
                                <label className={styles.filterLabel}>
                                    {selectedCountry.default_division_name || `Niveau ${selectedCountry.default_admin_level}`}
                                </label>

                                {/* Dropdown button with search inside */}
                                <div className={styles.divisionSelectorWrapper}>
                                    <button
                                        type="button"
                                        className={`${styles.divisionSelectorButton} ${dropdownOpen ? styles.open : ''}`}
                                        onClick={() => setDropdownOpen(!dropdownOpen)}
                                        disabled={loadingDefault}
                                    >
                                        <div className={styles.selectedDivision}>
                                            {selectedDefaultDivision ? (
                                                <div className={styles.divisionInfo}>
                                                    <div className={styles.divisionName}>
                                                        {selectedDefaultDivision.name}
                                                    </div>
                                                    {selectedDefaultDivision.parent_name && (
                                                        <div className={styles.divisionRegion}>
                                                            {selectedDefaultDivision.parent_name}
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (
                                                <div className={styles.divisionInfo}>
                                                    <div className={styles.divisionPlaceholder}>
                                                        {defaultLevelDivisions.length > 0
                                                            ? `Sélectionner une ${selectedCountry.default_division_name}...`
                                                            : `Aucune ${selectedCountry.default_division_name} disponible`
                                                        }
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        <ExpandMore className={`${styles.expandIcon} ${dropdownOpen ? styles.rotated : ''}`} />
                                    </button>

                                    {/* Dropdown menu with search */}
                                    <div className={`${styles.divisionDropdownMenu} ${dropdownOpen ? styles.show : ''}`}>
                                        <div className={styles.searchWrapper}>
                                            <input
                                                type="text"
                                                className={styles.searchInput}
                                                placeholder={`Rechercher une ${selectedCountry.default_division_name}...`}
                                                value={municipalitySearchTerm}
                                                onChange={async (e) => {
                                                    const searchValue = e.target.value;
                                                    setMunicipalitySearchTerm(searchValue);

                                                    // Search via API if search term is >= 2 characters
                                                    if (searchValue.trim().length >= 2) {
                                                        const searchResult = await geolocationService.searchDivisions(
                                                            selectedCountry.iso3,
                                                            searchValue,
                                                            20
                                                        );

                                                        if (searchResult.success) {
                                                            // Filter results by selectedLevel1 if available
                                                            let filteredResults = searchResult.results;
                                                            if (selectedLevel1) {
                                                                filteredResults = searchResult.results.filter(
                                                                    div => div.level_1_id === selectedLevel1.id
                                                                );
                                                            }
                                                            setDefaultLevelDivisions(filteredResults);
                                                        }
                                                    } else if (searchValue.trim().length === 0) {
                                                        // Reload default 10 divisions when search is cleared
                                                        // Only use hierarchy if it matches the current country
                                                        let divisionId = null;

                                                        if (divisionHierarchy?.id && divisionHierarchy?.country?.iso3 === selectedCountry.iso3) {
                                                            divisionId = divisionHierarchy.id;
                                                        }

                                                        // Only reload if we have a level1 selected
                                                        if (selectedLevel1) {
                                                            const result = await geolocationService.getDivisionsByLevel(
                                                                selectedCountry.id,
                                                                selectedCountry.default_admin_level,
                                                                selectedLevel1.id,
                                                                10,
                                                                divisionId
                                                            );

                                                            if (result.success) {
                                                                setDefaultLevelDivisions(result.divisions);
                                                            }
                                                        }
                                                    }
                                                }}
                                            />
                                            <LocationOn className={styles.searchIcon} />
                                        </div>

                                        <div className={styles.dropdownContent}>
                                            {loadingDefault ? (
                                                <div className={styles.loadingState}>
                                                    <div className={styles.loadingSpinner} />
                                                    Chargement...
                                                </div>
                                            ) : defaultLevelDivisions.length > 0 ? (
                                                defaultLevelDivisions.map((division) => {
                                                    const isSelected = selectedDefaultDivision?.id === division.id;
                                                    return (
                                                        <button
                                                            key={division.id}
                                                            type="button"
                                                            className={`${styles.divisionOption} ${isSelected ? styles.selected : ''}`}
                                                            onClick={() => {
                                                                handleDefaultDivisionChange(division.id);
                                                                setDropdownOpen(false);
                                                                setMunicipalitySearchTerm('');
                                                            }}
                                                        >
                                                            <div className={styles.optionContent}>
                                                                <div className={styles.optionInfo}>
                                                                    <div className={styles.optionName}>
                                                                        {division.name}
                                                                    </div>
                                                                    {division.parent_name && (
                                                                        <div className={styles.optionDetails}>
                                                                            {division.parent_name}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </div>
                                                            {isSelected && (
                                                                <Check className={styles.checkIcon} />
                                                            )}
                                                        </button>
                                                    );
                                                })
                                            ) : (
                                                <div className={styles.noResults}>
                                                    {municipalitySearchTerm ? `Aucune ${selectedCountry.default_division_name} trouvée pour "${municipalitySearchTerm}"` : `Aucune ${selectedCountry.default_division_name} disponible`}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Interface principale en grid */}
                <div className={styles.mainInterface}>
                    {/* Section principale avec carte et infos */}
                    <div className={styles.mapArea}>
                        <div className={styles.mapContainer}>
                            {loadingDivisionHierarchy ? (
                                <div className={styles.mapLoadingState}>
                                    <div className={styles.loadingSpinner} />
                                    <p>Chargement de la carte...</p>
                                </div>
                            ) : (
                                <MunicipalitiesMap
                                    selectedMunicipality={selectedDefaultDivision}
                                    onMunicipalitySelect={handleMunicipalitySelect}
                                    selectedCountry={selectedCountry}
                                    selectedLevel1={selectedLevel1}
                                    height="500px"
                                />
                            )}

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
                                            <div className={styles.compactStatLabel}>{adminLabels.plural}</div>
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

                        {/* Share Map Card - Always visible */}
                        <ShareMapCard
                            selectedDivision={selectedDefaultDivision}
                            selectedCountry={selectedCountry}
                        />
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default MapPage;