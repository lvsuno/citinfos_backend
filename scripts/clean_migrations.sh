#!/usr/bin/env bash
# Script moved to scripts/ so it can be run from the scripts folder reliably.
# Usage: ./scripts/clean_migrations.sh

set -euo pipefail

# Determine repo root (one level up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="${SCRIPT_DIR%/*}"
cd "$REPO_ROOT"

# List all app directories (edit this list if you have custom app locations)
APPS="accounts content core equipment messaging notifications polls search analytics ai_conversations communities"

for app in $APPS; do
  if [ -d "$app/migrations" ]; then
    echo "Cleaning migrations in $app/migrations"
    find "$app/migrations" -type f ! -name '__init__.py' -delete
  fi
done

find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

echo "All migration files (except __init__.py) deleted."

# Helpful reminders (commented out) for next steps
# echo "Now run:"
# echo "  python manage.py makemigrations"
# echo "  python manage.py migrate"

exit 0
