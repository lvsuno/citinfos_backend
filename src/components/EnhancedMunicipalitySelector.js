import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  LocationOn,
  ExpandMore,
  Check,
  Search,
  Close
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useMunicipality } from '../contexts/MunicipalityContext';
import { searchMunicipalities } from '../data/municipalitiesUtils';
import geolocationService from '../services/geolocationService';
import styles from './EnhancedMunicipalitySelector.module.css';

const EnhancedMunicipalitySelector = ({
  value = '',
  onChange = () => { },
  placeholder = "Sélectionner une municipalité",
  error = '',
  required = false,
  className = '',
  autoDetectLocation = false,
  disableNavigation = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMunicipality, setSelectedMunicipality] = useState(null);
  const [locationData, setLocationData] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);


  const selectorRef = useRef(null);
  const searchInputRef = useRef(null);
  const hasRunInitialDetection = useRef(false);
  const navigate = useNavigate();
  const { activeMunicipality, switchMunicipality, getMunicipalitySlug } = useMunicipality();

  // Define detectUserLocation function
  const detectUserLocation = useCallback(async () => {
    console.log('🔄 Making backend call: getUserLocationData()');

    try {
      const result = await geolocationService.getUserLocationData();
      console.log('📍 Location result:', result);

      if (result.success && result.closestDivisions && result.closestDivisions.length > 0) {
        setLocationData(result);

        // Auto-select the closest division
        const closestDivision = result.closestDivisions[0];
        const divisionName = closestDivision.name;

        console.log('✨ Auto-selecting closest division:', divisionName);

        // Set the selected municipality and update the form
        const municipalityObj = {
          id: closestDivision.id,
          name: divisionName,
          region: closestDivision.parent_name,
          distance_km: closestDivision.distance_km
        };

        setSelectedMunicipality(municipalityObj);
        // Pass both the division name and the division data with ID
        onChange(divisionName, closestDivision);
      } else {
        console.log('⚠️ Location detection failed or no close divisions found');
      }
    } catch (error) {
      console.error('❌ Location detection error:', error);
    }
  }, [onChange]);

  // Auto-detect location on component mount if enabled
  useEffect(() => {
    // Only run auto-detection once per component lifetime
    if (autoDetectLocation && !locationData && !selectedMunicipality && !hasRunInitialDetection.current) {
      hasRunInitialDetection.current = true;
      detectUserLocation();
    }
  }, [autoDetectLocation, detectUserLocation, locationData, selectedMunicipality]);

  // Handle initial selection
  useEffect(() => {
    if (activeMunicipality && !selectedMunicipality) {
      setSelectedMunicipality(activeMunicipality);
    } else if (value && !selectedMunicipality) {
      const municipality = searchMunicipalities(value, 1)[0];
      if (municipality) {
        setSelectedMunicipality(municipality);
      }
    }
  }, [value, selectedMunicipality, activeMunicipality]);

  // Search divisions when search term changes
  useEffect(() => {
    const searchDivisions = async () => {
      if (searchTerm.length < 2) {
        setSearchResults([]);
        return;
      }

      if (!locationData?.country) {
        // Fallback to local search if no country detected
        const localResults = searchMunicipalities(searchTerm, 10);
        setSearchResults(localResults.map(m => ({
          id: m.id || m.nom,
          name: m.nom,
          parent_name: m.region,
          boundary_type: 'municipalités',
          distance_km: null,
          admin_code: null
        })));
        return;
      }

      setIsSearching(true);
      try {
        const result = await geolocationService.searchDivisions(
          locationData.country.iso3,
          searchTerm,
          15
        );

        if (result.success) {
          setSearchResults(result.results);
        } else {
          console.error('Search failed:', result.error);
          // Fallback to local search
          const localResults = searchMunicipalities(searchTerm, 10);
          setSearchResults(localResults.map(m => ({
            id: m.id || m.nom,
            name: m.nom,
            parent_name: m.region,
            boundary_type: 'municipalités',
            distance_km: null,
            admin_code: null
          })));
        }
      } catch (error) {
        console.error('Error searching divisions:', error);
      } finally {
        setIsSearching(false);
      }
    };

    const debounceTimer = setTimeout(searchDivisions, 300);
    return () => clearTimeout(debounceTimer);
  }, [searchTerm, locationData]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (selectorRef.current && !selectorRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);



  const handleSelectorClick = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      setSearchTerm('');
      // Show closest divisions if available
      if (locationData?.closestDivisions) {
        setSearchResults(locationData.closestDivisions);
      }
    }
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleDivisionSelect = (division) => {
    if (!division) {
      console.error('Division is undefined in handleDivisionSelect');
      return;
    }

    const divisionName = division.name || division.nom || 'Unknown';
    const municipalityData = {
      id: division.id || `division-${Date.now()}`,
      nom: divisionName,
      name: divisionName,
      region: division.parent_name || locationData?.country?.name || '',
      boundary_type: division.boundary_type || '',
      distance_km: division.distance_km || null
    };

    setSelectedMunicipality(municipalityData);
    setIsOpen(false);
    setSearchTerm('');

    // Update context and navigate only if navigation is not disabled
    if (!disableNavigation) {
      if (switchMunicipality && typeof switchMunicipality === 'function') {
        switchMunicipality(divisionName);
      }

      // Navigate to new municipality if getMunicipalitySlug is available
      if (getMunicipalitySlug && typeof getMunicipalitySlug === 'function') {
        try {
          const slug = getMunicipalitySlug(divisionName);
          if (slug && navigate) {
            navigate(`/municipality/${slug}`);
          }
        } catch (error) {
          console.error('Error getting municipality slug:', error);
        }
      }
    }

    // Call onChange callback with both name and division data
    if (onChange && typeof onChange === 'function') {
      onChange(divisionName, division);
    }
  };

  const clearSelection = () => {
    setSelectedMunicipality(null);
    setSearchTerm('');
    if (onChange && typeof onChange === 'function') {
      onChange('', null);
    }
  };

  const getColorForMunicipality = (name) => {
    const colors = [
      '#84CC16', '#06B6D4', '#8B5CF6', '#F59E0B',
      '#EF4444', '#10B981', '#F97316', '#3B82F6'
    ];

    // Handle undefined or empty names
    if (!name || typeof name !== 'string' || name.length === 0) {
      return colors[0]; // Default to first color
    }

    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };



  const renderDivisionOption = (division) => {
    const distance = geolocationService.formatDistance(division.distance_km);

    return (
      <button
        key={division.id}
        type="button"
        className={`${styles.divisionOption} ${
          selectedMunicipality?.id === division.id ? styles.selected : ''
        }`}
        onClick={() => handleDivisionSelect(division)}
      >
        <div className={styles.optionContent}>
          <div
            className={styles.optionColorIndicator}
            style={{ backgroundColor: getColorForMunicipality(division.name || division.nom) }}
          />
          <div className={styles.optionInfo}>
            <div className={styles.optionName}>{division.name}</div>
            <div className={styles.optionDetails}>
              {division.parent_name && (
                <span className={styles.parentName}>{division.parent_name}</span>
              )}
              {distance && (
                <span className={styles.distance}> • {distance}</span>
              )}
              {division.boundary_type && (
                <span className={styles.boundaryType}> • {division.boundary_type}</span>
              )}
            </div>
          </div>
        </div>
        {selectedMunicipality?.id === division.id && (
          <Check className={styles.checkIcon} />
        )}
      </button>
    );
  };

  return (
    <div className={`${styles.municipalitySelector} ${className}`} ref={selectorRef}>
      {/* Header with icon */}
      <div className={styles.selectorHeader}>
        <LocationOn className={styles.locationIcon} />
        <span className={styles.selectorTitle}>Municipalité</span>
      </div>



      {/* Main selector button with clear button positioned outside */}
      <div className={styles.selectorContainer}>
        <button
          type="button"
          className={`${styles.selectorButton} ${isOpen ? styles.open : ''} ${error ? styles.error : ''}`}
          onClick={handleSelectorClick}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
        >
          <div className={styles.selectedMunicipality}>
            {selectedMunicipality ? (
              <>
                <div
                  className={styles.colorIndicator}
                  style={{ backgroundColor: getColorForMunicipality(selectedMunicipality.name || selectedMunicipality.nom) }}
                />
                <div className={styles.municipalityInfo}>
                  <div className={styles.municipalityName}>
                    {selectedMunicipality.name || selectedMunicipality.nom}
                  </div>
                  <div className={styles.municipalityRegion}>
                    {selectedMunicipality.region}
                    {selectedMunicipality.distance_km && (
                      <span className={styles.distance}>
                        {' • '}{geolocationService.formatDistance(selectedMunicipality.distance_km)}
                      </span>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className={styles.municipalityInfo}>
                <div className={styles.municipalityName} style={{ color: '#64748B' }}>
                  {placeholder}
                </div>
              </div>
            )}
          </div>
          <ExpandMore className={`${styles.expandIcon} ${isOpen ? styles.rotated : ''}`} />
        </button>

        {/* Clear button positioned outside the main button */}
        {selectedMunicipality && (
          <button
            type="button"
            className={styles.clearButton}
            onClick={(e) => {
              e.stopPropagation();
              clearSelection();
            }}
          >
            <Close className={styles.clearIcon} />
          </button>
        )}
      </div>

      {/* Dropdown menu */}
      <div className={`${styles.dropdownMenu} ${isOpen ? styles.show : ''}`}>
        <div className={styles.searchWrapper}>
          <input
            ref={searchInputRef}
            type="text"
            value={searchTerm}
            onChange={handleSearchChange}
            placeholder="Rechercher une municipalité..."
            className={styles.searchInput}
          />
          <Search className={styles.searchIcon} />
        </div>

        <div className={styles.dropdownContent}>
          {/* Loading state */}
          {isSearching && (
            <div className={styles.loadingState}>
              <div className={styles.loadingSpinner} />
              Recherche en cours...
            </div>
          )}

          {/* Results */}
          {!isSearching && searchResults.length > 0 ? (
            searchResults.map(renderDivisionOption)
          ) : !isSearching && searchTerm.length >= 2 ? (
            <div className={styles.noResults}>
              Aucune municipalité trouvée pour "{searchTerm}"
            </div>
          ) : !isSearching && !searchTerm && (!locationData?.closestDivisions?.length) ? (
            <div className={styles.noResults}>
              Aucune municipalité disponible
            </div>
          ) : null}
        </div>
      </div>

      {error && <div className={styles.errorText}>{error}</div>}
    </div>
  );
};

export default EnhancedMunicipalitySelector;