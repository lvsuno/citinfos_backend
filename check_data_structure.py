#!/usr/bin/env python3
"""
Test script to check if the administrative data folders and files exist
before running the main import script.
"""

import os
from pathlib import Path

def check_data_structure():
    """Check if the expected folder structure exists"""
    base_path = Path("/app/shapefiles")

    print("🔍 CHECKING DATA FOLDER STRUCTURE")
    print("=" * 40)

    # Expected files for each country
    expected_files = {
        "benin": [
            "ben_admbnda_adm1_1m_salb_20190816.shp",
            "ben_admbnda_adm2_1m_salb_20190816_fixed.shp",
            "ben_admbnda_adm3_1m_salb_20190816_corrected.shp"
        ],
        "quebec": [
            "QUEBEC_region_s.shp",
            "QUEBEC_mrc_s.shp",
            "QUEBEC_munic_s.shp",
            "QUEBEC_arron_s.shp"
        ]
    }

    all_good = True

    for country, files in expected_files.items():
        country_path = base_path / country
        print(f"\n📁 {country.upper()} folder: {country_path}")

        if not country_path.exists():
            print(f"❌ Folder not found!")
            all_good = False
            continue

        print(f"✅ Folder exists")

        # Check each file
        for filename in files:
            filepath = country_path / filename
            if filepath.exists():
                print(f"  ✅ {filename}")
            else:
                print(f"  ❌ {filename} - NOT FOUND")
                all_good = False

    print(f"\n{'🎉 ALL FILES FOUND - READY TO IMPORT!' if all_good else '⚠️ SOME FILES MISSING - CHECK PATHS'}")
    return all_good

if __name__ == "__main__":
    check_data_structure()