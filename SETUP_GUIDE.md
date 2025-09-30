# Citinfos Backend Setup Guide

This guide provides comprehensive setup instructions for the Citinfos Backend project with all its services and geographic data loading capabilities.

## Prerequisites

- Docker and Docker Compose
- At least 4GB of available RAM
- 10GB of free disk space

## Quick Setup (Recommended)

### Option 1: Complete Setup Script
```bash
# Complete setup with all services and data loading
./setup.sh
```

This script will:
- ✅ Build the backend Docker image
- ✅ Start all services (database, backend, celery, frontend, elasticsearch, etc.)
- ✅ Run database migrations
- ✅ Create default admin user (admin/admin)
- ✅ Setup countries (Benin, Canada)
- ✅ Auto-detect and load geographic data from shapefiles
- ✅ Display service URLs and status

### Option 2: Quick Start (Minimal)
```bash
# Quick setup for development
./quickstart.sh
```

This script provides minimal setup for development without geographic data loading.

## Manual Setup

If you prefer to set up manually or need to understand the process:

### 1. Build Backend
```bash
docker compose build backend
```

### 2. Start All Services
```bash
docker compose up -d
```

This starts all services:
- **postgis**: PostgreSQL with PostGIS extension
- **redis**: Redis cache and message broker
- **backend**: Django backend API
- **celery**: Background task worker
- **celery-beat**: Periodic task scheduler
- **flower**: Celery monitoring
- **frontend**: Vue.js frontend
- **elasticsearch**: Search engine
- **logstash**: Data processing pipeline
- **autocomplete**: Address autocomplete service

### 3. Run Migrations
```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

### 4. Create Admin User
```bash
docker compose exec backend python manage.py createsuperuser
```

### 5. Setup Countries
```bash
# Setup Benin
docker compose exec backend python manage.py setup_country \
    --name "Benin" --iso3 "BEN" --iso2 "BJ"

# Setup Canada
docker compose exec backend python manage.py setup_country \
    --name "Canada" --iso3 "CAN" --iso2 "CA"
```

## Geographic Data Loading

The system supports automatic loading of geographic data from shapefiles.

### Available Data Sources

Place your shapefiles in the appropriate directories:

- **Benin SALB Data**: `shapefiles/ben_adm_1m_salb_2019_shapes/`
- **Quebec Administrative Data**: `shapefiles/quebec_adm/`

### Auto-Detection Loading
```bash
# Load Benin administrative boundaries
docker compose exec backend python manage.py load_geo_data \
    --auto-detect /app/shapefiles/ben_adm_1m_salb_2019_shapes/

# Load Quebec administrative boundaries
docker compose exec backend python manage.py load_geo_data \
    --auto-detect /app/shapefiles/quebec_adm/
```

### Custom Mapping Loading
```bash
# Generate mapping template for unknown data
docker compose exec backend python manage.py generate_field_mappings \
    /app/shapefiles/your_data/ --output custom_mappings.json

# Load with custom mapping
docker compose exec backend python manage.py load_geo_data \
    --auto-detect /app/shapefiles/your_data/ \
    --mapping-file custom_mappings.json
```

## Service URLs

After setup, access the services at:

- 🌐 **Backend API**: http://localhost:8000
- 👥 **Admin Interface**: http://localhost:8000/admin
- 🌍 **Frontend**: http://localhost:3000
- 📊 **Celery Flower**: http://localhost:5555
- 🔧 **Redis Commander**: http://localhost:8081 (admin/admin)
- 🔍 **Elasticsearch**: http://localhost:9200
- 🔗 **Autocomplete Service**: http://localhost:4000

## Default Credentials

- **Admin User**: admin / admin
- **Redis Commander**: admin / admin

## Troubleshooting

### Check Service Status
```bash
docker compose ps
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f postgis
```

### Restart Services
```bash
docker compose restart [service_name]
```

### Clean Restart
```bash
docker compose down
docker compose up -d
```

### Database Issues
```bash
# Reset database
docker compose down -v
docker compose up -d postgis
# Wait for database to start, then run migrations
```

### Check Data Loading Status
```bash
# Check countries
docker compose exec backend python manage.py shell -c "
from accounts.models import Country;
print(f'Countries: {Country.objects.count()}')"

# Check administrative divisions
docker compose exec backend python manage.py shell -c "
from accounts.models import AdministrativeDivision;
print(f'Admin divisions: {AdministrativeDivision.objects.count()}')"
```

## Development Commands

### Run Tests
```bash
docker compose exec backend python manage.py test
```

### Create App
```bash
docker compose exec backend python manage.py startapp myapp
```

### Django Shell
```bash
docker compose exec backend python manage.py shell
```

### Database Shell
```bash
docker compose exec postgis psql -U citinfos citinfos_db
```

## Production Deployment

For production deployment:

1. Update environment variables in `.env`
2. Use production-grade reverse proxy (nginx)
3. Enable SSL/TLS certificates
4. Configure proper backup strategies
5. Set up monitoring and logging
6. Review security settings

## Support

For issues or questions:
1. Check the logs first
2. Review this setup guide
3. Consult the individual service documentation
4. Open an issue with detailed error information