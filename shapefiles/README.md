# Shapefile Data Directory

This directory contains geographic data that is automatically loaded into the database during project setup. The system supports intelligent auto-detection of data sources and administrative levels.

## Current Data Structure

```
shapefiles/
├── README.md                           # This file
├── ben_adm_1m_salb_2019_shapes/        # Benin SALB administrative data
│   ├── ben_admbnda_adm0_1m_salb_20190816.shp     # Country level
│   ├── ben_admbnda_adm1_1m_salb_20190816.shp     # Departments
│   ├── ben_admbnda_adm2_1m_salb_20190816_fixed.shp # Municipalities
│   └── geoBoundaries-BEN-ADM3-with-codes.shp     # Communes (546 total)
├── quebec_adm/                         # Quebec SDA administrative data
│   ├── QUEBEC_comet_s.shp             # Communities
│   ├── QUEBEC_regio_s.shp             # Regions
│   ├── QUEBEC_mrc_s.shp               # MRC (Regional County Municipalities)
│   ├── QUEBEC_munic_s.shp             # Municipalities
│   └── QUEBEC_arron_s.shp             # Arrondissements
└── [other country data...]
```

## Supported Countries & Default Divisions

- **🇧🇯 Benin**: Default level 2 (communes) - 77 divisions
- **🇨🇦 Canada/Quebec**: Default level 4 (municipalités) - 1,343 divisions

### Benin Administrative Hierarchy
- Level 0: pays (country) - 1
- Level 1: départements (departments) - 12
- Level 2: communes (municipalities) - 77 **← Default Level**
- Level 3: arrondissements (sub-municipal divisions) - 546

> **Note**: Communes are the primary municipal administrative level in Benin, while arrondissements are sub-divisions within communes.

## Adding New Geographic Data

### Method 1: Auto-Detection (Recommended)
1. **Place shapefile folder**: Create a country-specific folder in `shapefiles/`
2. **Add all admin levels**: Include shapefiles for different administrative levels
3. **Configure field mappings** (optional): Edit `core/geo_data_mappings.json` for custom field mappings
4. **Run auto-detection**:
   ```bash
   docker compose exec backend python manage.py load_geo_data --auto-detect /app/shapefiles/your_country_folder/
   ```

### Method 2: Manual Loading
1. **Setup country first**:
   ```bash
   docker compose exec backend python manage.py setup_country --iso3 USA --iso2 US --name "United States" --default-admin-level 3
   ```

2. **Load individual shapefiles**:
   ```bash
   docker compose exec backend python manage.py load_geo_data --shapefile path/to/states.shp --country USA --admin-level 1
   docker compose exec backend python manage.py load_geo_data --shapefile path/to/counties.shp --country USA --admin-level 2
   ```

### Method 3: Complete Setup Script
Use the comprehensive setup script for new deployments:
```bash
./setup.sh --cleanup              # Full clean setup with all data
./setup.sh --start-from geodata   # Just load geographic data
```

## Management Commands Reference

> **⚠️ Important**: All Django management commands must be executed within the Docker environment using `docker compose exec backend`. Alternatively, you can install all Python dependencies locally (PostgreSQL, PostGIS, GDAL, etc.) to run commands directly.

### Local Installation Requirements (Alternative to Docker)
If you prefer to run commands locally instead of using Docker, install:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib postgis gdal-bin python3-gdal

# macOS (with Homebrew)
brew install postgresql postgis gdal

# Python dependencies
pip install -r requirements.txt
```

### Country Setup
```bash
# Create new country with default admin level
docker compose exec backend python manage.py setup_country --iso3 FRA --iso2 FR --name "France" --default-admin-level 3

# Create from shapefile (country boundary)
docker compose exec backend python manage.py setup_country --from-shapefile country_boundary.shp
```

### Geographic Data Loading
```bash
# Auto-detect and load all shapefiles in a directory
docker compose exec backend python manage.py load_geo_data --auto-detect /app/shapefiles/country_folder/

# Load specific shapefile
docker compose exec backend python manage.py load_geo_data --shapefile admin.shp --country FRA --admin-level 2

# Batch load from configuration file
docker compose exec backend python manage.py load_geo_data --batch batch_config.json

# Dry run (test without importing)
docker compose exec backend python manage.py load_geo_data --shapefile admin.shp --country FRA --admin-level 1 --dry-run
```

### Setup System
```bash
# Complete setup with cleanup
./setup.sh --cleanup

# List available steps
./setup.sh --list-steps

# Resume from specific step (uses step names, not numbers)
./setup.sh --start-from build      # Start from building backend
./setup.sh --start-from migrate    # Start from database migrations
./setup.sh --start-from superuser  # Start from admin user creation
./setup.sh --start-from countries  # Start from country setup
./setup.sh --start-from geodata    # Start from geographic data loading
./setup.sh --start-from status     # Just show service status
```

## Auto-Detection System

The system automatically detects:
- **Data Source**: SALB, SDA, geoBoundaries, etc.
- **Country**: From filename patterns and content analysis
- **Admin Level**: Based on field analysis and feature count
- **Field Mappings**: Uses `geo_data_mappings.json` configuration
- **Boundary Types**: Dynamic, country-specific boundary types
- **Parent Relationships**: Automatic hierarchy building

### Field Mapping Configuration

Edit `core/geo_data_mappings.json` to customize field mappings:

```json
{
  "data_sources": {
    "SALB": {
      "country_code": "BEN",
      "admin_levels": {
        "1": {"name_field": "ADM1_FR", "code_field": "ADM1_PCODE"},
        "2": {"name_field": "ADM2_FR", "code_field": "ADM2_PCODE"}
      }
    },
    "SDA": {
      "country_code": "CAN",
      "admin_levels": {
        "4": {"name_field": "MUS_NM_MUN", "parent_field": "MRC_NM_MRC"}
      }
    }
  }
}
```

## Default Administrative Levels

Each country has a configured default administrative level:

- **Purpose**: Define the primary division type for APIs and applications
- **Benin**: Level 2 (communes) - Primary municipal level (77 communes)
- **Canada**: Level 4 (municipalités) - Used for municipality-level operations

### Using Default Divisions in Code

```python
from core.models import Country

# Get default divisions for any country
country = Country.objects.get(iso3='BEN')
default_divisions = country.get_default_divisions()  # Returns QuerySet of 77 communes
division_type = country.get_default_division_name()  # Returns "communes"

# Get all boundary types by level
boundary_types = country.get_boundary_types_by_level()
# Returns: {0: 'pays', 1: 'départements', 2: 'communes', 3: 'arrondissements'}
```

## Troubleshooting

### Import Issues
- **Encoding errors**: Check file encoding, try different codepages
- **Geometry errors**: Ensure polygons are valid MultiPolygons
- **Field mapping**: Verify field names match `geo_data_mappings.json`
- **Parent relationships**: Check that parent divisions exist before importing children

### Uniqueness Constraint Errors
- **Solution**: The system uses `(admin_code, country, admin_level)` for uniqueness
- **Duplicate names**: Handled automatically with parent relationships
- **Admin codes**: Must be unique within country and admin level

### Debugging Commands
```bash
# Check detection without importing
docker compose exec backend python manage.py load_geo_data --shapefile file.shp --country BEN --admin-level 3 --dry-run

# Verbose output for debugging
docker compose exec backend python manage.py load_geo_data --auto-detect folder/ --verbosity 2

# Clean slate for testing
./setup.sh --cleanup
```

## File Requirements

### Required Shapefile Components
- `.shp` - Shape format; the feature geometry
- `.shx` - Shape index format; positional index
- `.dbf` - Attribute format; columnar attributes for each shape
- `.prj` - Projection format; coordinate system and projection info

### Optional Components
- `.cpg` - Code page file; identifies character encoding
- `.sbn/.sbx` - Spatial index files (improve performance)

### Supported Data Sources
- **SALB** (Service d'Administration du Territoire) - Benin
- **SDA** (Secrétariat aux affaires intergouvernementales) - Quebec
- **geoBoundaries** - Global administrative boundaries
- **Custom** - Any properly formatted administrative boundary data

## Data Quality Standards

### Geometry Requirements
- **Polygons**: Must be valid and properly closed
- **Multi-part features**: Automatically converted to MultiPolygon
- **Projection**: Any projection (automatically handled by PostGIS)
- **Topology**: Self-intersections and invalid geometries are flagged

### Attribute Requirements
- **Name field**: Required for all features
- **Admin code**: Unique identifier within admin level
- **Parent reference**: For building hierarchical relationships
- **Boundary type**: Derived from data source configuration

### Performance Considerations
- **File size**: Large shapefiles are processed in batches
- **Memory usage**: Geometry conversion uses streaming for efficiency
- **Database**: Uses spatial indexes for optimal query performance
- **Uniqueness**: Database constraints ensure data integrity

## Production Deployment

### Initial Setup
1. Place all shapefile data in appropriate country folders
2. Configure field mappings in `geo_data_mappings.json`
3. Set country default admin levels during country creation
4. Run complete setup: `./setup.sh --cleanup`

### Adding New Countries
1. Create country: `docker compose exec backend python manage.py setup_country --iso3 XXX --name "Country" --default-admin-level N`
2. Add shapefile data to `shapefiles/country_folder/`
3. Run auto-detection: `docker compose exec backend python manage.py load_geo_data --auto-detect shapefiles/country_folder/`
4. Verify import: Check admin panel or use country methods

### Maintenance
- **Updates**: Use `--overwrite` flag to update existing data
- **Cleanup**: Use `./cleanup.sh` to reset database
- **Migration**: Database migrations handle schema changes automatically