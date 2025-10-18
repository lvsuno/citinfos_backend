#!/bin/bash

# Citinfos Backend Complete Setup Script
# This script builds the backend, starts all services, and loads geo data

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if Docker is running
check_docker() {
    log_info "Checking Docker availability..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    if ! docker compose version >/dev/null 2>&1; then
        log_error "Docker Compose is not available. Please install Docker Compose and try again."
        exit 1
    fi

    log_success "Docker and Docker Compose are available"
}

# Check if required files exist
check_files() {
    log_info "Checking required files..."

    local required_files=(
        "docker-compose.yml"
        "Dockerfile.backend"
        "requirements.txt"
        ".env"
        "core/management/commands/load_geo_data.py"
        "core/management/commands/setup_country.py"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done

    log_success "All required files found"
}

# Check for shapefile data
check_shapefiles() {
    log_info "Checking available shapefile data..."

    if [[ -d "shapefiles/ben_adm_1m_salb_2019_shapes" ]]; then
        log_success "Benin SALB shapefile data found"
        BENIN_DATA_AVAILABLE=true
    else
        log_warning "Benin SALB shapefile data not found in shapefiles/ben_adm_1m_salb_2019_shapes"
        BENIN_DATA_AVAILABLE=false
    fi

    if [[ -d "shapefiles/quebec_adm" ]]; then
        log_success "Quebec administrative shapefile data found"
        QUEBEC_DATA_AVAILABLE=true
    else
        log_warning "Quebec administrative shapefile data not found in shapefiles/quebec_adm"
        QUEBEC_DATA_AVAILABLE=false
    fi

    if [[ "$BENIN_DATA_AVAILABLE" == false && "$QUEBEC_DATA_AVAILABLE" == false ]]; then
        log_warning "No shapefile data found. Only basic setup will be performed."
    fi
}

# Stop and remove existing containers
cleanup_existing() {
    log_header "Cleaning up existing containers"

    log_info "Stopping existing containers..."
    docker compose down --remove-orphans || true

    log_info "Removing unused Docker images and volumes..."
    docker system prune -f || true

    log_success "Cleanup completed"
}

# Build backend
build_backend() {
    log_header "Building Backend"

    log_info "Building backend Docker image..."
    docker compose build backend --no-cache

    if [[ $? -eq 0 ]]; then
        log_success "Backend built successfully"
    else
        log_error "Failed to build backend"
        exit 1
    fi
}

# Start services
start_services() {
    log_header "Starting All Services"

    log_info "Starting all services with docker compose up -d..."
    docker compose up -d

    log_info "Waiting for database to be ready..."
    local max_attempts=60
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if docker compose exec postgis pg_isready -U ${POSTGRES_USER:-citinfos} -d ${POSTGRES_DATABASE:-citinfos_db} >/dev/null 2>&1; then
            log_success "Database is ready"
            break
        fi

        log_info "Attempt $attempt/$max_attempts: Waiting for database..."
        sleep 3
        ((attempt++))
    done

    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Database failed to start within timeout"
        exit 1
    fi

    log_info "Waiting for backend service to be ready..."
    sleep 15

    # Check if backend is responding
    local backend_attempts=20
    local backend_attempt=1

    while [[ $backend_attempt -le $backend_attempts ]]; do
        if docker compose exec backend python manage.py check >/dev/null 2>&1; then
            log_success "Backend is ready"
            break
        fi

        log_info "Attempt $backend_attempt/$backend_attempts: Waiting for backend..."
        sleep 3
        ((backend_attempt++))
    done

    if [[ $backend_attempt -gt $backend_attempts ]]; then
        log_error "Backend failed to start within timeout"
        exit 1
    fi

    log_success "All services started successfully"
}

# Run database migrations
run_migrations() {
    log_header "Running Database Migrations"

    log_info "Creating and running migrations..."

    # Try to run migrations, catch any dependency issues
    if ! docker compose exec backend python manage.py makemigrations; then
        log_error "Failed to create migrations"
        exit 1
    fi

    if ! docker compose exec backend python manage.py migrate; then
        log_error "Migration failed due to dependency issues"
        log_warning "This usually happens when migration history is inconsistent"
        echo ""
        echo "To fix this, you can:"
        echo "1. Run: ./reset_migrations.sh --full"
        echo "2. Then run: ./setup.sh"
        echo ""
        echo "Or run: ./setup.sh --cleanup (includes migration reset)"
        exit 1
    fi

    log_success "Database migrations completed"
}

# Create superuser if needed
create_superuser() {
    log_header "Setting up Admin User"

    log_info "Checking for existing superuser..."
    local has_superuser=$(docker compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
print(User.objects.filter(is_superuser=True).exists())
" | tr -d '\r')

    if [[ "$has_superuser" == "True" ]]; then
        log_success "Superuser already exists"
    else
        log_info "Creating default superuser (admin/admin)..."
        docker compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin');
    print('Superuser created successfully')
else:
    print('Admin user already exists')
"
        log_success "Admin user setup completed"
    fi
}

# Setup countries
setup_countries() {
    log_header "Setting up Countries"

    log_info "Setting up Benin..."
    docker compose exec backend python manage.py setup_country \
        --name "Benin" \
        --iso3 "BEN" \
        --iso2 "BJ" \
        --overwrite

    log_info "Setting up Canada..."
    docker compose exec backend python manage.py setup_country \
        --name "Canada" \
        --iso3 "CAN" \
        --iso2 "CA" \
        --overwrite

    log_success "Countries setup completed"

    # Populate phone data for all countries
    log_info "Populating phone data for countries..."
    if docker compose exec backend python populate_country_phone_data.py 2>&1 | tee /tmp/country_phone_update.log; then
        log_success "Phone data populated successfully"
    else
        log_warning "Phone data population had issues. Check logs for details."
    fi
}

# Load geo data
load_geo_data() {
    log_header "Loading Geographic Data"

    if [[ "$BENIN_DATA_AVAILABLE" == true ]]; then
        log_info "Loading Benin administrative data..."

        # Load Benin data using auto-detection
        log_info "Auto-detecting and loading Benin SALB data..."
        docker compose exec backend python manage.py load_geo_data \
            --auto-detect /app/shapefiles/ben_adm_1m_salb_2019_shapes/ \
            --overwrite

        # Specifically load Benin ADM3 (communes) if it wasn't imported by auto-detection
        log_info "Ensuring Benin ADM3 communes are loaded..."

        # Check current ADM3 count
        local adm3_count=$(docker compose exec backend python manage.py shell -c "
from accounts.models import AdministrativeDivision;
print(AdministrativeDivision.objects.filter(country__iso3='BEN', admin_level=3).count())
" 2>/dev/null | grep -E '^[0-9]+$' || echo "0")

        log_info "Current Benin ADM3 count: $adm3_count"

        if [[ "$adm3_count" -eq 0 ]]; then
            log_info "No ADM3 communes found. Clearing all Benin data and reimporting..."

            # Clear all existing Benin administrative data to avoid conflicts
            docker compose exec backend python manage.py shell -c "
from accounts.models import AdministrativeDivision;
deleted = AdministrativeDivision.objects.filter(country__iso3='BEN').delete();
print(f'Cleared {deleted[0]} existing Benin records')
"

            log_info "Reimporting all Benin administrative data from scratch..."
            docker compose exec backend python manage.py load_geo_data \
                --auto-detect /app/shapefiles/ben_adm_1m_salb_2019_shapes/ \
                --overwrite

            # Verify the import
            local new_adm3_count=$(docker compose exec backend python manage.py shell -c "
from accounts.models import AdministrativeDivision;
print(AdministrativeDivision.objects.filter(country__iso3='BEN', admin_level=3).count())
" 2>/dev/null | grep -E '^[0-9]+$' || echo "0")

            log_info "New Benin ADM3 count: $new_adm3_count"

            if [[ "$new_adm3_count" -gt 0 ]]; then
                log_success "Successfully loaded $new_adm3_count Benin communes"
            else
                log_warning "Benin ADM3 communes import failed - manual investigation needed"
            fi
        else
            log_success "Benin ADM3 communes already loaded ($adm3_count records)"
        fi

        if [[ $? -eq 0 ]]; then
            log_success "Benin geographic data loaded successfully"
        else
            log_error "Failed to load Benin geographic data"
        fi
    fi

    if [[ "$QUEBEC_DATA_AVAILABLE" == true ]]; then
        log_info "Loading Quebec administrative data..."

        # Load Quebec data using auto-detection
        log_info "Auto-detecting and loading Quebec administrative data..."
        docker compose exec backend python manage.py load_geo_data \
            --auto-detect /app/shapefiles/quebec_adm/ \
            --overwrite

        if [[ $? -eq 0 ]]; then
            log_success "Quebec geographic data loaded successfully"
        else
            log_error "Failed to load Quebec geographic data"
        fi
    fi

    if [[ "$BENIN_DATA_AVAILABLE" == false && "$QUEBEC_DATA_AVAILABLE" == false ]]; then
        log_warning "No shapefile data available. Skipping geo data loading."
        log_info "To load geo data later, place shapefiles in the appropriate directories and run:"
        log_info "  docker compose exec backend python manage.py load_geo_data --auto-detect /app/shapefiles/[your_data_directory]/"
    fi
}

# Show final status
show_status() {
    log_header "Setup Complete - Service Status"

    log_info "Service URLs:"
    echo "  🌐 Backend API:      http://localhost:8000"
    echo "  👥 Admin Interface:  http://localhost:8000/admin"
    echo "  📊 Celery Flower:    http://localhost:5555"
    echo "  🔧 Redis Commander:  http://localhost:8081 (admin/admin)"
    echo "  🌍 Frontend:         http://localhost:3000"
    echo "  🔍 Elasticsearch:    http://localhost:9200"
    echo "  🔗 Autocomplete:     http://localhost:4000"

    log_info "Default Admin Credentials:"
    echo "  Username: admin"
    echo "  Password: admin"

    log_info "Checking data status..."

    local country_count=$(docker compose exec backend python manage.py shell -c "
from accounts.models import Country;
print(Country.objects.count())
" 2>/dev/null | tr -d '\r' || echo "0")

    local division_count=$(docker compose exec backend python manage.py shell -c "
from accounts.models import AdministrativeDivision;
print(AdministrativeDivision.objects.count())
" 2>/dev/null | tr -d '\r' || echo "0")

    echo "  Countries loaded: $country_count"
    echo "  Administrative divisions loaded: $division_count"

    log_info "To view container logs:"
    echo "  docker compose logs -f [service_name]"

    log_info "To stop all services:"
    echo "  docker compose down"

    log_success "🎉 Citinfos Backend setup completed successfully!"
}

# Optional cleanup
run_cleanup() {
    log_header "Running Cleanup"

    if [[ -f "./cleanup.sh" ]]; then
        log_info "Running cleanup script..."
        ./cleanup.sh
        if [[ $? -eq 0 ]]; then
            log_success "Cleanup completed successfully"
        else
            log_error "Cleanup failed"
            exit 1
        fi
    else
        log_warning "Cleanup script not found. Performing basic Docker cleanup..."
        docker compose down --remove-orphans || true
        docker system prune -f || true
        log_success "Basic cleanup completed"
    fi

    # Also reset migrations to prevent dependency issues
    log_info "Resetting migrations to prevent dependency issues..."
    if [[ -f "./reset_migrations.sh" ]]; then
        ./reset_migrations.sh --db-only
    else
        log_warning "Migration reset script not found. Removing database volume manually..."
        docker volume rm citinfos_backend_postgis_data || true
    fi
}

# Parse command line arguments
parse_arguments() {
    CLEANUP_FIRST=false
    HELP=false
    START_FROM=""
    LIST_STEPS=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --cleanup|--clean)
                CLEANUP_FIRST=true
                shift
                ;;
            --start-from)
                START_FROM="$2"
                shift 2
                ;;
            --list-steps)
                LIST_STEPS=true
                shift
                ;;
            --help|-h)
                HELP=true
                shift
                ;;
            *)
                log_error "Unknown argument: $1"
                HELP=true
                shift
                ;;
        esac
    done
}

# List available steps
list_steps() {
    echo "Available setup steps:"
    echo ""
    echo "  1. cleanup         - Clean up existing containers and resources"
    echo "  2. build          - Build backend Docker image"
    echo "  3. start          - Start all services"
    echo "  4. migrate        - Run database migrations"
    echo "  5. superuser      - Create admin superuser"
    echo "  6. countries      - Setup countries (Benin, Canada)"
    echo "  7. geodata        - Load geographic data from shapefiles"
    echo "  8. status         - Show final status and URLs"
    echo ""
    echo "Usage examples:"
    echo "  $0 --start-from build     # Start from building backend"
    echo "  $0 --start-from countries # Start from country setup"
    echo "  $0 --start-from geodata   # Start from geo data loading"
    echo ""
}

# Check if we should skip to a specific step
should_run_step() {
    local step_name=$1
    local step_order

    # Define step order
    case $step_name in
        "cleanup") step_order=1 ;;
        "build") step_order=2 ;;
        "start") step_order=3 ;;
        "migrate") step_order=4 ;;
        "superuser") step_order=5 ;;
        "countries") step_order=6 ;;
        "geodata") step_order=7 ;;
        "status") step_order=8 ;;
        *) return 0 ;;  # Unknown step, run it
    esac

    if [[ -z "$START_FROM" ]]; then
        return 0  # No start-from specified, run all steps
    fi

    # Get the order of the start-from step
    local start_order
    case $START_FROM in
        "cleanup") start_order=1 ;;
        "build") start_order=2 ;;
        "start") start_order=3 ;;
        "migrate") start_order=4 ;;
        "superuser") start_order=5 ;;
        "countries") start_order=6 ;;
        "geodata") start_order=7 ;;
        "status") start_order=8 ;;
        *)
            log_error "Invalid step: $START_FROM"
            echo ""
            list_steps
            exit 1
            ;;
    esac

    # Run step if its order is >= start_order
    if [[ $step_order -ge $start_order ]]; then
        return 0  # Run this step
    else
        return 1  # Skip this step
    fi
}

# Show help
show_help() {
    echo "Citinfos Backend Setup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --cleanup, --clean    Run cleanup before setup (removes old containers, images, etc.)"
    echo "  --start-from STEP     Start from a specific step (see --list-steps)"
    echo "  --list-steps          List all available steps"
    echo "  --help, -h           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                        # Normal setup (all steps)"
    echo "  $0 --cleanup              # Clean setup (recommended for fresh start)"
    echo "  $0 --start-from build     # Start from building backend"
    echo "  $0 --start-from countries # Start from country setup"
    echo "  $0 --list-steps           # Show all available steps"
    echo ""
}

# Main execution
main() {
    parse_arguments "$@"

    if [[ "$HELP" == true ]]; then
        show_help
        exit 0
    fi

    if [[ "$LIST_STEPS" == true ]]; then
        list_steps
        exit 0
    fi

    log_header "Citinfos Backend Complete Setup"

    if [[ -n "$START_FROM" ]]; then
        log_info "Starting from step: $START_FROM"
        echo ""
    fi

    # Run cleanup first if requested
    if [[ "$CLEANUP_FIRST" == true ]]; then
        run_cleanup
    fi

    # Check prerequisites (always run these for safety)
    check_docker
    check_files
    check_shapefiles

    # Setup process with step checking
    if should_run_step "cleanup"; then
        cleanup_existing
    else
        log_info "Skipping cleanup step"
    fi

    if should_run_step "build"; then
        build_backend
    else
        log_info "Skipping build step"
    fi

    if should_run_step "start"; then
        start_services
    else
        log_info "Skipping service start step"
    fi

    if should_run_step "migrate"; then
        run_migrations
    else
        log_info "Skipping migration step"
    fi

    if should_run_step "superuser"; then
        create_superuser
    else
        log_info "Skipping superuser creation step"
    fi

    if should_run_step "countries"; then
        setup_countries
    else
        log_info "Skipping country setup step"
    fi

    if should_run_step "geodata"; then
        load_geo_data
    else
        log_info "Skipping geo data loading step"
    fi

    if should_run_step "status"; then
        show_status
    else
        log_info "Skipping status display step"
    fi
}

# Handle script interruption
trap 'log_error "Setup interrupted"; exit 1' INT TERM

# Run main function
main "$@"