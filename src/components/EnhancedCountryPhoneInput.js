/**
 * Enhanced Country Phone Input Component
 *
 * Features:
 * - Auto-detects user's country from IP
 * - Shows detected country + regional countries
 * - Searchable dropdown with all 242 countries
 * - Flag emojis and phone codes
 * - Real-time phone number formatting
 * - Validation feedback
 */

import React, { useState, useEffect, useRef } from 'react';
import { Form } from 'react-bootstrap';
import { Search as SearchIcon, Phone as PhoneIcon, ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import countryService from '../services/countryService';
import { formatAsYouType } from '../utils/phoneValidation';
import styles from './EnhancedCountryPhoneInput.module.css';

const EnhancedCountryPhoneInput = ({
  value = '',
  selectedCountry = null,
  onChange = () => {},
  onCountryChange = () => {},
  error = '',
  required = false,
  placeholder = '',
  autoDetect = true,
  className = ''
}) => {
  const [countries, setCountries] = useState([]);
  const [detectedCountry, setDetectedCountry] = useState(null);
  const [regionalCountries, setRegionalCountries] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(true);
  const [phoneValue, setPhoneValue] = useState(value);
  const [currentCountry, setCurrentCountry] = useState(selectedCountry);

  const dropdownRef = useRef(null);
  const searchInputRef = useRef(null);

  useEffect(() => {
    if (autoDetect) {
      loadLocationData();
    } else {
      loadAllCountries();
    }

    // Click outside handler
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
        setSearchQuery('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [autoDetect]);

  useEffect(() => {
    // Update internal state when external value/country changes
    setPhoneValue(value);
    setCurrentCountry(selectedCountry);
  }, [value, selectedCountry]);

  const loadLocationData = async () => {
    setLoading(true);
    try {      const data = await countryService.getUserLocationData();

      if (data.success && data.country) {
        setDetectedCountry(data.country);
        setRegionalCountries(data.regional_countries || []);

        // Build country list: detected + regional
        const countryList = [
          data.country,
          ...(data.regional_countries || [])
        ];
        setCountries(countryList);

        // Auto-select detected country if no country selected yet
        if (!currentCountry) {
          setCurrentCountry(data.country);
          onCountryChange(data.country);
        }
      } else {        await loadAllCountries();
      }
    } catch (error) {      await loadAllCountries();
    } finally {
      setLoading(false);
    }
  };

  const loadAllCountries = async () => {
    setLoading(true);
    try {
      const data = await countryService.getAllCountries();

      if (data.success) {
        setCountries(data.countries || []);
      }
    } catch (error) {    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query) => {
    setSearchQuery(query);

    if (query.length < 2) {
      // Reset to detected + regional countries
      if (detectedCountry) {
        setCountries([detectedCountry, ...regionalCountries]);
      } else {
        await loadAllCountries();
      }
      return;
    }

    try {
      const data = await countryService.searchCountries(query);

      if (data.success) {
        setCountries(data.countries || []);
      }
    } catch (error) {    }
  };

  const handleCountrySelect = (country) => {    setCurrentCountry(country);
    setShowDropdown(false);
    setSearchQuery('');

    // Reset to detected + regional countries
    if (detectedCountry) {
      setCountries([detectedCountry, ...regionalCountries]);
    }

    // Notify parent
    onCountryChange(country);
  };

  const handlePhoneChange = (e) => {
    const inputValue = e.target.value;

    // Format as user types if country selected
    let formatted = inputValue;
    if (currentCountry && currentCountry.iso2) {
      formatted = formatAsYouType(inputValue, currentCountry.iso2);
    }

    setPhoneValue(formatted);

    // Notify parent with full number
    onChange(formatted, currentCountry);
  };

  const handleDropdownToggle = () => {
    setShowDropdown(!showDropdown);

    // Focus search input when dropdown opens
    if (!showDropdown) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 100);
    }
  };

  const getPlaceholder = () => {
    if (placeholder) return placeholder;

    if (!currentCountry) return 'Enter phone number';

    // Country-specific placeholders
    const placeholders = {
      'CA': '514 123 4567',
      'US': '555 123 4567',
      'BJ': '97 12 34 56',
      'FR': '06 12 34 56 78',
      'GB': '07700 123456'
    };

    return `Ex: ${placeholders[currentCountry.iso2] || '...'}`;
  };

  return (
    <div className={`${styles.phoneInputContainer} ${className}`}>
      {/* Country Selector */}
      <div className={styles.countrySelector} ref={dropdownRef}>
        <button
          type="button"
          onClick={handleDropdownToggle}
          className={`${styles.countrySelectorButton} ${error ? styles.error : ''}`}
          disabled={loading}
        >
          {loading ? (
            <span className={styles.loading}>...</span>
          ) : currentCountry ? (
            <>
              <span className={styles.flag}>{currentCountry.flag_emoji}</span>
              <span className={styles.dialCode}>{currentCountry.phone_code}</span>
            </>
          ) : (
            <span className={styles.placeholder}>Select</span>
          )}
          <ExpandMoreIcon className={styles.chevron} />
        </button>

        {/* Dropdown */}
        {showDropdown && (
          <div className={styles.dropdown}>
            {/* Search Input */}
            <div className={styles.searchContainer}>
              <SearchIcon className={styles.searchIcon} />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search countries..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className={styles.searchInput}
              />
            </div>

            {/* Country List */}
            <div className={styles.countryList}>
              {countries.length > 0 ? (
                <>
                  {/* Show detected country label if applicable */}
                  {!searchQuery && detectedCountry && (
                    <div className={styles.sectionLabel}>
                      {currentCountry?.iso3 === detectedCountry.iso3 ? '✓ ' : ''}
                      Detected: {detectedCountry.name}
                    </div>
                  )}

                  {countries.map((country) => (
                    <button
                      key={country.iso3}
                      type="button"
                      onClick={() => handleCountrySelect(country)}
                      className={`${styles.countryItem} ${
                        currentCountry?.iso3 === country.iso3 ? styles.selected : ''
                      }`}
                    >
                      <span className={styles.flag}>{country.flag_emoji}</span>
                      <span className={styles.countryName}>{country.name}</span>
                      <span className={styles.dialCode}>{country.phone_code}</span>
                      {country.region && (
                        <span className={styles.region}>{country.region}</span>
                      )}
                    </button>
                  ))}

                  {/* Show regional label if applicable */}
                  {!searchQuery && regionalCountries.length > 0 && (
                    <div className={styles.sectionLabel}>
                      Regional countries
                    </div>
                  )}
                </>
              ) : (
                <div className={styles.noResults}>
                  {loading ? 'Loading...' : 'No countries found'}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Phone Number Input */}
      <div className={styles.phoneInputWrapper}>
        <Form.Control
          type="tel"
          value={phoneValue}
          onChange={handlePhoneChange}
          placeholder={getPlaceholder()}
          className={`${styles.phoneInput} ${error ? styles.error : ''}`}
          required={required}
          autoComplete="tel"
        />
        <PhoneIcon className={styles.phoneIcon} />
      </div>
    </div>
  );
};

export default EnhancedCountryPhoneInput;
