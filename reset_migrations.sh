#!/bin/bash

# Migration Reset Script for Citinfos Backend
# Fixes Django migration dependency issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Reset migrations
reset_migrations() {
    log_header "Resetting Migration Files"

    log_warning "This will delete all migration files and reset to initial state!"
    read -p "Continue? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Migration reset cancelled"
        exit 0
    fi

    log_info "Removing migration files..."
    find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
    find . -path "*/migrations/__pycache__" -exec rm -rf {} + 2>/dev/null || true

    log_success "Migration files removed"
}

# Reset database
reset_database() {
    log_header "Resetting Database"

    log_info "Stopping containers..."
    docker compose down || true

    log_info "Removing database volume..."
    docker volume rm citinfos_backend_postgis_data || true

    log_success "Database reset complete"
}

# Create fresh migrations
create_migrations() {
    log_header "Creating Fresh Migrations"

    # Start only the database for migration creation
    log_info "Starting database..."
    docker compose up -d postgis

    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10

    # Build backend if needed
    log_info "Building backend..."
    docker compose build backend

    # Start backend temporarily for migrations
    log_info "Starting backend..."
    docker compose up -d backend

    # Wait for backend to be ready
    sleep 15

    # Create migrations
    log_info "Creating initial migrations..."
    docker compose exec backend python manage.py makemigrations

    # Apply migrations
    log_info "Applying migrations..."
    docker compose exec backend python manage.py migrate

    log_success "Fresh migrations created and applied"
}

# Show help
show_help() {
    echo "Migration Reset Tool"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --files-only     Reset migration files only (keep database)"
    echo "  --db-only       Reset database only (keep migration files)"
    echo "  --full          Reset both migration files and database (default)"
    echo "  --help, -h      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0               # Full reset (migrations + database)"
    echo "  $0 --files-only  # Reset migration files only"
    echo "  $0 --db-only     # Reset database volume only"
    echo ""
}

# Parse arguments
parse_arguments() {
    FILES_ONLY=false
    DB_ONLY=false
    FULL_RESET=true
    HELP=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --files-only)
                FILES_ONLY=true
                FULL_RESET=false
                shift
                ;;
            --db-only)
                DB_ONLY=true
                FULL_RESET=false
                shift
                ;;
            --full)
                FULL_RESET=true
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

# Main execution
main() {
    parse_arguments "$@"

    if [[ "$HELP" == true ]]; then
        show_help
        exit 0
    fi

    log_header "Django Migration Reset Tool"

    # Check if we're in the right directory
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "Please run this script from the project root directory"
        exit 1
    fi

    if [[ "$FULL_RESET" == true ]]; then
        log_info "Performing full reset (migrations + database)..."
        reset_migrations
        reset_database
        create_migrations
    elif [[ "$FILES_ONLY" == true ]]; then
        log_info "Resetting migration files only..."
        reset_migrations
    elif [[ "$DB_ONLY" == true ]]; then
        log_info "Resetting database only..."
        reset_database
    fi

    log_success "Migration reset completed!"
    echo ""
    echo "Next steps:"
    echo "  - Run: ./setup.sh (to complete setup)"
    echo "  - Or run: docker compose up -d (to start services)"
    echo ""
}

# Handle script interruption
trap 'log_error "Reset interrupted"; exit 1' INT TERM

# Run main function
main "$@"