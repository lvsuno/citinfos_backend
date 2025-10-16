#!/usr/bin/env bash
# Helper script to create admin during backend image build.
# Expects the following env vars to be set at build/run time:
# - CREATE_SUPERUSER_ON_BUILD=true
# - DJANGO_SUPERUSER_USERNAME
# - DJANGO_SUPERUSER_EMAIL
# - DJANGO_SUPERUSER_PASSWORD
# - DJANGO_SUPERUSER_FORCE_RESET (optional)

set -euo pipefail

if [ "${CREATE_SUPERUSER_ON_BUILD:-}" != "1" ] && [ "${CREATE_SUPERUSER_ON_BUILD:-}" != "true" ] && [ "${CREATE_SUPERUSER_ON_BUILD:-}" != "yes" ]; then
  echo "CREATE_SUPERUSER_ON_BUILD not enabled; skipping admin creation."
  exit 0
fi

# Run migrations to ensure auth tables exist
python manage.py migrate --noinput

# Run the custom management command to create admin from env
python manage.py create_admin_from_env

exit 0
