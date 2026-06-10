from pathlib import Path

ROOT_DIR: Path = Path(__file__).resolve().parents[2]

RAW_DIR: Path = ROOT_DIR / "data" / "raw"
BRONZE_DIR: Path = ROOT_DIR / "data" / "bronze"
SILVER_DIR: Path = ROOT_DIR / "data" / "silver"
GOLD_DIR: Path = ROOT_DIR / "data" / "gold"

ATHLETE_EVENTS_FILE: str = "athlete_events.csv"
NOC_REGIONS_FILE: str = "noc_regions.csv"

for _dir in [BRONZE_DIR, SILVER_DIR, GOLD_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)