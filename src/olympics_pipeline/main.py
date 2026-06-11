"""
main.py
-------
IOC Olympic Data Platform — Batch Pipeline entrypoint.

Orchestrates the full Bronze -> Silver -> Gold medallion pipeline:

  1. Extract: Reads raw CSV files from data/raw/
  2. Quality: Validates and filters invalid records
  3. Bronze: Persists raw data as Parquet (immutable audit trail)
  4. Silver: Cleanses and standardises data
  5. Gold: Builds star schema dimensions (with SCD logic)
           and fact table, persisted as Parquet files

Architecture note:

  This implementation simulates a production lakehouse architecture
  locally using pandas and Parquet files, maintaining the same
  Bronze, Silver, Gold logical separation that would apply at scale.

  The business logic is execution-engine agnostic, it can run
  unchanged on a distributed platform without modifications to
  the transformation or SCD logic.

Usage:
    python -m src.olympics_pipeline.main
    make run
"""

from datetime import datetime

from loguru import logger

from src.olympics_pipeline.config import (
    ATHLETE_EVENTS_FILE,
    BRONZE_DIR,
    GOLD_DIR,
    NOC_REGIONS_FILE,
    RAW_DIR,
    SILVER_DIR,
)
from src.olympics_pipeline.io import read_csv, read_parquet, write_parquet
from src.olympics_pipeline.quality import (
    validate_athlete_events,
    validate_noc_regions,
)
from src.olympics_pipeline.transformations import (
    build_bronze,
    build_dim_athlete,
    build_dim_date,
    build_dim_event,
    build_dim_noc,
    build_fact_result,
    build_silver,
)


def run(as_of: datetime | None = None) -> None:
    """Execute the full batch pipeline for one run.

    Reads from data/raw/, applies medallion transformations,
    and writes Parquet files to data/bronze/, data/silver/,
    and data/gold/.

    Args:
        as_of: Effective datetime for SCD2 versioning.
               Defaults to current UTC time if not provided.
    """
    batch_time: datetime = as_of or datetime.utcnow()
    logger.info(f"Pipeline started — {batch_time.isoformat()}")

    # --- 1. Extract --------------------------------------------------------
    raw_events = read_csv(RAW_DIR / ATHLETE_EVENTS_FILE)
    raw_noc = read_csv(RAW_DIR / NOC_REGIONS_FILE)

    # ---  2. Quality gates  ------------------------------------------------
    raw_events = validate_athlete_events(raw_events)
    raw_noc = validate_noc_regions(raw_noc)

    # --- 3. Bronze  --------------------------------------------------------
    bronze_events, bronze_noc = build_bronze(raw_events, raw_noc)
    write_parquet(bronze_events, BRONZE_DIR / "athlete_events.parquet")
    write_parquet(bronze_noc, BRONZE_DIR / "noc_regions.parquet")

    # --- 4. Silver  --------------------------------------------------------
    silver_events, silver_noc = build_silver(bronze_events, bronze_noc)
    write_parquet(silver_events, SILVER_DIR / "athlete_events.parquet")
    write_parquet(silver_noc, SILVER_DIR / "noc_regions.parquet")

    # --- 5. Gold — Dimensions (load existing state for SCD2 incremental) ---
    existing_athlete = read_parquet(GOLD_DIR / "dim_athlete.parquet")
    existing_event = read_parquet(GOLD_DIR / "dim_event.parquet")
    existing_noc = read_parquet(GOLD_DIR / "dim_noc.parquet")

    dim_athlete = build_dim_athlete(silver_events, existing_athlete, batch_time)
    dim_event = build_dim_event(silver_events, existing_event, batch_time)
    dim_noc = build_dim_noc(silver_noc, existing_noc, batch_time)
    dim_date = build_dim_date(silver_events)

    write_parquet(dim_athlete, GOLD_DIR / "dim_athlete.parquet")
    write_parquet(dim_event, GOLD_DIR / "dim_event.parquet")
    write_parquet(dim_noc, GOLD_DIR / "dim_noc.parquet")
    write_parquet(dim_date, GOLD_DIR / "dim_date.parquet")

    # ---  6. Gold — Fact table  -----------------------------------------------
    fact = build_fact_result(
        silver_events, dim_athlete, dim_event, dim_noc, dim_date
    )
    write_parquet(fact, GOLD_DIR / "fact_result.parquet")

    # ---  Summary  -------------------------------------------------------------
    logger.success("Pipeline completed successfully.")
    logger.info(f"  dim_athlete : {len(dim_athlete):,} rows")
    logger.info(f"  dim_event   : {len(dim_event):,} rows")
    logger.info(f"  dim_noc     : {len(dim_noc):,} rows")
    logger.info(f"  dim_date    : {len(dim_date):,} rows")
    logger.info(f"  fact_result : {len(fact):,} rows")


if __name__ == "__main__":
    run()
