#!/bin/bash
# This script will automatically update all non-CASCADE foreign key constraints to ON DELETE CASCADE in your MySQL database.
# Usage: ./auto_cascade_mysql.sh <db_name> <db_user> <db_host>
# It will prompt for the password securely.

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DB_NAME=${1:-citinfos_backend}
DB_USER=${2:-loc_user}
DB_HOST=${3:-db}




echo "Generating ALTER statements for non-CASCADE foreign keys..."

mysql -u"$DB_USER" -p"$MYSQL_PASSWORD" -h "$DB_HOST" "$DB_NAME" --batch --skip-column-names < "$SCRIPT_DIR/ensure_mysql_cascade_constraints.sql" > alter_fks.sql


if [ ! -s alter_fks.sql ]; then
  echo "No non-CASCADE foreign keys found. All constraints are correct."
  rm -f alter_fks.sql
  exit 0
fi


echo "Applying ALTER statements to enforce ON DELETE CASCADE..."
mysql -u"$DB_USER" -p"$MYSQL_PASSWORD" -h "$DB_HOST" "$DB_NAME" < alter_fks.sql

rm -f alter_fks.sql

echo "All applicable foreign key constraints are now ON DELETE CASCADE."
