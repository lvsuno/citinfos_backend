import React, { useState, useEffect, useRef } from 'react';
import { LocationOn, ExpandMore, Check, Public } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useMunicipality } from '../contexts/MunicipalityContext';
import { useAuth } from '../contexts/AuthContext';
import geolocationService from '../services/geolocationService';
import { setCurrentDivision } from '../utils/divisionStorage';
import { getPreferredCountry, setPreferredCountry, isBrowsingDifferentCountry, getCountryName } from '../utils/countryPreference';
import { getAdminDivisionUrlPath, getUrlPathByISO3 } from '../config/adminDivisions';
import styles from './MunicipalitySelector.module.css';

const MunicipalitySelector = ({
  value = '',
  onChange = () => { },
  placeholder = '',
  error = '',
  required = false,
  className = '',
  currentPageDivision = null  // NEW: Current division from URL (takes priority)
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMunicipality, setSelectedMunicipality] = useState(null);
  const [neighbors, setNeighbors] = useState([]);
  const [isLoadingNeighbors, setIsLoadingNeighbors] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  // Country selection state
  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [loadingCountries, setLoadingCountries] = useState(true);
  const [countrySearchTerm, setCountrySearchTerm] = useState('');
  const [isCountryDropdownOpen, setIsCountryDropdownOpen] = useState(false);

  const selectorRef = useRef(null);
  const searchInputRef = useRef(null);
  const countryDropdownRef = useRef(null);
  const initialMunicipalitySetRef = useRef(false);
  const navigate = useNavigate();
  const { activeMunicipality, switchMunicipality, getMunicipalitySlug, getAdminLabels } = useMunicipality();
  const { user, anonymousLocation } = useAuth();

  // Obtenir les libellés adaptés à la division administrative
  const adminLabels = getAdminLabels();

  // Placeholder dynamique basé sur le type d'administration
  const dynamicPlaceholder = placeholder || `Sélectionner une ${adminLabels.singular}`;

  // Get active country code from selected country or user preference
  const countryCode = selectedCountry?.iso3 || getPreferredCountry(user);

  // Get the division ID from user's profile (UUID string for API calls)
  // The division_id is inside the location object from the login response
  // For anonymous users, get it from anonymousLocation from AuthContext
  // PRIORITY 1: Use currentPageDivision from props (URL-based)
  // PRIORITY 2: Use activeMunicipality.id from context (updated by switchMunicipality)
  // PRIORITY 3: Use user profile division
  const userDivisionId = currentPageDivision?.id ||
                         activeMunicipality?.id ||
                         user?.profile?.administrative_division?.division_id ||
                         user?.location?.division_id ||
                         user?.profile?.location?.division_id ||
                         anonymousLocation?.location?.administrative_division_id;

  // Combine current municipality + neighbors + search results
  const getDisplayedMunicipalities = () => {
    // If searching, show search results from API
    if (searchTerm && searchResults.length > 0) {
      return searchResults;
    }

    // If dropdown is open and we have neighbors, show current + neighbors
    if (isOpen && neighbors.length > 0) {
      return neighbors;
    }

    // Default: empty until search or neighbors load
    return [];
  };

  const municipalities = getDisplayedMunicipalities();

  // Filter countries based on search term
  const getFilteredCountries = () => {
    if (!countrySearchTerm.trim()) {
      return countries;
    }

    const search = countrySearchTerm.toLowerCase();
    return countries.filter(country =>
      country.name.toLowerCase().includes(search) ||
      country.iso3.toLowerCase().includes(search) ||
      country.iso2?.toLowerCase().includes(search)
    );
  };

  const filteredCountries = getFilteredCountries();
  const showCountrySearch = countries.length > 20;

  // Load countries on mount
  useEffect(() => {
    const loadCountries = async () => {
      setLoadingCountries(true);
      try {
        const result = await geolocationService.getCountries();
        if (result.success && result.countries) {
          setCountries(result.countries);

          // Set initial country from preference
          const preferredCountryCode = getPreferredCountry(user);
          const country = result.countries.find(c => c.iso3 === preferredCountryCode);

          if (country) {
            setSelectedCountry(country);          }
        }
      } catch (error) {      } finally {
        setLoadingCountries(false);
      }
    };

    loadCountries();
  }, [user]);

  // Fetch neighbors when user has a division ID
  useEffect(() => {
    const fetchNeighbors = async () => {
      // Use the user's division ID from their profile
      if (userDivisionId) {
        setIsLoadingNeighbors(true);
        try {
          const result = await geolocationService.getDivisionNeighbors(userDivisionId, 4);
          if (result.success && result.neighbors) {
            // Create combined list: current division + 4 neighbors
            const currentDivision = {
              id: userDivisionId,
              nom: result.division?.name || activeMunicipality?.nom || activeMunicipality?.name,
              name: result.division?.name || activeMunicipality?.nom || activeMunicipality?.name,
              region: result.division?.parent_name || activeMunicipality?.region,
              isCurrent: true
            };

            const neighborsList = result.neighbors.map(neighbor => ({
              id: neighbor.id,
              nom: neighbor.name,
              name: neighbor.name,
              region: neighbor.parent_name,
              distance_km: neighbor.distance_km,
              boundary_type: neighbor.boundary_type
            }));

            setNeighbors([currentDivision, ...neighborsList]);

            // Update selectedMunicipality with fresh API data ONLY ONCE on initial load
            // Use ref to prevent infinite re-renders
            if (!selectedMunicipality && !initialMunicipalitySetRef.current) {
              setSelectedMunicipality(currentDivision);
              initialMunicipalitySetRef.current = true;
            }
          } else {
            setNeighbors([]);
          }
        } catch (error) {
          setNeighbors([]);
        } finally {
          setIsLoadingNeighbors(false);
        }
      } else {
        setNeighbors([]);
      }
    };

    fetchNeighbors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userDivisionId]); // Only re-run when userDivisionId changes

  // Search divisions via backend API when user types
  useEffect(() => {
    const searchDivisions = async () => {
      // Only search if we have a query with at least 2 characters
      if (searchTerm && searchTerm.length >= 2) {
        setIsSearching(true);
        try {
          const result = await geolocationService.searchDivisions(countryCode, searchTerm, 15);
          if (result.success && result.results) {
            // Transform API results to match component structure
            const divisions = result.results.map(division => ({
              id: division.id,
              nom: division.name,
              name: division.name,
              region: division.parent_name,
              admin_code: division.admin_code,
              boundary_type: division.boundary_type
            }));
            setSearchResults(divisions);
          } else {
            setSearchResults([]);
          }
        } catch (error) {          setSearchResults([]);
        } finally {
          setIsSearching(false);
        }
      } else {
        // Clear search results if query is too short
        setSearchResults([]);
      }
    };

    // Debounce search to avoid too many API calls
    const timeoutId = setTimeout(searchDivisions, 300);
    return () => clearTimeout(timeoutId);
  }, [searchTerm, countryCode]);

  // Gérer la sélection initiale - PRIORITY: currentPageDivision from URL
  useEffect(() => {
    // Priority 1: Use currentPageDivision from props (URL-based, most authoritative)
    if (currentPageDivision) {
      const newSelection = {
        id: currentPageDivision.id,
        nom: currentPageDivision.name,
        name: currentPageDivision.name,
        region: currentPageDivision.parent?.name || currentPageDivision.parent_name,
        isCurrent: true,
        fromUrl: true
      };

      setSelectedMunicipality(newSelection);
      // Reset ref so fetchNeighbors can update if needed
      initialMunicipalitySetRef.current = true;

      // Store in localStorage as the current active division
      const slug = getMunicipalitySlug(currentPageDivision.name);
      setCurrentDivision({
        id: currentPageDivision.id,
        name: currentPageDivision.name,
        slug: slug,
        country: currentPageDivision.country?.iso3 || countryCode,
        parent: currentPageDivision.parent,
        boundary_type: currentPageDivision.boundary_type,
        admin_level: currentPageDivision.admin_level,
        community_id: currentPageDivision.community_id,  // Include community ID
        community_slug: currentPageDivision.community_slug  // Include community slug
      });
    }
    // Priority 2: Use activeMunicipality from context if no page division yet
    else if (activeMunicipality && !selectedMunicipality) {
      setSelectedMunicipality(activeMunicipality);
      // Mark as set so fetchNeighbors doesn't override
      initialMunicipalitySetRef.current = true;

      // Store in localStorage as well
      const slug = getMunicipalitySlug(activeMunicipality.name || activeMunicipality.nom);
      setCurrentDivision({
        id: activeMunicipality.id,
        name: activeMunicipality.name || activeMunicipality.nom,
        slug: slug,
        country: countryCode,
        parent: activeMunicipality.region ? { name: activeMunicipality.region } : null,
        boundary_type: activeMunicipality.boundary_type,
        admin_level: activeMunicipality.admin_level
      });
    }
    // Note: If userDivisionId exists, selectedMunicipality will be set by fetchNeighbors
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPageDivision?.id, activeMunicipality?.id]); // Use IDs instead of objects to avoid reference issues

  // Fermer le dropdown quand on clique à l'extérieur
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (selectorRef.current && !selectorRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm('');
      }

      // Close country dropdown if clicking outside
      if (countryDropdownRef.current && !countryDropdownRef.current.contains(event.target)) {
        setIsCountryDropdownOpen(false);
        setCountrySearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus sur l'input de recherche quand le dropdown s'ouvre
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  const handleSelectorClick = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      setSearchTerm('');
      // Show neighbors when opening dropdown
      if (neighbors.length === 0 && activeMunicipality?.id && !isLoadingNeighbors) {
        // Trigger neighbors fetch if not already loaded
      }
    }
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleCountryDropdownToggle = () => {
    setIsCountryDropdownOpen(!isCountryDropdownOpen);
    if (!isCountryDropdownOpen) {
      setCountrySearchTerm('');
    }
  };

  const handleCountrySearchChange = (e) => {
    setCountrySearchTerm(e.target.value);
  };

  const handleCountryChange = (country) => {
    setSelectedCountry(country);
    setPreferredCountry(country.iso3);

    // Clear search and selections when country changes
    setSearchTerm('');
    setSearchResults([]);
    setNeighbors([]);
    setSelectedMunicipality(null);
    setIsCountryDropdownOpen(false);
    setCountrySearchTerm('');  };

  const handleMunicipalitySelect = (municipality) => {
    setSelectedMunicipality(municipality);
    setIsOpen(false);
    setSearchTerm('');

    // Mettre à jour le contexte avec le nom, ID ET country
    switchMunicipality(
      municipality.nom || municipality.name,
      municipality.id,
      {
        country: countryCode,
        boundary_type: municipality.boundary_type,
        admin_level: municipality.admin_level,
        region: municipality.region,
        community_id: municipality.community_id  // Include community ID
      }
    );

    // Store as current active division (single source of truth)
    const municipalityName = municipality.nom || municipality.name;
    const slug = getMunicipalitySlug(municipalityName);

    const divisionToStore = {
      id: municipality.id,
      name: municipalityName,
      slug: slug,
      country: countryCode,
      parent: municipality.region ? { name: municipality.region } : null,
      boundary_type: municipality.boundary_type,
      admin_level: municipality.admin_level,
      community_id: municipality.community_id  // Include community ID
    };
    setCurrentDivision(divisionToStore);

    // Verify it was stored
    setTimeout(() => {
      const stored = localStorage.getItem('currentActiveDivision');    }, 100);

    // Naviguer vers la nouvelle division avec le bon URL path basé sur le pays
    const urlPath = getUrlPathByISO3(countryCode);    navigate(`/${urlPath}/${slug}/accueil`);

    // Appeler onChange seulement si elle est définie
    if (onChange && typeof onChange === 'function') {
      onChange(municipalityName);
    }
  };

  const getColorForMunicipality = (municipality) => {
    const colors = [
      '#84CC16', '#06B6D4', '#8B5CF6', '#F59E0B',
      '#EF4444', '#10B981', '#F97316', '#3B82F6'
    ];
    const index = municipality.nom.charCodeAt(0) % colors.length;
    return colors[index];
  };

  return (
    <div className={`${styles.municipalitySelector} ${className}`} ref={selectorRef}>
      {/* En-tête avec icône */}
      <div className={styles.selectorHeader}>
        <LocationOn className={styles.locationIcon} />
        <span className={styles.selectorTitle}>{adminLabels.singular}</span>
      </div>

      {/* Country Selector */}
      {!loadingCountries && countries.length > 0 && (
        <div className={styles.countrySelectorWrapper} ref={countryDropdownRef}>
          {showCountrySearch ? (
            // Searchable dropdown for > 20 countries
            <div className={styles.countrySelector}>
              <Public className={styles.countryIcon} />
              <button
                type="button"
                className={styles.countryButton}
                onClick={handleCountryDropdownToggle}
              >
                <span className={styles.countryName}>
                  {selectedCountry?.name || 'Select country'}
                </span>
                <ExpandMore className={`${styles.countryExpandIcon} ${isCountryDropdownOpen ? styles.open : ''}`} />
              </button>

              {isCountryDropdownOpen && (
                <div className={styles.countryDropdown}>
                  {/* Search input */}
                  <div className={styles.countrySearchBox}>
                    <input
                      type="text"
                      className={styles.countrySearchInput}
                      placeholder="Search countries..."
                      value={countrySearchTerm}
                      onChange={handleCountrySearchChange}
                      autoFocus
                    />
                  </div>

                  {/* Countries list */}
                  <div className={styles.countryList}>
                    {filteredCountries.length > 0 ? (
                      filteredCountries.map(country => (
                        <button
                          key={country.id}
                          type="button"
                          className={`${styles.countryOption} ${selectedCountry?.id === country.id ? styles.selected : ''}`}
                          onClick={() => handleCountryChange(country)}
                        >
                          <span className={styles.countryOptionName}>{country.name}</span>
                          {selectedCountry?.id === country.id && (
                            <Check className={styles.checkIcon} />
                          )}
                        </button>
                      ))
                    ) : (
                      <div className={styles.noResults}>
                        No countries found
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            // Simple select for ≤ 20 countries
            <div className={styles.countrySelector}>
              <Public className={styles.countryIcon} />
              <select
                className={styles.countryDropdownSelect}
                value={selectedCountry?.id || ''}
                onChange={(e) => {
                  const country = countries.find(c => c.id === e.target.value);
                  if (country) handleCountryChange(country);
                }}
              >
                {countries.map(country => (
                  <option key={country.id} value={country.id}>
                    {country.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {/* Visual indicator if browsing different country */}
      {isBrowsingDifferentCountry(user) && selectedCountry && (
        <div className={styles.countryIndicator}>
          🌍 Browsing: {selectedCountry.name}
        </div>
      )}

      {/* Bouton principal du sélecteur */}
      <button
        type="button"
        className={`${styles.selectorButton} ${isOpen ? styles.open : ''}`}
        onClick={handleSelectorClick}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <div className={styles.selectedMunicipality}>
          {selectedMunicipality ? (
            <>
              <div
                className={styles.colorIndicator}
                style={{ backgroundColor: getColorForMunicipality(selectedMunicipality) }}
              />
              <div className={styles.municipalityInfo}>
                <div className={styles.municipalityName}>
                  {selectedMunicipality.nom}
                </div>
                <div className={styles.municipalityRegion}>
                  {selectedMunicipality.region}
                </div>
              </div>
            </>
          ) : (
            <div className={styles.municipalityInfo}>
              <div className={styles.municipalityName} style={{ color: '#64748B' }}>
                {dynamicPlaceholder}
              </div>
            </div>
          )}
        </div>
        <ExpandMore className={`${styles.expandIcon} ${isOpen ? styles.rotated : ''}`} />
      </button>

      {/* Menu déroulant avec recherche */}
      <div className={`${styles.dropdownMenu} ${isOpen ? styles.show : ''}`}>
        <div className={styles.searchWrapper}>
          <input
            ref={searchInputRef}
            type="text"
            value={searchTerm}
            onChange={handleSearchChange}
                      placeholder={`Rechercher une ${adminLabels.singular}...`}
            className={styles.searchInput}
          />
          <LocationOn className={styles.searchIcon} />
        </div>

        <div className={styles.dropdownContent}>
          {(isLoadingNeighbors || isSearching) ? (
            <div className={styles.loadingState}>
              <div className={styles.loadingSpinner} />
              {isSearching ? 'Recherche...' : 'Chargement...'}
            </div>
          ) : municipalities.length > 0 ? (
            municipalities.map((municipality, index) => {
              const municipalityName = municipality.nom || municipality.name;
              const isSelected = selectedMunicipality?.nom === municipalityName || selectedMunicipality?.name === municipalityName;
              const isCurrent = municipality.isCurrent;

              return (
                <button
                  key={municipality.id || municipality.nom || index}
                  type="button"
                  className={`${styles.municipalityOption} ${isSelected ? styles.selected : ''} ${isCurrent ? styles.currentDivision : ''}`}
                  onClick={() => handleMunicipalitySelect(municipality)}
                >
                  <div className={styles.optionContent}>
                    <div
                      className={styles.optionColorIndicator}
                      style={{ backgroundColor: getColorForMunicipality(municipality) }}
                    />
                    <div className={styles.optionInfo}>
                      <div className={styles.optionName}>
                        {municipalityName}
                        {isCurrent && <span className={styles.currentBadge}> (Actuelle)</span>}
                      </div>
                      <div className={styles.optionDetails}>
                        {municipality.region}
                        {municipality.distance_km && (
                          <> • {municipality.distance_km}km</>
                        )}
                        {municipality.population && (
                          <> • {municipality.population.toLocaleString('fr-CA')} hab.</>
                        )}
                      </div>
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
              {searchTerm ? `Aucune municipalité trouvée pour "${searchTerm}"` : 'Aucune municipalité disponible'}
            </div>
          )}
        </div>
      </div>

      {error && <div className={styles.errorText}>{error}</div>}
    </div>
  );
};

export default MunicipalitySelector;