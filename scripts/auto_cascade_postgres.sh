#!/bin/bash
# This script will automatically update all non-CASCADE foreign key constraints to ON DELETE CASCADE in your PostgreSQL database.
# Usage: ./auto_cascade_postgres.sh <db_name> <db_user> <db_host>

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DB_NAME=${1:-loc_database}
DB_USER=${2:-loc_user}
DB_HOST=${3:-postgis}

echo "Generating ALTER statements for non-CASCADE foreign keys..."

# Use psql to execute the SQL and generate ALTER statements
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -A -f "$SCRIPT_DIR/ensure_postgres_cascade_constraints.sql" > alter_fks.sql

if [ ! -s alter_fks.sql ]; then
  echo "No non-CASCADE foreign keys found. All constraints are correct."
  rm -f alter_fks.sql
  exit 0
fi

echo "Applying ALTER statements to enforce ON DELETE CASCADE..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f alter_fks.sql

rm -f alter_fks.sql

echo "All applicable foreign key constraints are now ON DELETE CASCADE."