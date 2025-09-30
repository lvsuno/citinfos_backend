#!/bin/bash

# Cleanup Script for Citinfos Backend
# Removes unused commands and Docker resources for fresh setup

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

# Clean up unused management commands
cleanup_commands() {
    log_header "Cleaning Up Unused Management Commands"

    # Commands to keep (essential for production)
    local keep_commands=(
        "load_geo_data.py"
        "setup_country.py"
        "generate_field_mappings.py"
        "load_initial_data.py"
        "test_announcements.py"
    )

    # Commands to remove (development/testing only)
    local remove_commands=(
        "add_point_geometries.py"
        "analyze_hierarchy.py"
        "analyze_shapefiles.py"
        "auto_import_shapefiles.py"
        "batch_import_shapefiles.py"
        "fix_shapefile.py"
        "generate_boundaries.py"
        "generate_field_mapping.py"
        "import_cities.py"
        "import_shapefile.py"
        "import_shapefile_with_auto_parent.py"
        "populate_countries.py"
    )

    log_info "Commands to keep:"
    for cmd in "${keep_commands[@]}"; do
        if [[ -f "core/management/commands/$cmd" ]]; then
            echo "  ✅ $cmd"
        else
            echo "  ❌ $cmd (missing)"
        fi
    done

    log_info "Commands to remove:"
    for cmd in "${remove_commands[@]}"; do
        if [[ -f "core/management/commands/$cmd" ]]; then
            log_warning "Removing obsolete command: $cmd"
            rm -f "core/management/commands/$cmd"
            echo "  🗑️  $cmd (removed)"
        else
            echo "  ➖ $cmd (not found)"
        fi
    done

    # Clean up __pycache__ directories
    log_info "Cleaning Python cache files..."
    find core/management/commands/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true

    log_success "Command cleanup completed"
}

# Clean up unused files
cleanup_files() {
    log_header "Cleaning Up Unused Project Files"

    # Files to potentially clean up (check if they exist first)
    local files_to_check=(
        "update_admin_division_types.py"
        "scripts/load_initial_shapefiles.sh"
    )

    for file in "${files_to_check[@]}"; do
        if [[ -f "$file" ]]; then
            log_warning "Found potentially unused file: $file"
            read -p "Remove this file? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -f "$file"
                log_success "Removed: $file"
            else
                log_info "Kept: $file"
            fi
        fi
    done
}

# Stop and clean Docker resources
cleanup_docker() {
    log_header "Cleaning Docker Resources"

    log_info "Stopping all containers..."
    docker compose down --remove-orphans || true

    log_info "Removing unused Docker images..."
    docker image prune -f || true

    log_info "Removing unused Docker volumes..."
    docker volume prune -f || true

    log_info "Removing unused Docker networks..."
    docker network prune -f || true

    log_info "Removing build cache..."
    docker builder prune -f || true

    # More aggressive cleanup if requested
    read -p "Perform aggressive Docker cleanup (removes all unused containers/images)? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Performing aggressive Docker cleanup..."
        docker system prune -a -f --volumes || true
        log_success "Aggressive cleanup completed"
    fi

    log_success "Docker cleanup completed"
}

# Clean up migration files (optional)
cleanup_migrations() {
    log_header "Migration Cleanup (Optional)"

    log_info "Current migration files:"
    find . -path "*/migrations/*.py" -not -name "__init__.py" | sort

    read -p "Reset all migrations? This will delete all migration files! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Removing all migration files..."
        find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
        log_warning "Removing migration cache..."
        find . -path "*/migrations/__pycache__" -exec rm -rf {} + 2>/dev/null || true
        log_success "Migration files removed"
        log_info "You'll need to run 'makemigrations' after setup"
    else
        log_info "Migration files kept"
    fi
}

# Show cleanup summary
show_summary() {
    log_header "Cleanup Summary"

    log_info "✅ Cleaned up unused management commands"
    log_info "✅ Cleaned up Docker resources"
    log_info "✅ Removed cache files"

    log_success "System is ready for fresh setup!"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./setup.sh (complete setup)"
    echo "  2. Or run: ./quickstart.sh (minimal setup)"
    echo ""
}

# Main execution
main() {
    log_header "Citinfos Backend Cleanup"

    # Check if we're in the right directory
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "Please run this script from the project root directory"
        exit 1
    fi

    cleanup_commands
    cleanup_files
    cleanup_docker
    cleanup_migrations
    show_summary
}

# Handle script interruption
trap 'log_error "Cleanup interrupted"; exit 1' INT TERM

# Run main function
main "$@"