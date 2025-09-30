#!/bin/bash

# List all app directories (edit this list if you have custom app locations)
APPS="accounts content core messaging notifications polls search analytics ai_conversations communities"

for app in $APPS; do
  if [ -d "$app/migrations" ]; then
    echo "Cleaning migrations in $app/migrations"
    find "$app/migrations" -type f ! -name '__init__.py' -delete
  fi
done

find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

echo "All migration files (except __init__.py) deleted."

# DB_NAME="citinfos_backend"
# DB_USER="loc_user"
# DB_HOST="localhost"

# echo -n "Enter password for new MySQL user 'loc_user': "
# read -s DB_PASS
# echo ""

# echo "Dropping database $DB_NAME..."
# mysql -u"$DB_USER" -p"$DB_PASS" -h "$DB_HOST" -e "DROP DATABASE IF EXISTS \`$DB_NAME\`;"

# echo "Creating database $DB_NAME..."
# mysql -u"$DB_USER" -p"$DB_PASS" -h "$DB_HOST" -e "CREATE DATABASE \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# echo "Done."

# echo "Now run:"
# echo "  python manage.py makemigrations"
# echo "  python manage.py migrate"

# python manage.py makemigrations
# python manage.py migrate


# # DB_NAME=${1:-citinfos_backend}
# # DB_USER=${2:-loc_user}
# # DB_HOST=${3:-localhost}

# read -s -p "Enter MySQL password for user $DB_USER: " DB_PASS
# echo

# echo "Generating ALTER statements for non-CASCADE foreign keys..."

# mysql -u"$DB_USER" -p"$DB_PASS" -h "$DB_HOST" "$DB_NAME" --batch --skip-column-names < ensure_mysql_cascade_constraints.sql > alter_fks.sql

# if [ ! -s alter_fks.sql ]; then
#   echo "No non-CASCADE foreign keys found. All constraints are correct."
#   rm -f alter_fks.sql
#   exit 0
# fi

# echo "Applying ALTER statements to enforce ON DELETE CASCADE..."
# mysql -u"$DB_USER" -p"$DB_PASS" -h "$DB_HOST" "$DB_NAME" < alter_fks.sql

# rm -f alter_fks.sql

# echo "All applicable foreign key constraints are now ON DELETE CASCADE."
