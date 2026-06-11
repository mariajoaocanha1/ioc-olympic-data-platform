"""
config.py
---------
Central configuration for the pipeline.

Defines all file system paths and source file names used across
the pipeline. Importing from this module ensures that paths are
consistent and only need to change in one place.

Also ensures that the Bronze, Silver and Gold output directories
exist before the pipeline attempts to write to them.
"""

from pathlib import Path

# Resolves the project root regardless of where the script is run from.
# Path(__file__): This file's location (src/olympics_pipeline/config.py)
# .parents[2]: Go up 2 levels (project root)
ROOT_DIR: Path = Path(__file__).resolve().parents[2]

RAW_DIR: Path = ROOT_DIR / "data" / "raw"
BRONZE_DIR: Path = ROOT_DIR / "data" / "bronze"
SILVER_DIR: Path = ROOT_DIR / "data" / "silver"
GOLD_DIR: Path = ROOT_DIR / "data" / "gold"

ATHLETE_EVENTS_FILE: str = "athlete_events.csv"
NOC_REGIONS_FILE: str = "noc_regions.csv"

# Create output directories if they don't exist yet.
# parents=True  — create intermediate folders if needed.
# exist_ok=True — don't raise an error if folder already exists
for _dir in [BRONZE_DIR, SILVER_DIR, GOLD_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)
