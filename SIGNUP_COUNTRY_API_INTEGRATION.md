# Signup Page Country Selection API Integration

## Overview

The backend now provides comprehensive API endpoints to support intelligent country selection on the signup page. The system automatically detects the user's country and loads regional countries for easy selection, with full search capabilities.

## Key Features

✅ **Auto-detection**: Detects user's country based on IP geolocation
✅ **Regional Loading**: Shows countries from the same region as detected country
✅ **Search Functionality**: Search countries by name, ISO2, or ISO3 code
✅ **Phone Data**: All countries include phone codes, flags, and regions
✅ **Caching**: Redis caching for fast response times
✅ **242 Countries**: Complete worldwide coverage

---

## API Endpoints

### 1. Get User Location Data (Enhanced)

**Endpoint**: `POST /api/auth/location-data/`

**Purpose**: Detect user's location and return regional countries for signup

**Request**:
```json
{
  "ip_address": "optional - uses request IP if not provided"
}
```

**Response**:
```json
{
  "success": true,
  "country": {
    "iso3": "BEN",
    "iso2": "BJ",
    "name": "Benin",
    "phone_code": "+229",
    "flag_emoji": "🇧🇯",
    "region": "West Africa",
    "default_admin_level": 3,
    "default_division_name": "communes"
  },
  "user_location": {
    "latitude": 6.3703,
    "longitude": 2.3912,
    "administrative_division_id": "uuid",
    "division_name": "Cotonou",
    "region": "Littoral",
    "ip_address": "192.168.1.1"
  },
  "closest_divisions": [
    {
      "id": "uuid",
      "name": "Cotonou",
      "boundary_type": "communes",
      "distance_km": 0.5,
      "parent_name": "Littoral"
    }
    // ... 4 more
  ],
  "regional_countries": [
    {
      "iso2": "BF",
      "iso3": "BFA",
      "name": "Burkina Faso",
      "phone_code": "+226",
      "flag_emoji": "🇧🇫",
      "region": "West Africa"
    },
    {
      "iso2": "CI",
      "iso3": "CIV",
      "name": "Côte d'Ivoire",
      "phone_code": "+225",
      "flag_emoji": "🇨🇮",
      "region": "West Africa"
    }
    // ... up to 10 regional countries
  ],
  "country_search_info": {
    "search_endpoint": "/api/auth/countries/phone-data/",
    "region_filter": "West Africa",
    "total_in_region": 17
  }
}
```

**Usage in Signup Flow**:
1. Call this endpoint when signup page loads
2. Pre-select detected country in phone input
3. Populate country dropdown with detected + regional countries
4. Use for initial division suggestions

---

### 2. Get Countries with Phone Data

**Endpoint**: `GET /api/auth/countries/phone-data/`

**Purpose**: Search and filter countries for phone selection

**Query Parameters**:
- `region` (optional): Filter by region (e.g., "West Africa", "North America")
- `search` (optional): Search by name, ISO2, or ISO3 code
- `iso3` (optional): Get specific country by ISO3 code

**Examples**:

**Get all countries**:
```
GET /api/auth/countries/phone-data/
```

**Filter by region**:
```
GET /api/auth/countries/phone-data/?region=West+Africa
```

**Search by name**:
```
GET /api/auth/countries/phone-data/?search=ben
```

**Get specific country**:
```
GET /api/auth/countries/phone-data/?iso3=CAN
```

**Response**:
```json
{
  "success": true,
  "countries": [
    {
      "iso2": "BJ",
      "iso3": "BEN",
      "name": "Benin",
      "phone_code": "+229",
      "flag_emoji": "🇧🇯",
      "region": "West Africa"
    },
    {
      "iso2": "BF",
      "iso3": "BFA",
      "name": "Burkina Faso",
      "phone_code": "+226",
      "flag_emoji": "🇧🇫",
      "region": "West Africa"
    }
    // ... more countries
  ],
  "count": 17,
  "region": "West Africa"  // if filtered
}
```

**Caching**: 1 hour

---

### 3. Get Available Regions

**Endpoint**: `GET /api/auth/countries/regions/`

**Purpose**: Get list of all regions with country counts

**Response**:
```json
{
  "success": true,
  "regions": [
    {
      "name": "West Africa",
      "country_count": 17,
      "sample_countries": ["Benin", "Burkina Faso", "Côte d'Ivoire"]
    },
    {
      "name": "North America",
      "country_count": 6,
      "sample_countries": ["Canada", "United States", "Mexico"]
    }
    // ... 18 more regions
  ],
  "count": 20
}
```

**Usage**:
- Build region filter dropdown
- Show country distribution stats
- Group countries by region in UI

**Caching**: 24 hours

---

## Frontend Implementation Guide

### React/Next.js Example

```javascript
// services/countryService.js
import api from './api';

export const countryService = {
  // Get user location and regional countries
  async getUserLocationData() {
    const response = await api.post('/api/auth/location-data/');
    return response.data;
  },

  // Search countries
  async searchCountries(query) {
    const response = await api.get('/api/auth/countries/phone-data/', {
      params: { search: query }
    });
    return response.data;
  },

  // Get countries by region
  async getCountriesByRegion(region) {
    const response = await api.get('/api/auth/countries/phone-data/', {
      params: { region }
    });
    return response.data;
  },

  // Get all regions
  async getRegions() {
    const response = await api.get('/api/auth/countries/regions/');
    return response.data;
  },

  // Get specific country
  async getCountry(iso3) {
    const response = await api.get('/api/auth/countries/phone-data/', {
      params: { iso3 }
    });
    return response.data;
  }
};
```

### Signup Page Component

```javascript
// pages/signup.jsx
import { useState, useEffect } from 'react';
import { countryService } from '@/services/countryService';
import PhoneInput from '@/components/PhoneInput';

export default function SignupPage() {
  const [detectedCountry, setDetectedCountry] = useState(null);
  const [countries, setCountries] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLocationData();
  }, []);

  const loadLocationData = async () => {
    try {
      const data = await countryService.getUserLocationData();

      if (data.success) {
        // Set detected country
        setDetectedCountry(data.country);

        // Build country list: detected + regional + search endpoint
        const countryList = [
          data.country,
          ...data.regional_countries
        ];

        setCountries(countryList);
      }
    } catch (error) {
      console.error('Failed to load location data:', error);
      // Fallback: load all countries
      loadAllCountries();
    } finally {
      setLoading(false);
    }
  };

  const loadAllCountries = async () => {
    try {
      const data = await countryService.searchCountries('');
      if (data.success) {
        setCountries(data.countries);
      }
    } catch (error) {
      console.error('Failed to load countries:', error);
    }
  };

  const handleCountrySearch = async (query) => {
    setSearchQuery(query);

    if (query.length < 2) {
      // Reset to regional countries
      loadLocationData();
      return;
    }

    try {
      const data = await countryService.searchCountries(query);
      if (data.success) {
        setCountries(data.countries);
      }
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  return (
    <div className="signup-page">
      <h1>Sign Up</h1>

      {loading ? (
        <div>Loading location data...</div>
      ) : (
        <form>
          {/* Phone Number Input with Country Selection */}
          <PhoneInput
            countries={countries}
            defaultCountry={detectedCountry}
            onSearch={handleCountrySearch}
            onChange={(value) => console.log('Phone:', value)}
          />

          {/* Other signup fields */}
        </form>
      )}
    </div>
  );
}
```

### Phone Input Component

```javascript
// components/PhoneInput.jsx
import { useState, useRef, useEffect } from 'react';

export default function PhoneInput({
  countries = [],
  defaultCountry = null,
  onSearch,
  onChange
}) {
  const [selectedCountry, setSelectedCountry] = useState(defaultCountry);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (defaultCountry && !selectedCountry) {
      setSelectedCountry(defaultCountry);
    }
  }, [defaultCountry]);

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);

    // Trigger backend search
    if (onSearch) {
      onSearch(query);
    }
  };

  const handleCountrySelect = (country) => {
    setSelectedCountry(country);
    setShowDropdown(false);
    setSearchQuery('');

    // Notify parent
    if (onChange) {
      onChange({
        country,
        phoneNumber,
        fullNumber: `${country.phone_code}${phoneNumber}`
      });
    }
  };

  const handlePhoneChange = (e) => {
    const value = e.target.value.replace(/\D/g, ''); // Only digits
    setPhoneNumber(value);

    if (onChange && selectedCountry) {
      onChange({
        country: selectedCountry,
        phoneNumber: value,
        fullNumber: `${selectedCountry.phone_code}${value}`
      });
    }
  };

  return (
    <div className="phone-input">
      <label>Phone Number</label>

      <div className="phone-input-container">
        {/* Country Selector */}
        <div className="country-selector">
          <button
            type="button"
            onClick={() => setShowDropdown(!showDropdown)}
            className="country-selector-button"
          >
            {selectedCountry ? (
              <>
                <span className="flag">{selectedCountry.flag_emoji}</span>
                <span className="code">{selectedCountry.phone_code}</span>
              </>
            ) : (
              <span>Select country</span>
            )}
            <svg className="chevron" viewBox="0 0 20 20">
              <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
            </svg>
          </button>

          {/* Dropdown */}
          {showDropdown && (
            <div className="country-dropdown">
              {/* Search Input */}
              <div className="dropdown-search">
                <input
                  type="text"
                  placeholder="Search countries..."
                  value={searchQuery}
                  onChange={handleSearchChange}
                  className="search-input"
                />
              </div>

              {/* Country List */}
              <div className="country-list">
                {countries.length > 0 ? (
                  countries.map((country) => (
                    <button
                      key={country.iso3}
                      type="button"
                      onClick={() => handleCountrySelect(country)}
                      className={`country-item ${
                        selectedCountry?.iso3 === country.iso3 ? 'selected' : ''
                      }`}
                    >
                      <span className="flag">{country.flag_emoji}</span>
                      <span className="name">{country.name}</span>
                      <span className="code">{country.phone_code}</span>
                    </button>
                  ))
                ) : (
                  <div className="no-results">
                    No countries found
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Phone Number Input */}
        <input
          type="tel"
          placeholder="Phone number"
          value={phoneNumber}
          onChange={handlePhoneChange}
          className="phone-number-input"
        />
      </div>

      {/* Helper Text */}
      {selectedCountry && (
        <div className="helper-text">
          {selectedCountry.region} • {selectedCountry.phone_code}
        </div>
      )}
    </div>
  );
}
```

### Styling (Tailwind CSS)

```css
/* styles/phoneInput.css */
.phone-input {
  @apply mb-4;
}

.phone-input label {
  @apply block text-sm font-medium text-gray-700 mb-2;
}

.phone-input-container {
  @apply flex border border-gray-300 rounded-md overflow-hidden focus-within:ring-2 focus-within:ring-blue-500;
}

.country-selector {
  @apply relative;
}

.country-selector-button {
  @apply flex items-center gap-2 px-3 py-2 bg-gray-50 border-r border-gray-300 hover:bg-gray-100 transition-colors;
}

.country-selector-button .flag {
  @apply text-xl;
}

.country-selector-button .code {
  @apply text-sm font-medium text-gray-700;
}

.country-selector-button .chevron {
  @apply w-4 h-4 fill-current text-gray-400;
}

.country-dropdown {
  @apply absolute top-full left-0 mt-1 w-72 bg-white border border-gray-300 rounded-md shadow-lg z-50 max-h-96 overflow-hidden;
}

.dropdown-search {
  @apply p-2 border-b border-gray-200;
}

.search-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent;
}

.country-list {
  @apply overflow-y-auto max-h-80;
}

.country-item {
  @apply w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-50 transition-colors text-left;
}

.country-item.selected {
  @apply bg-blue-50 text-blue-700;
}

.country-item .flag {
  @apply text-xl;
}

.country-item .name {
  @apply flex-1 text-sm font-medium;
}

.country-item .code {
  @apply text-sm text-gray-500;
}

.phone-number-input {
  @apply flex-1 px-4 py-2 border-0 focus:outline-none;
}

.helper-text {
  @apply mt-1 text-xs text-gray-500;
}

.no-results {
  @apply px-4 py-8 text-center text-sm text-gray-500;
}
```

---

## Implementation Checklist

### Backend (✅ Complete)
- ✅ Added phone fields to Country model
- ✅ Created country_data.py with 242 countries
- ✅ Populated database with phone data
- ✅ Created CountryPhoneDataSerializer
- ✅ Added get_countries_with_phone_data endpoint
- ✅ Added get_available_regions endpoint
- ✅ Enhanced get_user_location_data with regional countries
- ✅ Added search, region, and ISO3 filtering
- ✅ Implemented Redis caching
- ✅ Added URL routes

### Frontend (⏳ To Do)
- [ ] Create countryService API client
- [ ] Update PhoneInput component to use new API
- [ ] Add country search functionality
- [ ] Remove hardcoded COUNTRY_PHONE_CODES
- [ ] Implement regional country loading
- [ ] Add country dropdown with flags
- [ ] Handle loading states
- [ ] Add error handling
- [ ] Test with different IPs/locations

---

## Migration from Hardcoded Data

### Before (Frontend)
```javascript
// Old: Hardcoded in phoneValidation.js
const COUNTRY_PHONE_CODES = [
  { code: '+1', country: 'US', flag: '🇺🇸' },
  { code: '+229', country: 'BJ', flag: '🇧🇯' },
  // ... 240 more
];
```

### After (Backend API)
```javascript
// New: Dynamic from backend
const countries = await countryService.getUserLocationData();
// Returns detected country + regional countries + search capability
```

### Benefits
✅ **Single Source of Truth**: Backend manages all country data
✅ **Auto-updates**: Add countries without frontend deploy
✅ **Smart Loading**: Only load relevant countries (detected + regional)
✅ **Search**: Backend-powered search across 242 countries
✅ **Caching**: Fast response with Redis caching
✅ **Extensible**: Can add features like recent countries, favorites, etc.

---

## Testing

### Test Detected Country
```bash
curl -X POST http://localhost:8000/api/auth/location-data/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Test Country Search
```bash
# Search by name
curl "http://localhost:8000/api/auth/countries/phone-data/?search=canada"

# Filter by region
curl "http://localhost:8000/api/auth/countries/phone-data/?region=West+Africa"

# Get specific country
curl "http://localhost:8000/api/auth/countries/phone-data/?iso3=BEN"
```

### Test Regions
```bash
curl http://localhost:8000/api/auth/countries/regions/
```

---

## Performance

### Caching Strategy
- **Location Data**: Not cached (user-specific)
- **Country Search**: 1 hour cache per query
- **Regions List**: 24 hour cache
- **Regional Countries**: 1 hour cache per region

### Response Times (Estimated)
- First request: ~100-200ms (database query)
- Cached requests: ~5-10ms (Redis)
- Search queries: ~50-100ms (indexed search)

### Database Optimization
- `region` field is indexed for fast filtering
- Country queries use `.exclude()` for null phone codes
- Regional queries limited to 10 countries

---

## Support

For questions or issues:
1. Check API response format matches expected structure
2. Verify country data is populated: `docker compose exec backend python manage.py shell -c "from core.models import Country; print(Country.objects.exclude(phone_code__isnull=True).count())"`
3. Check Redis cache: `docker compose exec backend python manage.py shell -c "from django.core.cache import cache; print(cache.get('available_regions_v1'))"`
4. Review logs: `docker compose logs backend | grep -i country`

---

## Next Steps

1. ✅ **Backend Complete**: All endpoints ready and tested
2. ⏳ **Frontend Integration**: Update signup page to use new APIs
3. ⏳ **Remove Hardcoded Data**: Delete COUNTRY_PHONE_CODES from frontend
4. ⏳ **Testing**: Test signup flow with different locations
5. ⏳ **UI Polish**: Add loading states, animations, accessibility
6. ⏳ **Analytics**: Track country selection patterns
7. ⏳ **Optimization**: Monitor cache hit rates and API performance
