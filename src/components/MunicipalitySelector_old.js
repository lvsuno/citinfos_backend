import React, { useState, useEffect, useRef } from 'react';
import { LocationOn, ExpandMore, Check } from '@mui/icons-material';
import { searchMunicipalities, getAllMunicipalities } from '../data/municipalitiesUtils';
import styles from './MunicipalitySelector.module.css';

const MunicipalitySelector = ({ 
  value = '', 
  onChange, 
  placeholder = "Sélectionner une municipalité",
  error = '',
  required = false,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMunicipality, setSelectedMunicipality] = useState(null);
  const selectorRef = useRef(null);
  const searchInputRef = useRef(null);

  // Obtenir toutes les municipalités ou les résultats filtrés
  const municipalities = searchTerm 
    ? searchMunicipalities(searchTerm, 15) 
    : getAllMunicipalities().slice(0, 15);

  // Gérer la sélection initiale
  useEffect(() => {
    if (value && !selectedMunicipality) {
      const municipality = searchMunicipalities(value, 1)[0];
      if (municipality) {
        setSelectedMunicipality(municipality);
      }
    }
  }, [value, selectedMunicipality]);

  // Fermer le dropdown quand on clique à l'extérieur
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
    }
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleMunicipalitySelect = (municipality) => {
    setSelectedMunicipality(municipality);
    setIsOpen(false);
    setSearchTerm('');
    onChange(municipality.nom);
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
        <span className={styles.selectorTitle}>Municipalité</span>
      </div>

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
                {placeholder}
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
            placeholder="Rechercher une municipalité..."
            className={styles.searchInput}
          />
          <LocationOn className={styles.searchIcon} />
        </div>
        
        <div className={styles.dropdownContent}>
          {municipalities.length > 0 ? (
            municipalities.map((municipality) => (
              <button
                key={municipality.nom}
                type="button"
                className={`${styles.municipalityOption} ${
                  selectedMunicipality?.nom === municipality.nom ? styles.selected : ''
                }`}
                onClick={() => handleMunicipalitySelect(municipality)}
              >
                <div className={styles.optionContent}>
                  <div 
                    className={styles.optionColorIndicator}
                    style={{ backgroundColor: getColorForMunicipality(municipality) }}
                  />
                  <div className={styles.optionInfo}>
                    <div className={styles.optionName}>{municipality.nom}</div>
                    <div className={styles.optionDetails}>
                      {municipality.region}
                      {municipality.population && (
                        <> • {municipality.population.toLocaleString('fr-CA')} hab.</>
                      )}
                    </div>
                  </div>
                </div>
                {selectedMunicipality?.nom === municipality.nom && (
                  <Check className={styles.checkIcon} />
                )}
              </button>
            ))
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