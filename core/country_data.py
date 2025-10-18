"""
Country data lookup table.
Contains comprehensive information about all countries for reference
when creating new Country records.

This data is used to automatically populate phone_code, flag_emoji,
and region when countries are added to the database.
"""

# Comprehensive country data: ISO3 -> country info
COUNTRY_DATA = {
    # North America
    'CAN': {
        'iso2': 'CA',
        'name': 'Canada',
        'phone_code': '+1',
        'flag_emoji': '🇨🇦',
        'region': 'North America'
    },
    'USA': {
        'iso2': 'US',
        'name': 'United States',
        'phone_code': '+1',
        'flag_emoji': '🇺🇸',
        'region': 'North America'
    },
    'MEX': {
        'iso2': 'MX',
        'name': 'Mexico',
        'phone_code': '+52',
        'flag_emoji': '🇲🇽',
        'region': 'North America'
    },

    # West Africa (Francophone)
    'BEN': {
        'iso2': 'BJ',
        'name': 'Benin',
        'phone_code': '+229',
        'flag_emoji': '🇧🇯',
        'region': 'West Africa'
    },
    'BFA': {
        'iso2': 'BF',
        'name': 'Burkina Faso',
        'phone_code': '+226',
        'flag_emoji': '🇧🇫',
        'region': 'West Africa'
    },
    'CIV': {
        'iso2': 'CI',
        'name': "Côte d'Ivoire",
        'phone_code': '+225',
        'flag_emoji': '🇨🇮',
        'region': 'West Africa'
    },
    'GIN': {
        'iso2': 'GN',
        'name': 'Guinea',
        'phone_code': '+224',
        'flag_emoji': '🇬🇳',
        'region': 'West Africa'
    },
    'MLI': {
        'iso2': 'ML',
        'name': 'Mali',
        'phone_code': '+223',
        'flag_emoji': '🇲🇱',
        'region': 'West Africa'
    },
    'NER': {
        'iso2': 'NE',
        'name': 'Niger',
        'phone_code': '+227',
        'flag_emoji': '🇳🇪',
        'region': 'West Africa'
    },
    'SEN': {
        'iso2': 'SN',
        'name': 'Senegal',
        'phone_code': '+221',
        'flag_emoji': '🇸🇳',
        'region': 'West Africa'
    },
    'TGO': {
        'iso2': 'TG',
        'name': 'Togo',
        'phone_code': '+228',
        'flag_emoji': '🇹🇬',
        'region': 'West Africa'
    },

    # West Africa (Anglophone)
    'GHA': {
        'iso2': 'GH',
        'name': 'Ghana',
        'phone_code': '+233',
        'flag_emoji': '🇬🇭',
        'region': 'West Africa'
    },
    'NGA': {
        'iso2': 'NG',
        'name': 'Nigeria',
        'phone_code': '+234',
        'flag_emoji': '🇳🇬',
        'region': 'West Africa'
    },
    'SLE': {
        'iso2': 'SL',
        'name': 'Sierra Leone',
        'phone_code': '+232',
        'flag_emoji': '🇸🇱',
        'region': 'West Africa'
    },
    'LBR': {
        'iso2': 'LR',
        'name': 'Liberia',
        'phone_code': '+231',
        'flag_emoji': '🇱🇷',
        'region': 'West Africa'
    },
    'GMB': {
        'iso2': 'GM',
        'name': 'Gambia',
        'phone_code': '+220',
        'flag_emoji': '🇬🇲',
        'region': 'West Africa'
    },

    # Central Africa
    'CMR': {
        'iso2': 'CM',
        'name': 'Cameroon',
        'phone_code': '+237',
        'flag_emoji': '🇨🇲',
        'region': 'Central Africa'
    },
    'COD': {
        'iso2': 'CD',
        'name': 'DR Congo',
        'phone_code': '+243',
        'flag_emoji': '🇨🇩',
        'region': 'Central Africa'
    },
    'COG': {
        'iso2': 'CG',
        'name': 'Congo',
        'phone_code': '+242',
        'flag_emoji': '🇨🇬',
        'region': 'Central Africa'
    },
    'GAB': {
        'iso2': 'GA',
        'name': 'Gabon',
        'phone_code': '+241',
        'flag_emoji': '🇬🇦',
        'region': 'Central Africa'
    },
    'CAF': {
        'iso2': 'CF',
        'name': 'Central African Republic',
        'phone_code': '+236',
        'flag_emoji': '🇨🇫',
        'region': 'Central Africa'
    },
    'TCD': {
        'iso2': 'TD',
        'name': 'Chad',
        'phone_code': '+235',
        'flag_emoji': '🇹🇩',
        'region': 'Central Africa'
    },

    # East Africa
    'KEN': {
        'iso2': 'KE',
        'name': 'Kenya',
        'phone_code': '+254',
        'flag_emoji': '🇰🇪',
        'region': 'East Africa'
    },
    'TZA': {
        'iso2': 'TZ',
        'name': 'Tanzania',
        'phone_code': '+255',
        'flag_emoji': '🇹🇿',
        'region': 'East Africa'
    },
    'UGA': {
        'iso2': 'UG',
        'name': 'Uganda',
        'phone_code': '+256',
        'flag_emoji': '🇺🇬',
        'region': 'East Africa'
    },
    'RWA': {
        'iso2': 'RW',
        'name': 'Rwanda',
        'phone_code': '+250',
        'flag_emoji': '🇷🇼',
        'region': 'East Africa'
    },
    'BDI': {
        'iso2': 'BI',
        'name': 'Burundi',
        'phone_code': '+257',
        'flag_emoji': '🇧🇮',
        'region': 'East Africa'
    },
    'ETH': {
        'iso2': 'ET',
        'name': 'Ethiopia',
        'phone_code': '+251',
        'flag_emoji': '🇪🇹',
        'region': 'East Africa'
    },

    # Southern Africa
    'ZAF': {
        'iso2': 'ZA',
        'name': 'South Africa',
        'phone_code': '+27',
        'flag_emoji': '🇿🇦',
        'region': 'Southern Africa'
    },
    'ZWE': {
        'iso2': 'ZW',
        'name': 'Zimbabwe',
        'phone_code': '+263',
        'flag_emoji': '🇿🇼',
        'region': 'Southern Africa'
    },
    'BWA': {
        'iso2': 'BW',
        'name': 'Botswana',
        'phone_code': '+267',
        'flag_emoji': '🇧🇼',
        'region': 'Southern Africa'
    },
    'NAM': {
        'iso2': 'NA',
        'name': 'Namibia',
        'phone_code': '+264',
        'flag_emoji': '🇳🇦',
        'region': 'Southern Africa'
    },

    # North Africa
    'DZA': {
        'iso2': 'DZ',
        'name': 'Algeria',
        'phone_code': '+213',
        'flag_emoji': '🇩🇿',
        'region': 'North Africa'
    },
    'MAR': {
        'iso2': 'MA',
        'name': 'Morocco',
        'phone_code': '+212',
        'flag_emoji': '🇲🇦',
        'region': 'North Africa'
    },
    'TUN': {
        'iso2': 'TN',
        'name': 'Tunisia',
        'phone_code': '+216',
        'flag_emoji': '🇹🇳',
        'region': 'North Africa'
    },
    'EGY': {
        'iso2': 'EG',
        'name': 'Egypt',
        'phone_code': '+20',
        'flag_emoji': '🇪🇬',
        'region': 'North Africa'
    },
    'LBY': {
        'iso2': 'LY',
        'name': 'Libya',
        'phone_code': '+218',
        'flag_emoji': '🇱🇾',
        'region': 'North Africa'
    },

    # Western Europe
    'FRA': {
        'iso2': 'FR',
        'name': 'France',
        'phone_code': '+33',
        'flag_emoji': '🇫🇷',
        'region': 'Western Europe'
    },
    'DEU': {
        'iso2': 'DE',
        'name': 'Germany',
        'phone_code': '+49',
        'flag_emoji': '🇩🇪',
        'region': 'Western Europe'
    },
    'GBR': {
        'iso2': 'GB',
        'name': 'United Kingdom',
        'phone_code': '+44',
        'flag_emoji': '🇬🇧',
        'region': 'Western Europe'
    },
    'ESP': {
        'iso2': 'ES',
        'name': 'Spain',
        'phone_code': '+34',
        'flag_emoji': '🇪🇸',
        'region': 'Western Europe'
    },
    'ITA': {
        'iso2': 'IT',
        'name': 'Italy',
        'phone_code': '+39',
        'flag_emoji': '🇮🇹',
        'region': 'Western Europe'
    },
    'PRT': {
        'iso2': 'PT',
        'name': 'Portugal',
        'phone_code': '+351',
        'flag_emoji': '🇵🇹',
        'region': 'Western Europe'
    },
    'BEL': {
        'iso2': 'BE',
        'name': 'Belgium',
        'phone_code': '+32',
        'flag_emoji': '🇧🇪',
        'region': 'Western Europe'
    },
    'NLD': {
        'iso2': 'NL',
        'name': 'Netherlands',
        'phone_code': '+31',
        'flag_emoji': '🇳🇱',
        'region': 'Western Europe'
    },
    'CHE': {
        'iso2': 'CH',
        'name': 'Switzerland',
        'phone_code': '+41',
        'flag_emoji': '🇨🇭',
        'region': 'Western Europe'
    },
    'AUT': {
        'iso2': 'AT',
        'name': 'Austria',
        'phone_code': '+43',
        'flag_emoji': '🇦🇹',
        'region': 'Western Europe'
    },
    'LUX': {
        'iso2': 'LU',
        'name': 'Luxembourg',
        'phone_code': '+352',
        'flag_emoji': '🇱🇺',
        'region': 'Western Europe'
    },
    'IRL': {
        'iso2': 'IE',
        'name': 'Ireland',
        'phone_code': '+353',
        'flag_emoji': '🇮🇪',
        'region': 'Western Europe'
    },

    # Northern Europe
    'SWE': {
        'iso2': 'SE',
        'name': 'Sweden',
        'phone_code': '+46',
        'flag_emoji': '🇸🇪',
        'region': 'Northern Europe'
    },
    'NOR': {
        'iso2': 'NO',
        'name': 'Norway',
        'phone_code': '+47',
        'flag_emoji': '🇳🇴',
        'region': 'Northern Europe'
    },
    'DNK': {
        'iso2': 'DK',
        'name': 'Denmark',
        'phone_code': '+45',
        'flag_emoji': '🇩🇰',
        'region': 'Northern Europe'
    },
    'FIN': {
        'iso2': 'FI',
        'name': 'Finland',
        'phone_code': '+358',
        'flag_emoji': '🇫🇮',
        'region': 'Northern Europe'
    },
    'ISL': {
        'iso2': 'IS',
        'name': 'Iceland',
        'phone_code': '+354',
        'flag_emoji': '🇮🇸',
        'region': 'Northern Europe'
    },

    # Eastern Europe
    'POL': {
        'iso2': 'PL',
        'name': 'Poland',
        'phone_code': '+48',
        'flag_emoji': '🇵🇱',
        'region': 'Eastern Europe'
    },
    'CZE': {
        'iso2': 'CZ',
        'name': 'Czech Republic',
        'phone_code': '+420',
        'flag_emoji': '🇨🇿',
        'region': 'Eastern Europe'
    },
    'HUN': {
        'iso2': 'HU',
        'name': 'Hungary',
        'phone_code': '+36',
        'flag_emoji': '🇭🇺',
        'region': 'Eastern Europe'
    },
    'ROU': {
        'iso2': 'RO',
        'name': 'Romania',
        'phone_code': '+40',
        'flag_emoji': '🇷🇴',
        'region': 'Eastern Europe'
    },
    'BGR': {
        'iso2': 'BG',
        'name': 'Bulgaria',
        'phone_code': '+359',
        'flag_emoji': '🇧🇬',
        'region': 'Eastern Europe'
    },
    'UKR': {
        'iso2': 'UA',
        'name': 'Ukraine',
        'phone_code': '+380',
        'flag_emoji': '🇺🇦',
        'region': 'Eastern Europe'
    },
    'RUS': {
        'iso2': 'RU',
        'name': 'Russia',
        'phone_code': '+7',
        'flag_emoji': '🇷🇺',
        'region': 'Eastern Europe'
    },

    # Southern Europe
    'GRC': {
        'iso2': 'GR',
        'name': 'Greece',
        'phone_code': '+30',
        'flag_emoji': '🇬🇷',
        'region': 'Southern Europe'
    },
    'TUR': {
        'iso2': 'TR',
        'name': 'Turkey',
        'phone_code': '+90',
        'flag_emoji': '🇹🇷',
        'region': 'Southern Europe'
    },
    'HRV': {
        'iso2': 'HR',
        'name': 'Croatia',
        'phone_code': '+385',
        'flag_emoji': '🇭🇷',
        'region': 'Southern Europe'
    },
    'SRB': {
        'iso2': 'RS',
        'name': 'Serbia',
        'phone_code': '+381',
        'flag_emoji': '🇷🇸',
        'region': 'Southern Europe'
    },

    # Middle East
    'SAU': {
        'iso2': 'SA',
        'name': 'Saudi Arabia',
        'phone_code': '+966',
        'flag_emoji': '🇸🇦',
        'region': 'Middle East'
    },
    'ARE': {
        'iso2': 'AE',
        'name': 'UAE',
        'phone_code': '+971',
        'flag_emoji': '🇦🇪',
        'region': 'Middle East'
    },
    'ISR': {
        'iso2': 'IL',
        'name': 'Israel',
        'phone_code': '+972',
        'flag_emoji': '🇮🇱',
        'region': 'Middle East'
    },
    'JOR': {
        'iso2': 'JO',
        'name': 'Jordan',
        'phone_code': '+962',
        'flag_emoji': '🇯🇴',
        'region': 'Middle East'
    },
    'LBN': {
        'iso2': 'LB',
        'name': 'Lebanon',
        'phone_code': '+961',
        'flag_emoji': '🇱🇧',
        'region': 'Middle East'
    },
    'QAT': {
        'iso2': 'QA',
        'name': 'Qatar',
        'phone_code': '+974',
        'flag_emoji': '🇶🇦',
        'region': 'Middle East'
    },
    'KWT': {
        'iso2': 'KW',
        'name': 'Kuwait',
        'phone_code': '+965',
        'flag_emoji': '🇰🇼',
        'region': 'Middle East'
    },

    # Asia Pacific
    'CHN': {
        'iso2': 'CN',
        'name': 'China',
        'phone_code': '+86',
        'flag_emoji': '🇨🇳',
        'region': 'Asia Pacific'
    },
    'JPN': {
        'iso2': 'JP',
        'name': 'Japan',
        'phone_code': '+81',
        'flag_emoji': '🇯🇵',
        'region': 'Asia Pacific'
    },
    'KOR': {
        'iso2': 'KR',
        'name': 'South Korea',
        'phone_code': '+82',
        'flag_emoji': '🇰🇷',
        'region': 'Asia Pacific'
    },
    'IND': {
        'iso2': 'IN',
        'name': 'India',
        'phone_code': '+91',
        'flag_emoji': '🇮🇳',
        'region': 'Asia Pacific'
    },
    'PAK': {
        'iso2': 'PK',
        'name': 'Pakistan',
        'phone_code': '+92',
        'flag_emoji': '🇵🇰',
        'region': 'Asia Pacific'
    },
    'BGD': {
        'iso2': 'BD',
        'name': 'Bangladesh',
        'phone_code': '+880',
        'flag_emoji': '🇧🇩',
        'region': 'Asia Pacific'
    },
    'THA': {
        'iso2': 'TH',
        'name': 'Thailand',
        'phone_code': '+66',
        'flag_emoji': '🇹🇭',
        'region': 'Asia Pacific'
    },
    'VNM': {
        'iso2': 'VN',
        'name': 'Vietnam',
        'phone_code': '+84',
        'flag_emoji': '🇻🇳',
        'region': 'Asia Pacific'
    },
    'PHL': {
        'iso2': 'PH',
        'name': 'Philippines',
        'phone_code': '+63',
        'flag_emoji': '🇵🇭',
        'region': 'Asia Pacific'
    },
    'MYS': {
        'iso2': 'MY',
        'name': 'Malaysia',
        'phone_code': '+60',
        'flag_emoji': '🇲🇾',
        'region': 'Asia Pacific'
    },
    'SGP': {
        'iso2': 'SG',
        'name': 'Singapore',
        'phone_code': '+65',
        'flag_emoji': '🇸🇬',
        'region': 'Asia Pacific'
    },
    'IDN': {
        'iso2': 'ID',
        'name': 'Indonesia',
        'phone_code': '+62',
        'flag_emoji': '🇮🇩',
        'region': 'Asia Pacific'
    },
    'AUS': {
        'iso2': 'AU',
        'name': 'Australia',
        'phone_code': '+61',
        'flag_emoji': '🇦🇺',
        'region': 'Asia Pacific'
    },
    'NZL': {
        'iso2': 'NZ',
        'name': 'New Zealand',
        'phone_code': '+64',
        'flag_emoji': '🇳🇿',
        'region': 'Asia Pacific'
    },

    # South America
    'BRA': {
        'iso2': 'BR',
        'name': 'Brazil',
        'phone_code': '+55',
        'flag_emoji': '🇧🇷',
        'region': 'South America'
    },
    'ARG': {
        'iso2': 'AR',
        'name': 'Argentina',
        'phone_code': '+54',
        'flag_emoji': '🇦🇷',
        'region': 'South America'
    },
    'CHL': {
        'iso2': 'CL',
        'name': 'Chile',
        'phone_code': '+56',
        'flag_emoji': '🇨🇱',
        'region': 'South America'
    },
    'COL': {
        'iso2': 'CO',
        'name': 'Colombia',
        'phone_code': '+57',
        'flag_emoji': '🇨🇴',
        'region': 'South America'
    },
    'PER': {
        'iso2': 'PE',
        'name': 'Peru',
        'phone_code': '+51',
        'flag_emoji': '🇵🇪',
        'region': 'South America'
    },
    'VEN': {
        'iso2': 'VE',
        'name': 'Venezuela',
        'phone_code': '+58',
        'flag_emoji': '🇻🇪',
        'region': 'South America'
    },
    'ECU': {
        'iso2': 'EC',
        'name': 'Ecuador',
        'phone_code': '+593',
        'flag_emoji': '🇪🇨',
        'region': 'South America'
    },
    'URY': {
        'iso2': 'UY',
        'name': 'Uruguay',
        'phone_code': '+598',
        'flag_emoji': '🇺🇾',
        'region': 'South America'
    },

    # Caribbean
    'HTI': {
        'iso2': 'HT',
        'name': 'Haiti',
        'phone_code': '+509',
        'flag_emoji': '🇭🇹',
        'region': 'Caribbean'
    },
    'JAM': {
        'iso2': 'JM',
        'name': 'Jamaica',
        'phone_code': '+1876',
        'flag_emoji': '🇯🇲',
        'region': 'Caribbean'
    },
    'CUB': {
        'iso2': 'CU',
        'name': 'Cuba',
        'phone_code': '+53',
        'flag_emoji': '🇨🇺',
        'region': 'Caribbean'
    },
    'DOM': {
        'iso2': 'DO',
        'name': 'Dominican Republic',
        'phone_code': '+1809',
        'flag_emoji': '🇩🇴',
        'region': 'Caribbean'
    },
    'TTO': {
        'iso2': 'TT',
        'name': 'Trinidad and Tobago',
        'phone_code': '+1868',
        'flag_emoji': '🇹🇹',
        'region': 'Caribbean'
    },
    'BRB': {
        'iso2': 'BB',
        'name': 'Barbados',
        'phone_code': '+1246',
        'flag_emoji': '🇧🇧',
        'region': 'Caribbean'
    },
    'BHS': {
        'iso2': 'BS',
        'name': 'Bahamas',
        'phone_code': '+1242',
        'flag_emoji': '🇧🇸',
        'region': 'Caribbean'
    },
    'GRD': {
        'iso2': 'GD',
        'name': 'Grenada',
        'phone_code': '+1473',
        'flag_emoji': '🇬🇩',
        'region': 'Caribbean'
    },
    'LCA': {
        'iso2': 'LC',
        'name': 'Saint Lucia',
        'phone_code': '+1758',
        'flag_emoji': '🇱🇨',
        'region': 'Caribbean'
    },
    'VCT': {
        'iso2': 'VC',
        'name': 'Saint Vincent',
        'phone_code': '+1784',
        'flag_emoji': '🇻🇨',
        'region': 'Caribbean'
    },
    'ATG': {
        'iso2': 'AG',
        'name': 'Antigua and Barbuda',
        'phone_code': '+1268',
        'flag_emoji': '🇦🇬',
        'region': 'Caribbean'
    },
    'DMA': {
        'iso2': 'DM',
        'name': 'Dominica',
        'phone_code': '+1767',
        'flag_emoji': '🇩🇲',
        'region': 'Caribbean'
    },
    'KNA': {
        'iso2': 'KN',
        'name': 'Saint Kitts and Nevis',
        'phone_code': '+1869',
        'flag_emoji': '🇰🇳',
        'region': 'Caribbean'
    },

    # Central America
    'GTM': {
        'iso2': 'GT',
        'name': 'Guatemala',
        'phone_code': '+502',
        'flag_emoji': '🇬🇹',
        'region': 'Central America'
    },
    'HND': {
        'iso2': 'HN',
        'name': 'Honduras',
        'phone_code': '+504',
        'flag_emoji': '🇭🇳',
        'region': 'Central America'
    },
    'SLV': {
        'iso2': 'SV',
        'name': 'El Salvador',
        'phone_code': '+503',
        'flag_emoji': '🇸🇻',
        'region': 'Central America'
    },
    'NIC': {
        'iso2': 'NI',
        'name': 'Nicaragua',
        'phone_code': '+505',
        'flag_emoji': '🇳🇮',
        'region': 'Central America'
    },
    'CRI': {
        'iso2': 'CR',
        'name': 'Costa Rica',
        'phone_code': '+506',
        'flag_emoji': '🇨🇷',
        'region': 'Central America'
    },
    'PAN': {
        'iso2': 'PA',
        'name': 'Panama',
        'phone_code': '+507',
        'flag_emoji': '🇵🇦',
        'region': 'Central America'
    },
    'BLZ': {
        'iso2': 'BZ',
        'name': 'Belize',
        'phone_code': '+501',
        'flag_emoji': '🇧🇿',
        'region': 'Central America'
    },

    # Additional South America
    'BOL': {
        'iso2': 'BO',
        'name': 'Bolivia',
        'phone_code': '+591',
        'flag_emoji': '🇧🇴',
        'region': 'South America'
    },
    'PRY': {
        'iso2': 'PY',
        'name': 'Paraguay',
        'phone_code': '+595',
        'flag_emoji': '🇵🇾',
        'region': 'South America'
    },
    'GUY': {
        'iso2': 'GY',
        'name': 'Guyana',
        'phone_code': '+592',
        'flag_emoji': '🇬🇾',
        'region': 'South America'
    },
    'SUR': {
        'iso2': 'SR',
        'name': 'Suriname',
        'phone_code': '+597',
        'flag_emoji': '🇸🇷',
        'region': 'South America'
    },

    # Additional Africa
    'MOZ': {
        'iso2': 'MZ',
        'name': 'Mozambique',
        'phone_code': '+258',
        'flag_emoji': '🇲🇿',
        'region': 'East Africa'
    },
    'MDG': {
        'iso2': 'MG',
        'name': 'Madagascar',
        'phone_code': '+261',
        'flag_emoji': '🇲🇬',
        'region': 'East Africa'
    },
    'MWI': {
        'iso2': 'MW',
        'name': 'Malawi',
        'phone_code': '+265',
        'flag_emoji': '🇲🇼',
        'region': 'East Africa'
    },
    'ZMB': {
        'iso2': 'ZM',
        'name': 'Zambia',
        'phone_code': '+260',
        'flag_emoji': '🇿🇲',
        'region': 'East Africa'
    },
    'SOM': {
        'iso2': 'SO',
        'name': 'Somalia',
        'phone_code': '+252',
        'flag_emoji': '🇸🇴',
        'region': 'East Africa'
    },
    'DJI': {
        'iso2': 'DJ',
        'name': 'Djibouti',
        'phone_code': '+253',
        'flag_emoji': '🇩🇯',
        'region': 'East Africa'
    },
    'ERI': {
        'iso2': 'ER',
        'name': 'Eritrea',
        'phone_code': '+291',
        'flag_emoji': '🇪🇷',
        'region': 'East Africa'
    },
    'SSD': {
        'iso2': 'SS',
        'name': 'South Sudan',
        'phone_code': '+211',
        'flag_emoji': '🇸🇸',
        'region': 'East Africa'
    },
    'MRT': {
        'iso2': 'MR',
        'name': 'Mauritania',
        'phone_code': '+222',
        'flag_emoji': '🇲🇷',
        'region': 'West Africa'
    },
    'CPV': {
        'iso2': 'CV',
        'name': 'Cape Verde',
        'phone_code': '+238',
        'flag_emoji': '🇨🇻',
        'region': 'West Africa'
    },
    'GNB': {
        'iso2': 'GW',
        'name': 'Guinea-Bissau',
        'phone_code': '+245',
        'flag_emoji': '🇬🇼',
        'region': 'West Africa'
    },
    'GNQ': {
        'iso2': 'GQ',
        'name': 'Equatorial Guinea',
        'phone_code': '+240',
        'flag_emoji': '🇬🇶',
        'region': 'Central Africa'
    },
    'STP': {
        'iso2': 'ST',
        'name': 'São Tomé and Príncipe',
        'phone_code': '+239',
        'flag_emoji': '🇸🇹',
        'region': 'Central Africa'
    },
    'AGO': {
        'iso2': 'AO',
        'name': 'Angola',
        'phone_code': '+244',
        'flag_emoji': '🇦🇴',
        'region': 'Central Africa'
    },
    'LSO': {
        'iso2': 'LS',
        'name': 'Lesotho',
        'phone_code': '+266',
        'flag_emoji': '🇱🇸',
        'region': 'Southern Africa'
    },
    'SWZ': {
        'iso2': 'SZ',
        'name': 'Eswatini',
        'phone_code': '+268',
        'flag_emoji': '🇸🇿',
        'region': 'Southern Africa'
    },
    'COM': {
        'iso2': 'KM',
        'name': 'Comoros',
        'phone_code': '+269',
        'flag_emoji': '🇰🇲',
        'region': 'East Africa'
    },
    'MUS': {
        'iso2': 'MU',
        'name': 'Mauritius',
        'phone_code': '+230',
        'flag_emoji': '🇲🇺',
        'region': 'East Africa'
    },
    'SYC': {
        'iso2': 'SC',
        'name': 'Seychelles',
        'phone_code': '+248',
        'flag_emoji': '🇸🇨',
        'region': 'East Africa'
    },
    'REU': {
        'iso2': 'RE',
        'name': 'Réunion',
        'phone_code': '+262',
        'flag_emoji': '🇷🇪',
        'region': 'East Africa'
    },
    'MYT': {
        'iso2': 'YT',
        'name': 'Mayotte',
        'phone_code': '+262',
        'flag_emoji': '🇾🇹',
        'region': 'East Africa'
    },
    'SDN': {
        'iso2': 'SD',
        'name': 'Sudan',
        'phone_code': '+249',
        'flag_emoji': '🇸🇩',
        'region': 'North Africa'
    },

    # Additional Europe
    'SVK': {
        'iso2': 'SK',
        'name': 'Slovakia',
        'phone_code': '+421',
        'flag_emoji': '🇸🇰',
        'region': 'Eastern Europe'
    },
    'SVN': {
        'iso2': 'SI',
        'name': 'Slovenia',
        'phone_code': '+386',
        'flag_emoji': '🇸🇮',
        'region': 'Southern Europe'
    },
    'BIH': {
        'iso2': 'BA',
        'name': 'Bosnia and Herzegovina',
        'phone_code': '+387',
        'flag_emoji': '🇧🇦',
        'region': 'Southern Europe'
    },
    'MNE': {
        'iso2': 'ME',
        'name': 'Montenegro',
        'phone_code': '+382',
        'flag_emoji': '🇲🇪',
        'region': 'Southern Europe'
    },
    'MKD': {
        'iso2': 'MK',
        'name': 'North Macedonia',
        'phone_code': '+389',
        'flag_emoji': '🇲🇰',
        'region': 'Southern Europe'
    },
    'ALB': {
        'iso2': 'AL',
        'name': 'Albania',
        'phone_code': '+355',
        'flag_emoji': '🇦🇱',
        'region': 'Southern Europe'
    },
    'CYP': {
        'iso2': 'CY',
        'name': 'Cyprus',
        'phone_code': '+357',
        'flag_emoji': '🇨🇾',
        'region': 'Southern Europe'
    },
    'MLT': {
        'iso2': 'MT',
        'name': 'Malta',
        'phone_code': '+356',
        'flag_emoji': '🇲🇹',
        'region': 'Southern Europe'
    },
    'EST': {
        'iso2': 'EE',
        'name': 'Estonia',
        'phone_code': '+372',
        'flag_emoji': '🇪🇪',
        'region': 'Northern Europe'
    },
    'LVA': {
        'iso2': 'LV',
        'name': 'Latvia',
        'phone_code': '+371',
        'flag_emoji': '🇱🇻',
        'region': 'Northern Europe'
    },
    'LTU': {
        'iso2': 'LT',
        'name': 'Lithuania',
        'phone_code': '+370',
        'flag_emoji': '🇱🇹',
        'region': 'Northern Europe'
    },
    'BLR': {
        'iso2': 'BY',
        'name': 'Belarus',
        'phone_code': '+375',
        'flag_emoji': '🇧🇾',
        'region': 'Eastern Europe'
    },
    'MDA': {
        'iso2': 'MD',
        'name': 'Moldova',
        'phone_code': '+373',
        'flag_emoji': '🇲🇩',
        'region': 'Eastern Europe'
    },
    'GEO': {
        'iso2': 'GE',
        'name': 'Georgia',
        'phone_code': '+995',
        'flag_emoji': '🇬🇪',
        'region': 'Eastern Europe'
    },
    'ARM': {
        'iso2': 'AM',
        'name': 'Armenia',
        'phone_code': '+374',
        'flag_emoji': '🇦🇲',
        'region': 'Eastern Europe'
    },
    'AZE': {
        'iso2': 'AZ',
        'name': 'Azerbaijan',
        'phone_code': '+994',
        'flag_emoji': '🇦🇿',
        'region': 'Eastern Europe'
    },
    'AND': {
        'iso2': 'AD',
        'name': 'Andorra',
        'phone_code': '+376',
        'flag_emoji': '🇦🇩',
        'region': 'Western Europe'
    },
    'MCO': {
        'iso2': 'MC',
        'name': 'Monaco',
        'phone_code': '+377',
        'flag_emoji': '🇲🇨',
        'region': 'Western Europe'
    },
    'LIE': {
        'iso2': 'LI',
        'name': 'Liechtenstein',
        'phone_code': '+423',
        'flag_emoji': '🇱🇮',
        'region': 'Western Europe'
    },
    'SMR': {
        'iso2': 'SM',
        'name': 'San Marino',
        'phone_code': '+378',
        'flag_emoji': '🇸🇲',
        'region': 'Southern Europe'
    },
    'VAT': {
        'iso2': 'VA',
        'name': 'Vatican City',
        'phone_code': '+379',
        'flag_emoji': '🇻🇦',
        'region': 'Southern Europe'
    },
    'FRO': {
        'iso2': 'FO',
        'name': 'Faroe Islands',
        'phone_code': '+298',
        'flag_emoji': '🇫🇴',
        'region': 'Northern Europe'
    },
    'GRL': {
        'iso2': 'GL',
        'name': 'Greenland',
        'phone_code': '+299',
        'flag_emoji': '🇬🇱',
        'region': 'North America'
    },

    # Additional Middle East
    'IRQ': {
        'iso2': 'IQ',
        'name': 'Iraq',
        'phone_code': '+964',
        'flag_emoji': '🇮🇶',
        'region': 'Middle East'
    },
    'IRN': {
        'iso2': 'IR',
        'name': 'Iran',
        'phone_code': '+98',
        'flag_emoji': '🇮🇷',
        'region': 'Middle East'
    },
    'SYR': {
        'iso2': 'SY',
        'name': 'Syria',
        'phone_code': '+963',
        'flag_emoji': '🇸🇾',
        'region': 'Middle East'
    },
    'YEM': {
        'iso2': 'YE',
        'name': 'Yemen',
        'phone_code': '+967',
        'flag_emoji': '🇾🇪',
        'region': 'Middle East'
    },
    'OMN': {
        'iso2': 'OM',
        'name': 'Oman',
        'phone_code': '+968',
        'flag_emoji': '🇴🇲',
        'region': 'Middle East'
    },
    'BHR': {
        'iso2': 'BH',
        'name': 'Bahrain',
        'phone_code': '+973',
        'flag_emoji': '🇧🇭',
        'region': 'Middle East'
    },
    'PSE': {
        'iso2': 'PS',
        'name': 'Palestine',
        'phone_code': '+970',
        'flag_emoji': '🇵🇸',
        'region': 'Middle East'
    },

    # Additional Asia Pacific
    'KAZ': {
        'iso2': 'KZ',
        'name': 'Kazakhstan',
        'phone_code': '+7',
        'flag_emoji': '🇰🇿',
        'region': 'Central Asia'
    },
    'UZB': {
        'iso2': 'UZ',
        'name': 'Uzbekistan',
        'phone_code': '+998',
        'flag_emoji': '🇺🇿',
        'region': 'Central Asia'
    },
    'TKM': {
        'iso2': 'TM',
        'name': 'Turkmenistan',
        'phone_code': '+993',
        'flag_emoji': '🇹🇲',
        'region': 'Central Asia'
    },
    'KGZ': {
        'iso2': 'KG',
        'name': 'Kyrgyzstan',
        'phone_code': '+996',
        'flag_emoji': '🇰🇬',
        'region': 'Central Asia'
    },
    'TJK': {
        'iso2': 'TJ',
        'name': 'Tajikistan',
        'phone_code': '+992',
        'flag_emoji': '🇹🇯',
        'region': 'Central Asia'
    },
    'AFG': {
        'iso2': 'AF',
        'name': 'Afghanistan',
        'phone_code': '+93',
        'flag_emoji': '🇦🇫',
        'region': 'Central Asia'
    },
    'MNG': {
        'iso2': 'MN',
        'name': 'Mongolia',
        'phone_code': '+976',
        'flag_emoji': '🇲🇳',
        'region': 'East Asia'
    },
    'PRK': {
        'iso2': 'KP',
        'name': 'North Korea',
        'phone_code': '+850',
        'flag_emoji': '🇰🇵',
        'region': 'East Asia'
    },
    'TWN': {
        'iso2': 'TW',
        'name': 'Taiwan',
        'phone_code': '+886',
        'flag_emoji': '🇹🇼',
        'region': 'East Asia'
    },
    'HKG': {
        'iso2': 'HK',
        'name': 'Hong Kong',
        'phone_code': '+852',
        'flag_emoji': '🇭🇰',
        'region': 'East Asia'
    },
    'MAC': {
        'iso2': 'MO',
        'name': 'Macau',
        'phone_code': '+853',
        'flag_emoji': '🇲🇴',
        'region': 'East Asia'
    },
    'NPL': {
        'iso2': 'NP',
        'name': 'Nepal',
        'phone_code': '+977',
        'flag_emoji': '🇳🇵',
        'region': 'South Asia'
    },
    'BTN': {
        'iso2': 'BT',
        'name': 'Bhutan',
        'phone_code': '+975',
        'flag_emoji': '🇧🇹',
        'region': 'South Asia'
    },
    'LKA': {
        'iso2': 'LK',
        'name': 'Sri Lanka',
        'phone_code': '+94',
        'flag_emoji': '🇱🇰',
        'region': 'South Asia'
    },
    'MDV': {
        'iso2': 'MV',
        'name': 'Maldives',
        'phone_code': '+960',
        'flag_emoji': '🇲🇻',
        'region': 'South Asia'
    },
    'MMR': {
        'iso2': 'MM',
        'name': 'Myanmar',
        'phone_code': '+95',
        'flag_emoji': '🇲🇲',
        'region': 'Southeast Asia'
    },
    'LAO': {
        'iso2': 'LA',
        'name': 'Laos',
        'phone_code': '+856',
        'flag_emoji': '🇱🇦',
        'region': 'Southeast Asia'
    },
    'KHM': {
        'iso2': 'KH',
        'name': 'Cambodia',
        'phone_code': '+855',
        'flag_emoji': '🇰🇭',
        'region': 'Southeast Asia'
    },
    'BRN': {
        'iso2': 'BN',
        'name': 'Brunei',
        'phone_code': '+673',
        'flag_emoji': '🇧🇳',
        'region': 'Southeast Asia'
    },
    'TLS': {
        'iso2': 'TL',
        'name': 'Timor-Leste',
        'phone_code': '+670',
        'flag_emoji': '🇹🇱',
        'region': 'Southeast Asia'
    },
    'PNG': {
        'iso2': 'PG',
        'name': 'Papua New Guinea',
        'phone_code': '+675',
        'flag_emoji': '🇵🇬',
        'region': 'Oceania'
    },
    'FJI': {
        'iso2': 'FJ',
        'name': 'Fiji',
        'phone_code': '+679',
        'flag_emoji': '🇫🇯',
        'region': 'Oceania'
    },
    'SLB': {
        'iso2': 'SB',
        'name': 'Solomon Islands',
        'phone_code': '+677',
        'flag_emoji': '🇸🇧',
        'region': 'Oceania'
    },
    'VUT': {
        'iso2': 'VU',
        'name': 'Vanuatu',
        'phone_code': '+678',
        'flag_emoji': '🇻🇺',
        'region': 'Oceania'
    },
    'NCL': {
        'iso2': 'NC',
        'name': 'New Caledonia',
        'phone_code': '+687',
        'flag_emoji': '🇳🇨',
        'region': 'Oceania'
    },
    'PYF': {
        'iso2': 'PF',
        'name': 'French Polynesia',
        'phone_code': '+689',
        'flag_emoji': '🇵🇫',
        'region': 'Oceania'
    },
    'WSM': {
        'iso2': 'WS',
        'name': 'Samoa',
        'phone_code': '+685',
        'flag_emoji': '🇼🇸',
        'region': 'Oceania'
    },
    'TON': {
        'iso2': 'TO',
        'name': 'Tonga',
        'phone_code': '+676',
        'flag_emoji': '🇹🇴',
        'region': 'Oceania'
    },
    'KIR': {
        'iso2': 'KI',
        'name': 'Kiribati',
        'phone_code': '+686',
        'flag_emoji': '🇰🇮',
        'region': 'Oceania'
    },
    'MHL': {
        'iso2': 'MH',
        'name': 'Marshall Islands',
        'phone_code': '+692',
        'flag_emoji': '🇲🇭',
        'region': 'Oceania'
    },
    'FSM': {
        'iso2': 'FM',
        'name': 'Micronesia',
        'phone_code': '+691',
        'flag_emoji': '🇫🇲',
        'region': 'Oceania'
    },
    'PLW': {
        'iso2': 'PW',
        'name': 'Palau',
        'phone_code': '+680',
        'flag_emoji': '🇵🇼',
        'region': 'Oceania'
    },
    'NRU': {
        'iso2': 'NR',
        'name': 'Nauru',
        'phone_code': '+674',
        'flag_emoji': '🇳🇷',
        'region': 'Oceania'
    },
    'TUV': {
        'iso2': 'TV',
        'name': 'Tuvalu',
        'phone_code': '+688',
        'flag_emoji': '🇹🇻',
        'region': 'Oceania'
    },

    # Additional territories and dependencies
    'GUM': {
        'iso2': 'GU',
        'name': 'Guam',
        'phone_code': '+1671',
        'flag_emoji': '🇬🇺',
        'region': 'Oceania'
    },
    'ASM': {
        'iso2': 'AS',
        'name': 'American Samoa',
        'phone_code': '+1684',
        'flag_emoji': '🇦🇸',
        'region': 'Oceania'
    },
    'MNP': {
        'iso2': 'MP',
        'name': 'Northern Mariana Islands',
        'phone_code': '+1670',
        'flag_emoji': '🇲🇵',
        'region': 'Oceania'
    },
    'PRI': {
        'iso2': 'PR',
        'name': 'Puerto Rico',
        'phone_code': '+1787',
        'flag_emoji': '🇵🇷',
        'region': 'Caribbean'
    },
    'VIR': {
        'iso2': 'VI',
        'name': 'US Virgin Islands',
        'phone_code': '+1340',
        'flag_emoji': '🇻🇮',
        'region': 'Caribbean'
    },
    'VGB': {
        'iso2': 'VG',
        'name': 'British Virgin Islands',
        'phone_code': '+1284',
        'flag_emoji': '🇻🇬',
        'region': 'Caribbean'
    },
    'CYM': {
        'iso2': 'KY',
        'name': 'Cayman Islands',
        'phone_code': '+1345',
        'flag_emoji': '🇰🇾',
        'region': 'Caribbean'
    },
    'BMU': {
        'iso2': 'BM',
        'name': 'Bermuda',
        'phone_code': '+1441',
        'flag_emoji': '🇧🇲',
        'region': 'North America'
    },
    'GLP': {
        'iso2': 'GP',
        'name': 'Guadeloupe',
        'phone_code': '+590',
        'flag_emoji': '🇬🇵',
        'region': 'Caribbean'
    },
    'MTQ': {
        'iso2': 'MQ',
        'name': 'Martinique',
        'phone_code': '+596',
        'flag_emoji': '🇲🇶',
        'region': 'Caribbean'
    },
    'GUF': {
        'iso2': 'GF',
        'name': 'French Guiana',
        'phone_code': '+594',
        'flag_emoji': '🇬🇫',
        'region': 'South America'
    },
    'ABW': {
        'iso2': 'AW',
        'name': 'Aruba',
        'phone_code': '+297',
        'flag_emoji': '🇦🇼',
        'region': 'Caribbean'
    },
    'CUW': {
        'iso2': 'CW',
        'name': 'Curaçao',
        'phone_code': '+599',
        'flag_emoji': '🇨🇼',
        'region': 'Caribbean'
    },
    'SXM': {
        'iso2': 'SX',
        'name': 'Sint Maarten',
        'phone_code': '+1721',
        'flag_emoji': '🇸🇽',
        'region': 'Caribbean'
    },
    'TCA': {
        'iso2': 'TC',
        'name': 'Turks and Caicos',
        'phone_code': '+1649',
        'flag_emoji': '🇹🇨',
        'region': 'Caribbean'
    },
    'MSR': {
        'iso2': 'MS',
        'name': 'Montserrat',
        'phone_code': '+1664',
        'flag_emoji': '🇲🇸',
        'region': 'Caribbean'
    },
    'AIA': {
        'iso2': 'AI',
        'name': 'Anguilla',
        'phone_code': '+1264',
        'flag_emoji': '🇦🇮',
        'region': 'Caribbean'
    },
    'FLK': {
        'iso2': 'FK',
        'name': 'Falkland Islands',
        'phone_code': '+500',
        'flag_emoji': '🇫🇰',
        'region': 'South America'
    },
    'GIB': {
        'iso2': 'GI',
        'name': 'Gibraltar',
        'phone_code': '+350',
        'flag_emoji': '🇬🇮',
        'region': 'Southern Europe'
    },

    # Additional territories
    'BES': {
        'iso2': 'BQ',
        'name': 'Bonaire, Sint Eustatius and Saba',
        'phone_code': '+599',
        'flag_emoji': '🇧🇶',
        'region': 'Caribbean'
    },
    'BLM': {
        'iso2': 'BL',
        'name': 'Saint Barthélemy',
        'phone_code': '+590',
        'flag_emoji': '🇧🇱',
        'region': 'Caribbean'
    },
    'COK': {
        'iso2': 'CK',
        'name': 'Cook Islands',
        'phone_code': '+682',
        'flag_emoji': '🇨🇰',
        'region': 'Oceania'
    },
    'CXR': {
        'iso2': 'CX',
        'name': 'Christmas Island',
        'phone_code': '+61',
        'flag_emoji': '🇨🇽',
        'region': 'Oceania'
    },
    'GGY': {
        'iso2': 'GG',
        'name': 'Guernsey',
        'phone_code': '+44',
        'flag_emoji': '🇬🇬',
        'region': 'Western Europe'
    },
    'IMN': {
        'iso2': 'IM',
        'name': 'Isle of Man',
        'phone_code': '+44',
        'flag_emoji': '🇮🇲',
        'region': 'Western Europe'
    },
    'JEY': {
        'iso2': 'JE',
        'name': 'Jersey',
        'phone_code': '+44',
        'flag_emoji': '🇯🇪',
        'region': 'Western Europe'
    },
    'MAF': {
        'iso2': 'MF',
        'name': 'Saint Martin',
        'phone_code': '+590',
        'flag_emoji': '🇲🇫',
        'region': 'Caribbean'
    },
    'NFK': {
        'iso2': 'NF',
        'name': 'Norfolk Island',
        'phone_code': '+672',
        'flag_emoji': '🇳🇫',
        'region': 'Oceania'
    },
    'NIU': {
        'iso2': 'NU',
        'name': 'Niue',
        'phone_code': '+683',
        'flag_emoji': '🇳🇺',
        'region': 'Oceania'
    },
    'PCN': {
        'iso2': 'PN',
        'name': 'Pitcairn Islands',
        'phone_code': '+64',
        'flag_emoji': '🇵🇳',
        'region': 'Oceania'
    },
    'SGS': {
        'iso2': 'GS',
        'name': 'South Georgia',
        'phone_code': '+500',
        'flag_emoji': '🇬🇸',
        'region': 'South America'
    },
    'SHN': {
        'iso2': 'SH',
        'name': 'Saint Helena',
        'phone_code': '+290',
        'flag_emoji': '🇸🇭',
        'region': 'West Africa'
    },
    'SPM': {
        'iso2': 'PM',
        'name': 'Saint Pierre and Miquelon',
        'phone_code': '+508',
        'flag_emoji': '🇵🇲',
        'region': 'North America'
    },
    'WLF': {
        'iso2': 'WF',
        'name': 'Wallis and Futuna',
        'phone_code': '+681',
        'flag_emoji': '🇼🇫',
        'region': 'Oceania'
    },
    'XKS': {
        'iso2': 'XK',
        'name': 'Kosovo',
        'phone_code': '+383',
        'flag_emoji': '🇽🇰',
        'region': 'Southern Europe'
    },
    'XSV': {
        'iso2': 'XR',
        'name': 'Svalbard',
        'phone_code': '+47',
        'flag_emoji': '🇸🇯',
        'region': 'Northern Europe'
    },
    'XGZ': {
        'iso2': 'XG',
        'name': 'Gaza Strip',
        'phone_code': '+970',
        'flag_emoji': '🇵🇸',
        'region': 'Middle East'
    },
    'XWB': {
        'iso2': 'XW',
        'name': 'West Bank',
        'phone_code': '+970',
        'flag_emoji': '🇵🇸',
        'region': 'Middle East'
    },
}


def get_country_info(iso3_code):
    """
    Get country information by ISO3 code.

    Args:
        iso3_code: Three-letter ISO3 country code (e.g., 'BEN', 'CAN')

    Returns:
        Dictionary with country info or None if not found
    """
    return COUNTRY_DATA.get(iso3_code.upper())


def get_phone_code(iso3_code):
    """Get phone code for a country by ISO3 code."""
    info = get_country_info(iso3_code)
    return info['phone_code'] if info else None


def get_flag_emoji(iso3_code):
    """Get flag emoji for a country by ISO3 code."""
    info = get_country_info(iso3_code)
    return info['flag_emoji'] if info else None


def get_region(iso3_code):
    """Get region for a country by ISO3 code."""
    info = get_country_info(iso3_code)
    return info['region'] if info else None


def get_iso2(iso3_code):
    """Get ISO2 code for a country by ISO3 code."""
    info = get_country_info(iso3_code)
    return info['iso2'] if info else None
