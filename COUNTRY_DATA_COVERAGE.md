# Country Data Coverage

## Overview

The `core/country_data.py` file now contains comprehensive phone data for **242 countries and territories** worldwide - covering **100% of the worldcities.csv dataset**.

## Coverage by Region

| Region | Count | Coverage |
|--------|-------|----------|
| Caribbean | 28 | Complete ✅ |
| Oceania | 23 | Complete ✅ |
| East Africa | 19 | Complete ✅ |
| Western Europe | 18 | Complete ✅ |
| West Africa | 17 | Complete ✅ |
| Middle East | 16 | Complete ✅ |
| Southern Europe | 15 | Complete ✅ |
| South America | 15 | Complete ✅ |
| Asia Pacific | 14 | Complete ✅ |
| Eastern Europe | 13 | Complete ✅ |
| Northern Europe | 10 | Complete ✅ |
| Central Africa | 9 | Complete ✅ |
| Central America | 7 | Complete ✅ |
| Southern Africa | 6 | Complete ✅ |
| North America | 6 | Complete ✅ |
| North Africa | 6 | Complete ✅ |
| Central Asia | 6 | Complete ✅ |
| Southeast Asia | 5 | Complete ✅ |
| East Asia | 5 | Complete ✅ |
| South Asia | 4 | Complete ✅ |

## Total: 242 Countries & Territories

This includes:
- All UN member states (193)
- Observer states (2: Vatican City, Palestine)
- Dependent territories (47+)
- Special administrative regions (Hong Kong, Macau, etc.)
- Disputed territories (Kosovo, Gaza Strip, West Bank)

## Recently Added (19 territories)

- **Caribbean**: Bonaire/Sint Eustatius/Saba, Saint Barthélemy, Saint Martin
- **Oceania**: Cook Islands, Christmas Island, Norfolk Island, Niue, Pitcairn Islands, Wallis and Futuna
- **Europe**: Guernsey, Isle of Man, Jersey, Kosovo, Svalbard
- **Americas**: Saint Pierre and Miquelon, South Georgia
- **Africa**: Saint Helena
- **Middle East**: Gaza Strip, West Bank

## Data Structure

Each country entry contains:
```python
'ISO3': {
    'iso2': 'XX',
    'name': 'Country Name',
    'phone_code': '+XXX',
    'flag_emoji': '🏳️',
    'region': 'Region Name'
}
```

## Usage in Country Model

When a new Country is created (typically when importing administrative divisions):

1. The Country model checks `core/country_data.py` using the ISO3 code
2. If found, automatically populates:
   - `phone_code` field
   - `flag_emoji` field
   - `region` field
3. If not found, fields remain `null` and can be manually populated

## API Integration

The country data will be exposed via REST API endpoints:

- `GET /api/auth/countries/` - All countries with phone data
- `GET /api/auth/countries/?region=West+Africa` - Filter by region
- `GET /api/auth/countries/search/?q=benin` - Search countries
- Included in `get_user_location_data` for regional auto-detection

## Frontend Usage

The frontend signup page will:
1. Detect user's location (IP-based geolocation)
2. Load countries from the same region
3. Provide search functionality to find other countries
4. Display flag emoji + dial code for each country

## Maintenance

To add a new country:
1. Add entry to `COUNTRY_DATA` dictionary in `core/country_data.py`
2. Follow ISO 3166 standards for ISO2/ISO3 codes
3. Use proper Unicode flag emoji
4. Assign to appropriate region

## Regions Defined

- **Africa**: North, West, Central, East, Southern
- **Americas**: North, Central, South, Caribbean
- **Asia**: East, Southeast, South, Central, Western (Middle East)
- **Europe**: Northern, Western, Eastern, Southern
- **Oceania**: Pacific Islands and territories
