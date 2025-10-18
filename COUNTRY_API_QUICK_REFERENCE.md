# Country API Quick Reference

## 🚀 Endpoints Overview

All endpoints are under `/api/auth/` and allow anonymous access for signup flow.

---

## 1️⃣ Detect User Location + Regional Countries

**POST** `/api/auth/location-data/`

Returns user's detected country with phone data + up to 10 countries from the same region.

```bash
curl -X POST http://localhost:8000/api/auth/location-data/ \
  -H "Content-Type: application/json"
```

**Response**:
```json
{
  "country": {
    "iso3": "CAN",
    "phone_code": "+1",
    "flag_emoji": "🇨🇦",
    "region": "North America"
  },
  "regional_countries": [
    {"iso3": "USA", "phone_code": "+1", "flag_emoji": "🇺🇸"},
    {"iso3": "MEX", "phone_code": "+52", "flag_emoji": "🇲🇽"}
  ],
  "country_search_info": {
    "search_endpoint": "/api/auth/countries/phone-data/",
    "region_filter": "North America"
  }
}
```

**Use for**: Initial page load, pre-selecting user's country

---

## 2️⃣ Search Countries

**GET** `/api/auth/countries/phone-data/?search={query}`

Search countries by name, ISO2, or ISO3 code.

```bash
# Search by name
curl "http://localhost:8000/api/auth/countries/phone-data/?search=canada"

# Search by ISO code
curl "http://localhost:8000/api/auth/countries/phone-data/?search=can"
```

**Response**:
```json
{
  "success": true,
  "countries": [
    {
      "iso2": "CA",
      "iso3": "CAN",
      "name": "Canada",
      "phone_code": "+1",
      "flag_emoji": "🇨🇦",
      "region": "North America"
    }
  ],
  "count": 1,
  "search": "canada"
}
```

**Use for**: Live search as user types

---

## 3️⃣ Filter by Region

**GET** `/api/auth/countries/phone-data/?region={region_name}`

Get all countries in a specific region.

```bash
curl "http://localhost:8000/api/auth/countries/phone-data/?region=West+Africa"
```

**Response**:
```json
{
  "success": true,
  "countries": [
    {"iso3": "BEN", "name": "Benin", "phone_code": "+229", "flag_emoji": "🇧🇯"},
    {"iso3": "BFA", "name": "Burkina Faso", "phone_code": "+226", "flag_emoji": "🇧🇫"}
  ],
  "count": 17,
  "region": "West Africa"
}
```

**Use for**: Regional dropdown filter

---

## 4️⃣ Get Specific Country

**GET** `/api/auth/countries/phone-data/?iso3={code}`

Get details for one country.

```bash
curl "http://localhost:8000/api/auth/countries/phone-data/?iso3=BEN"
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
    }
  ],
  "count": 1
}
```

**Use for**: Getting country by saved ISO3 code

---

## 5️⃣ Get All Regions

**GET** `/api/auth/countries/regions/`

Get list of all regions with country counts.

```bash
curl "http://localhost:8000/api/auth/countries/regions/"
```

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
  ],
  "count": 20
}
```

**Use for**: Building region filter dropdown

---

## 6️⃣ Get All Countries

**GET** `/api/auth/countries/phone-data/`

Get all countries with phone data.

```bash
curl "http://localhost:8000/api/auth/countries/phone-data/"
```

**Response**:
```json
{
  "success": true,
  "countries": [
    {"iso3": "BEN", "name": "Benin", "phone_code": "+229"},
    {"iso3": "CAN", "name": "Canada", "phone_code": "+1"}
  ],
  "count": 242
}
```

**Use for**: Loading all countries (fallback)

---

## 📊 Response Fields

All country objects include:

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `iso2` | string | "CA" | ISO 3166-1 alpha-2 code |
| `iso3` | string | "CAN" | ISO 3166-1 alpha-3 code |
| `name` | string | "Canada" | Country name |
| `phone_code` | string | "+1" | International dial code |
| `flag_emoji` | string | "🇨🇦" | Unicode flag emoji |
| `region` | string | "North America" | Geographic region |

---

## ⚡ Performance

| Feature | Status |
|---------|--------|
| Caching | ✅ Redis, 1-24 hours |
| Response time | < 100ms (first) / < 10ms (cached) |
| Search | Indexed, sub-50ms |
| Database queries | Optimized with excludes/filters |

---

## 🔒 Permissions

All endpoints: `AllowAny` - No authentication required for signup flow.

---

## 🎯 Common Use Cases

### Signup Page Flow
```javascript
// 1. Page loads
const data = await post('/api/auth/location-data/');
// User sees: Canada 🇨🇦 +1 (detected) + USA, Mexico (regional)

// 2. User searches "france"
const results = await get('/api/auth/countries/phone-data/?search=france');
// User sees: France 🇫🇷 +33

// 3. User selects France
setCountry(france);
// Phone input shows: 🇫🇷 +33 | [____]
```

### Building Region Filter
```javascript
// Load regions
const { regions } = await get('/api/auth/countries/regions/');
// Display: West Africa (17), North America (6), etc.

// User selects "West Africa"
const { countries } = await get('/api/auth/countries/phone-data/?region=West+Africa');
// Display: Benin, Burkina Faso, etc.
```

---

## 🧪 Testing

```bash
# Test all endpoints
./test_country_endpoints.sh

# Or manually:
curl -X POST http://localhost:8000/api/auth/location-data/
curl "http://localhost:8000/api/auth/countries/phone-data/"
curl "http://localhost:8000/api/auth/countries/phone-data/?search=ben"
curl "http://localhost:8000/api/auth/countries/phone-data/?region=West+Africa"
curl "http://localhost:8000/api/auth/countries/regions/"
```

---

## 📝 Notes

- **242 countries** available (100% worldcities.csv coverage)
- **Cache** automatically invalidates after 1-24 hours
- **Regional loading** limited to 10 countries for performance
- **Search** works on name, ISO2, and ISO3 (case-insensitive)
- **Fallback**: If location detection fails, load all countries
