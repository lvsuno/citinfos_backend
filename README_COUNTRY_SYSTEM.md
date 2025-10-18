# 🌍 Country Phone Data System - Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Endpoints](#api-endpoints)
4. [Frontend Integration](#frontend-integration)
5. [Testing](#testing)
6. [Documentation](#documentation)

---

## Overview

This feature provides a complete country selection system for the signup page with:
- ✅ **242 countries** with phone codes, flags, and regions
- ✅ **Smart detection** based on user's IP location
- ✅ **Regional suggestions** (up to 10 countries from same region)
- ✅ **Fast search** with Redis caching
- ✅ **REST API** endpoints for frontend integration

### Key Benefits
- 🎯 **Intelligent**: Detects user's country automatically
- ⚡ **Fast**: Redis caching for sub-10ms responses
- 🔍 **Searchable**: Search by name, ISO2, or ISO3 code
- 🌐 **Complete**: 100% coverage of worldcities.csv countries
- 📦 **Maintainable**: Single source of truth in backend

---

## Architecture

### Data Flow

```
User Opens Signup Page
         ↓
Frontend calls POST /api/auth/location-data/
         ↓
Backend detects IP → Returns detected country + regional countries
         ↓
Frontend displays: 🇨🇦 Canada +1 (pre-selected)
         ↓
User searches or selects from list
         ↓
Frontend calls GET /api/auth/countries/phone-data/?search=france
         ↓
Backend returns: 🇫🇷 France +33
         ↓
User selects and enters phone number
         ↓
Form submits: +33612345678
```

### Database Schema

```sql
-- Country model with phone data
CREATE TABLE core_country (
    id UUID PRIMARY KEY,
    iso2 VARCHAR(2),
    iso3 VARCHAR(3) UNIQUE,
    name VARCHAR(100),
    code INTEGER,
    phone_code VARCHAR(10),      -- NEW: "+229", "+1", etc.
    flag_emoji VARCHAR(10),       -- NEW: "🇧🇯", "🇨🇦", etc.
    region VARCHAR(50) INDEXED,   -- NEW: "West Africa", etc.
    default_admin_level INTEGER
);
```

### Components

```
┌─────────────────────────────────────────────┐
│   core/country_data.py (242 countries)      │
│   Lookup table: ISO3 → phone data           │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│   Country Model (Database)                  │
│   Fields: phone_code, flag_emoji, region    │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│   Serializers (API)                         │
│   - CountrySerializer                       │
│   - CountryPhoneDataSerializer              │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│   API Endpoints                             │
│   - /api/auth/location-data/                │
│   - /api/auth/countries/phone-data/         │
│   - /api/auth/countries/regions/            │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│   Redis Cache (1-24 hours)                  │
└─────────────────────────────────────────────┘
```

---

## API Endpoints

### Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/location-data/` | POST | Detect user location + regional countries |
| `/api/auth/countries/phone-data/` | GET | Search/filter countries |
| `/api/auth/countries/phone-data/?search=X` | GET | Search by name/code |
| `/api/auth/countries/phone-data/?region=X` | GET | Filter by region |
| `/api/auth/countries/phone-data/?iso3=X` | GET | Get specific country |
| `/api/auth/countries/regions/` | GET | List all regions |

### Full Documentation
See [COUNTRY_API_QUICK_REFERENCE.md](./COUNTRY_API_QUICK_REFERENCE.md)

---

## Frontend Integration

### Step 1: Create API Service

```javascript
// services/countryService.js
import api from './api';

export const countryService = {
  async getUserLocationData() {
    const { data } = await api.post('/api/auth/location-data/');
    return data;
  },

  async searchCountries(query) {
    const { data } = await api.get('/api/auth/countries/phone-data/', {
      params: { search: query }
    });
    return data;
  },

  async getCountriesByRegion(region) {
    const { data } = await api.get('/api/auth/countries/phone-data/', {
      params: { region }
    });
    return data;
  }
};
```

### Step 2: Use in Signup Page

```javascript
// pages/signup.jsx
import { useState, useEffect } from 'react';
import { countryService } from '@/services/countryService';

export default function SignupPage() {
  const [detectedCountry, setDetectedCountry] = useState(null);
  const [countries, setCountries] = useState([]);

  useEffect(() => {
    loadLocationData();
  }, []);

  const loadLocationData = async () => {
    const data = await countryService.getUserLocationData();

    setDetectedCountry(data.country);
    setCountries([data.country, ...data.regional_countries]);
  };

  const handleSearch = async (query) => {
    if (query.length < 2) return;
    const data = await countryService.searchCountries(query);
    setCountries(data.countries);
  };

  return (
    <PhoneInput
      countries={countries}
      defaultCountry={detectedCountry}
      onSearch={handleSearch}
    />
  );
}
```

### Full Examples
See [SIGNUP_COUNTRY_API_INTEGRATION.md](./SIGNUP_COUNTRY_API_INTEGRATION.md)

---

## Testing

### Manual Testing

```bash
# Run the test suite
./test_country_endpoints.sh
```

### Unit Tests

```bash
# Test all endpoints
docker compose exec backend python manage.py test accounts.tests.test_country_endpoints

# Test specific endpoint
docker compose exec backend python manage.py shell -c "
from accounts.geolocation_views import get_countries_with_phone_data
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()
request = factory.get('/api/auth/countries/phone-data/?search=canada')
response = get_countries_with_phone_data(request)
print(response.data)
"
```

### Verify Database

```bash
# Check countries with phone data
docker compose exec backend python manage.py shell -c "
from core.models import Country
countries = Country.objects.exclude(phone_code__isnull=True)
for c in countries:
    print(f'{c.flag_emoji} {c.name}: {c.phone_code} - {c.region}')
"
```

---

## Documentation

### Complete Guides

1. **[COUNTRY_PHONE_DATA_INTEGRATION.md](./COUNTRY_PHONE_DATA_INTEGRATION.md)**
   - Complete system architecture
   - Database schema and migrations
   - Integration points
   - Maintenance guide

2. **[SIGNUP_COUNTRY_API_INTEGRATION.md](./SIGNUP_COUNTRY_API_INTEGRATION.md)**
   - Frontend integration guide
   - React/Next.js examples
   - PhoneInput component code
   - Styling with Tailwind CSS

3. **[SIGNUP_COUNTRY_IMPLEMENTATION_SUMMARY.md](./SIGNUP_COUNTRY_IMPLEMENTATION_SUMMARY.md)**
   - What we accomplished
   - Testing results
   - Performance metrics
   - Next steps

4. **[COUNTRY_API_QUICK_REFERENCE.md](./COUNTRY_API_QUICK_REFERENCE.md)**
   - Quick API reference
   - Common use cases
   - Response formats
   - Testing commands

5. **[COUNTRY_DATA_COVERAGE.md](./COUNTRY_DATA_COVERAGE.md)**
   - Coverage statistics
   - Regional distribution
   - Country list

---

## Quick Start

### For Backend Developers

```bash
# 1. Check current state
docker compose exec backend python manage.py shell -c "
from core.models import Country
print(f'Countries with phone data: {Country.objects.exclude(phone_code__isnull=True).count()}')
"

# 2. Populate phone data for existing countries
docker compose exec backend python populate_country_phone_data.py

# 3. Test endpoints
./test_country_endpoints.sh
```

### For Frontend Developers

```bash
# 1. Test location detection
curl -X POST http://localhost:8000/api/auth/location-data/

# 2. Test country search
curl "http://localhost:8000/api/auth/countries/phone-data/?search=canada"

# 3. Test region filter
curl "http://localhost:8000/api/auth/countries/phone-data/?region=West+Africa"

# 4. Integrate into signup page (see SIGNUP_COUNTRY_API_INTEGRATION.md)
```

---

## Performance

### Caching Strategy

| Data Type | Cache Duration | Strategy |
|-----------|----------------|----------|
| Location detection | No cache | User-specific |
| All countries | 1 hour | Global |
| Search results | 1 hour | Per query |
| Region filter | 1 hour | Per region |
| Regions list | 24 hours | Global |

### Response Times (Typical)

- First request: ~100-200ms (database query)
- Cached request: ~5-10ms (Redis)
- Search query: ~50-100ms (indexed)

### Optimization

- `region` field is indexed for fast filtering
- Queries exclude countries without phone codes
- Regional results limited to 10 countries
- Redis caching with smart key generation

---

## Maintenance

### Adding New Countries

When you import new shapefiles or create countries:

1. **Automatic**: Phone data populated from `country_data.py`
2. **Manual**: Run `populate_country_phone_data.py`
3. **Verify**: Check API endpoints return new countries

### Updating Country Data

1. Edit `core/country_data.py`
2. Run population script
3. Cache automatically expires after 1-24 hours

### Monitoring

```bash
# Check cache hit rates
docker compose exec redis redis-cli --scan --pattern "*countries*"

# Monitor API performance
docker compose logs backend | grep "country"

# Database query stats
docker compose exec backend python manage.py shell -c "
from django.db import connection
from django.db.models import Count
from core.models import Country

# Regions distribution
Country.objects.values('region').annotate(c=Count('id')).order_by('-c')
"
```

---

## Troubleshooting

### Issue: Location detection returns wrong country

**Cause**: IP geolocation database may be outdated or user behind VPN

**Solution**: User can manually search and select their country

### Issue: Search returns no results

**Cause**: Country not in database or missing phone data

**Solution**: Check if country exists in `country_data.py`, run population script

### Issue: Cache not working

**Cause**: Redis not running or connection issue

**Solution**:
```bash
docker compose restart redis
docker compose exec backend python manage.py shell -c "from django.core.cache import cache; print(cache.get('test'))"
```

### Issue: Regional countries not showing

**Cause**: Country missing `region` field

**Solution**: Update country in `country_data.py` and repopulate

---

## Files Reference

### Core Files
- `core/models.py` - Country model with phone fields
- `core/country_data.py` - Lookup table (242 countries)
- `core/serializers.py` - Country serializers
- `core/migrations/0004_add_phone_fields_to_country.py` - Migration

### API Files
- `accounts/geolocation_views.py` - API endpoints
- `accounts/urls.py` - URL routing

### Scripts
- `populate_country_phone_data.py` - Population script
- `test_country_endpoints.sh` - Test suite
- `setup.sh` - Setup integration

### Documentation
- `COUNTRY_PHONE_DATA_INTEGRATION.md` - System guide
- `SIGNUP_COUNTRY_API_INTEGRATION.md` - Frontend guide
- `SIGNUP_COUNTRY_IMPLEMENTATION_SUMMARY.md` - Summary
- `COUNTRY_API_QUICK_REFERENCE.md` - API reference
- `COUNTRY_DATA_COVERAGE.md` - Coverage stats
- `README_COUNTRY_SYSTEM.md` - This file

---

## Support

### Questions?

1. Check the documentation files listed above
2. Run the test suite: `./test_country_endpoints.sh`
3. Verify database state: See "Testing" section
4. Review logs: `docker compose logs backend | grep -i country`

### Contributing

When adding new features:
1. Update relevant documentation
2. Add tests for new endpoints
3. Update cache keys if data structure changes
4. Run full test suite before committing

---

## Summary

✅ **Backend**: Fully implemented and tested
⏳ **Frontend**: Ready for integration
📚 **Documentation**: Comprehensive and complete
🧪 **Testing**: Test suite available
⚡ **Performance**: Optimized with caching
🌍 **Coverage**: 242 countries worldwide

**The system is production-ready for signup page integration!**

---

*Last Updated: October 13, 2025*
