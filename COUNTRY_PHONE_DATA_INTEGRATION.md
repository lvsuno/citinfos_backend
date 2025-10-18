# Country Phone Data Integration Guide

## Overview

The Citinfos backend now includes comprehensive phone data (dial codes, flag emojis, and regions) for **242 countries and territories** worldwide. This data is automatically populated when countries are created.

## System Architecture

### 1. Country Data Lookup (`core/country_data.py`)

Central lookup table containing phone data for 242 countries:

```python
COUNTRY_DATA = {
    'BEN': {
        'iso2': 'BJ',
        'name': 'Benin',
        'phone_code': '+229',
        'flag_emoji': '🇧🇯',
        'region': 'West Africa'
    },
    # ... 241 more countries
}
```

**Helper Functions:**
- `get_country_info(iso3_code)` - Get full country info
- `get_phone_code(iso3_code)` - Get dial code only
- `get_flag_emoji(iso3_code)` - Get flag emoji only
- `get_region(iso3_code)` - Get region only
- `get_iso2(iso3_code)` - Get ISO2 code

### 2. Country Model (`core/models.py`)

Extended with phone-related fields:

```python
class Country(models.Model):
    # Existing fields
    id = UUIDField(primary_key=True)
    iso3 = CharField(max_length=3, unique=True)  # BEN, CAN, USA
    iso2 = CharField(max_length=2, unique=True)  # BJ, CA, US
    name = CharField(max_length=100)
    code = IntegerField(null=True)
    default_admin_level = IntegerField(null=True)

    # NEW: Phone-related fields
    phone_code = CharField(max_length=10, null=True, blank=True)
    flag_emoji = CharField(max_length=10, null=True, blank=True)
    region = CharField(max_length=50, null=True, blank=True, db_index=True)
```

**Migration Applied:** `0004_add_phone_fields_to_country`

### 3. Auto-Population System

Countries are automatically populated with phone data when created through:

#### A. Admin Data Import (`import_admin_data.py`)

When importing administrative divisions (shapefiles), the `get_or_create_country()` method automatically:

1. Looks up country info from `country_data.py`
2. Creates country with phone data if new
3. Updates existing country if phone data is missing

```python
def get_or_create_country(self, name, code):
    """Get or create a country with phone data from country_data.py"""
    country_info = get_country_info(code)

    defaults = {'name': name}
    if country_info:
        defaults.update({
            'iso2': country_info.get('iso2'),
            'iso3': code,
            'phone_code': country_info.get('phone_code'),
            'flag_emoji': country_info.get('flag_emoji'),
            'region': country_info.get('region')
        })

    country, created = Country.objects.get_or_create(
        code=code,
        defaults=defaults
    )

    # Update existing countries with missing phone data
    if not created and country_info:
        # ... update logic

    return country
```

#### B. Setup Country Command (`core/management/commands/setup_country.py`)

The `setup_country` management command also integrates phone data:

```bash
python manage.py setup_country --name "France" --iso3 "FRA" --iso2 "FR"
# Output: Created country: France (FRA) 🇫🇷 +33
```

### 4. Data Population Script (`populate_country_phone_data.py`)

Standalone script to populate phone data for existing countries:

```bash
docker compose exec backend python populate_country_phone_data.py
```

**Output:**
```
Starting country phone data population...
--------------------------------------------------------
Found 2 countries in database

✓ Updated Benin (BEN): 🇧🇯 +229 - West Africa
✓ Updated Canada (CAN): 🇨🇦 +1 - North America

--------------------------------------------------------
Population complete!
Updated: 2 countries
Missing: 0 countries
```

### 5. Setup Integration (`setup.sh`)

The main setup script automatically populates phone data:

```bash
./setup.sh
```

**Setup Flow:**
1. Build backend
2. Start services
3. Run migrations (including `0004_add_phone_fields_to_country`)
4. Create superuser
5. **Setup countries** → Auto-populates phone data via `setup_country` command
6. **Populate phone data** → Runs `populate_country_phone_data.py`
7. Load geo data

## Data Coverage

### Complete Coverage: 242 Countries/Territories

| Region | Count | Examples |
|--------|-------|----------|
| Caribbean | 28 | Jamaica 🇯🇲 +1876, Haiti 🇭🇹 +509 |
| Oceania | 23 | Fiji 🇫🇯 +679, Samoa 🇼🇸 +685 |
| East Africa | 19 | Kenya 🇰🇪 +254, Tanzania 🇹🇿 +255 |
| Western Europe | 18 | France 🇫🇷 +33, Germany 🇩🇪 +49 |
| West Africa | 17 | Benin 🇧🇯 +229, Nigeria 🇳🇬 +234 |
| Middle East | 16 | UAE 🇦🇪 +971, Saudi Arabia 🇸🇦 +966 |
| Southern Europe | 15 | Italy 🇮🇹 +39, Spain 🇪🇸 +34 |
| South America | 15 | Brazil 🇧🇷 +55, Argentina 🇦🇷 +54 |
| Asia Pacific | 14 | China 🇨🇳 +86, Japan 🇯🇵 +81 |
| Eastern Europe | 13 | Poland 🇵🇱 +48, Ukraine 🇺🇦 +380 |
| Northern Europe | 10 | Sweden 🇸🇪 +46, Norway 🇳🇴 +47 |
| Central Africa | 9 | Cameroon 🇨🇲 +237, Gabon 🇬🇦 +241 |
| Central America | 7 | Guatemala 🇬🇹 +502, Panama 🇵🇦 +507 |
| Southern Africa | 6 | South Africa 🇿🇦 +27, Botswana 🇧🇼 +267 |
| North America | 6 | USA 🇺🇸 +1, Canada 🇨🇦 +1 |
| North Africa | 6 | Egypt 🇪🇬 +20, Morocco 🇲🇦 +212 |
| Central Asia | 6 | Kazakhstan 🇰🇿 +7, Uzbekistan 🇺🇿 +998 |
| Southeast Asia | 5 | Thailand 🇹🇭 +66, Vietnam 🇻🇳 +84 |
| East Asia | 5 | South Korea 🇰🇷 +82, Taiwan 🇹🇼 +886 |
| South Asia | 4 | India 🇮🇳 +91, Pakistan 🇵🇰 +92 |

**Total: 242 countries and territories** ✅

## Usage Examples

### 1. Check Phone Data for a Country

```python
from core.models import Country

# Get country
benin = Country.objects.get(iso3='BEN')

print(f"Country: {benin.name}")
print(f"Dial Code: {benin.phone_code}")
print(f"Flag: {benin.flag_emoji}")
print(f"Region: {benin.region}")

# Output:
# Country: Benin
# Dial Code: +229
# Flag: 🇧🇯
# Region: West Africa
```

### 2. Get Countries by Region

```python
from core.models import Country

# Get all West African countries
west_africa = Country.objects.filter(region='West Africa')

for country in west_africa:
    print(f"{country.flag_emoji} {country.name}: {country.phone_code}")

# Output:
# 🇧🇯 Benin: +229
# 🇧🇫 Burkina Faso: +226
# 🇨🇮 Côte d'Ivoire: +225
# ... etc
```

### 3. Add New Country with Auto Phone Data

```bash
# Via management command
docker compose exec backend python manage.py setup_country \
    --name "France" \
    --iso3 "FRA" \
    --iso2 "FR"

# Output: Created country: France (FRA) 🇫🇷 +33 - Western Europe
```

```python
# Via import script (when loading shapefiles)
from import_admin_data import AdminDataImporter

importer = AdminDataImporter()
france = importer.get_or_create_country("France", "FRA")
# Automatically gets phone_code='+33', flag_emoji='🇫🇷', region='Western Europe'
```

### 4. API Response (Future)

When API endpoints are created, they will return:

```json
{
  "id": "uuid-here",
  "iso3": "BEN",
  "iso2": "BJ",
  "name": "Benin",
  "phone_code": "+229",
  "flag_emoji": "🇧🇯",
  "region": "West Africa",
  "default_admin_level": 3
}
```

## Maintenance

### Adding New Countries

1. **Add to `core/country_data.py`:**

```python
'FRA': {
    'iso2': 'FR',
    'name': 'France',
    'phone_code': '+33',
    'flag_emoji': '🇫🇷',
    'region': 'Western Europe'
}
```

2. **Countries are auto-created when:**
   - Importing shapefiles with `import_admin_data.py`
   - Using `setup_country` management command
   - Both automatically populate phone data from lookup table

### Updating Existing Countries

Run the population script:

```bash
docker compose exec backend python populate_country_phone_data.py
```

This will:
- Find all countries in the database
- Update missing phone data from `country_data.py`
- Skip countries already with complete data

### Verifying Data

```bash
# Check all countries
docker compose exec backend python manage.py shell -c "
from core.models import Country
for c in Country.objects.all():
    print(f'{c.name} ({c.iso3}): {c.flag_emoji} {c.phone_code} - {c.region}')
"

# Count by region
docker compose exec backend python manage.py shell -c "
from core.models import Country
from django.db.models import Count
result = Country.objects.values('region').annotate(count=Count('id')).order_by('-count')
for r in result:
    print(f\"{r['region']}: {r['count']} countries\")
"
```

## Files Modified/Created

### Core Files
- ✅ `core/models.py` - Added phone fields to Country model
- ✅ `core/migrations/0004_add_phone_fields_to_country.py` - Migration
- ✅ `core/country_data.py` - Lookup table (242 countries)
- ✅ `core/management/commands/setup_country.py` - Auto phone data

### Import Scripts
- ✅ `import_admin_data.py` - Auto-populate phone data on country creation
- ✅ `populate_country_phone_data.py` - Standalone population script

### Setup & Documentation
- ✅ `setup.sh` - Integrated phone data population
- ✅ `COUNTRY_DATA_COVERAGE.md` - Coverage statistics
- ✅ `COUNTRY_DATA_UPDATE_SUMMARY.md` - Update history
- ✅ `COUNTRY_PHONE_DATA_INTEGRATION.md` - This guide

## Next Steps

### 1. Create API Endpoints

```python
# accounts/views.py
from rest_framework import viewsets
from core.models import Country

class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    @action(detail=False, methods=['get'])
    def by_region(self, request):
        region = request.query_params.get('region')
        countries = Country.objects.filter(region=region)
        return Response(serializer.data)
```

### 2. Update Frontend

Remove hardcoded country lists and fetch from API:

```javascript
// services/countryService.js
export const getCountriesByRegion = async (region) => {
  const response = await api.get(`/api/countries/?region=${region}`);
  return response.data;
};

// Use in phone validation
const userCountry = await getUserCountry(); // from IP geolocation
const regionalCountries = await getCountriesByRegion(userCountry.region);
```

### 3. Search & Filter

Add search capabilities:

```python
# Add to CountryViewSet
@action(detail=False, methods=['get'])
def search(self, request):
    q = request.query_params.get('q', '')
    countries = Country.objects.filter(
        Q(name__icontains=q) |
        Q(iso3__icontains=q) |
        Q(iso2__icontains=q)
    )
    return Response(serializer.data)
```

## Benefits

✅ **Centralized Data** - Single source of truth for country phone data
✅ **Auto-Population** - Phone data added automatically when countries created
✅ **Complete Coverage** - 242 countries/territories included
✅ **Easy Maintenance** - Update `country_data.py` and run population script
✅ **Integration Ready** - Works with existing import scripts and setup
✅ **API Ready** - Database fields ready for API serialization
✅ **Frontend Ready** - Can replace hardcoded country lists

## Troubleshooting

### Countries Missing Phone Data

Run the population script:
```bash
docker compose exec backend python populate_country_phone_data.py
```

### New Country Not in Lookup Table

Add to `core/country_data.py`:
```python
'XXX': {
    'iso2': 'XX',
    'name': 'Country Name',
    'phone_code': '+XXX',
    'flag_emoji': '🇽🇽',
    'region': 'Region Name'
}
```

### Check Coverage

```bash
# Count countries in database
docker compose exec backend python manage.py shell -c "
from core.models import Country
print(f'Database: {Country.objects.count()} countries')
print(f'With phone data: {Country.objects.exclude(phone_code__isnull=True).count()} countries')
"
```

## Summary

The country phone data integration is now **fully automated** and integrated into the setup process:

1. ✅ 242 countries in lookup table
2. ✅ Database fields added and migrated
3. ✅ Auto-population on country creation
4. ✅ Standalone population script
5. ✅ Integrated into setup.sh
6. ✅ Works with import scripts
7. ✅ Ready for API endpoints
8. ✅ Documentation complete

**All countries created in the system will automatically have phone data populated!** 🎉
