# Administrative Data Import Scripts

Automated import scripts for Benin and Quebec administrative division data.

## Folder Structure

Create the following folder structure in your shapefiles directory:

```
/app/shapefiles/
├── benin/
│   ├── ben_admbnda_adm1_1m_salb_20190816.shp (+ .dbf, .shx, .prj files)
│   ├── ben_admbnda_adm2_1m_salb_20190816_fixed.shp (+ .dbf, .shx, .prj files)
│   └── ben_admbnda_adm3_1m_salb_20190816_corrected.shp (+ .dbf, .shx, .prj files)
└── quebec/
    ├── QUEBEC_region_s.shp (+ .dbf, .shx, .prj files)
    ├── QUEBEC_mrc_s.shp (+ .dbf, .shx, .prj files)
    ├── QUEBEC_munic_s.shp (+ .dbf, .shx, .prj files)
    └── QUEBEC_arron_s.shp (+ .dbf, .shx, .prj files)
```

## Usage

### 1. Check Data Structure
First, verify your data files are in the correct locations:

```bash
docker compose exec backend python check_data_structure.py
```

### 2. Run Complete Import
Import all administrative data for both countries:

```bash
docker compose exec backend python import_admin_data.py
```

## What Gets Imported

### Benin Administrative Hierarchy
- **Level 1**: 12 Departments
- **Level 2**: 77 Communes
- **Level 3**: 546 Arrondissements
- **Total**: 635 administrative divisions

### Quebec Administrative Hierarchy
- **Level 1**: 1 Province (Quebec)
- **Level 2**: 17 Administrative Regions
- **Level 3**: 104 MRCs (Regional County Municipalities)
- **Level 4**: 1,345 Municipalities/Territories
  - 1,100 Municipalités (M, V, VL, P, CT, CU)
  - 161 Territoires non organisés (NO, G, GR)
  - 84 Territoires autochtones (TI, R, VC, VN, VK, TC, TK, EI)
- **Level 5**: 41 Arrondissements (across 8 major cities)
- **Total**: 1,467 administrative divisions

### Grand Total: 2,102 administrative divisions

## Features

- **Automatic Country Creation**: Creates Benin and Canada countries if they don't exist
- **Parent-Child Relationships**: Automatically establishes hierarchical relationships
- **Geometry Handling**: Converts Polygon to MultiPolygon as needed
- **Error Handling**: Comprehensive error logging and recovery
- **Progress Tracking**: Real-time import progress with detailed logging
- **Data Cleanup**: Clears existing data before re-import to avoid duplicates
- **Independent Cities**: Correctly handles Quebec independent cities (where municipality name = MRC name)

## Logging

The script provides detailed logging output showing:
- Import progress for each level
- Success/error counts
- Parent relationship establishment
- Final summary statistics

## Error Recovery

The script is designed to:
- Continue processing if individual records fail
- Log detailed error information
- Provide final success/failure status for each country
- Clear existing data before re-import to ensure clean state

## File Requirements

Each .shp file must be accompanied by its supporting files (.dbf, .shx, .prj, .cpg).

The script will automatically detect and use the appropriate field names from each shapefile.