#!/usr/bin/env python
"""
Script to populate phone_code, flag_emoji, and region fields for existing
Country records.

This script uses the centralized country_data.py lookup table with 223 countries.

Run this script with:
    docker compose exec backend python populate_country_phone_data.py

Or via Django shell:
    docker compose exec backend python manage.py shell < populate_country_phone_data.py
"""

import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from core.models import Country
from core.country_data import get_country_info


def populate_country_phone_data():
    """
    Populate phone data for all existing countries in the database.
    Uses the country_data.py lookup table.
    """
    print("Starting country phone data population...")
    print("-" * 60)

    countries = Country.objects.all()
    total_countries = countries.count()
    updated_count = 0
    missing_count = 0

    print(f"Found {total_countries} countries in database\n")

    for country in countries:
        iso3 = country.iso3
        info = get_country_info(iso3)

        if info:
            # Update the country with phone data
            country.phone_code = info['phone_code']
            country.flag_emoji = info['flag_emoji']
            country.region = info['region']
            country.save()

            updated_count += 1
            print(
                f"✓ Updated {country.name} ({iso3}): "
                f"{info['flag_emoji']} {info['phone_code']} - {info['region']}"
            )
        else:
            missing_count += 1
            print(
                f"✗ No data found for {country.name} ({iso3}) - "
                "please add to country_data.py"
            )

    print("\n" + "-" * 60)
    print("Population complete!")
    print(f"Updated: {updated_count} countries")
    print(f"Missing: {missing_count} countries")
    print("-" * 60)

    return updated_count, missing_count


if __name__ == '__main__':
    try:
        updated, missing = populate_country_phone_data()
        sys.exit(0 if missing == 0 else 1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
