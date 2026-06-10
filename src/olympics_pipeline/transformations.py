"""
transformations.py
------------------
Medallion architecture transformation logic.

Orchestrates the three-layer pipeline:
  Bronze  — raw data ingested as-is from source files.
  Silver  — cleansed, typed, and validated data.
  Gold    — dimensional model (star schema) ready for analytics.
"""
from datetime import datetime
from typing import Optional
import pandas as pd
from loguru import logger

from src.olympics_pipeline.scd import apply_scd2


def build_bronze(
    raw_events: pd.DataFrame,
    raw_noc: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ingest raw source data into the Bronze layer without any transformation.

    The Bronze layer preserves the original data exactly as received,
    acting as an immutable audit trail of every ingestion run.

    Args:
        raw_events: Raw DataFrame from athlete_events.csv.
        raw_noc: Raw DataFrame from noc_regions.csv.

    Returns:
        Tuple of (bronze_events, bronze_noc) as unmodified copies.
    """
    logger.info("Building bronze layer...")
    return raw_events.copy(), raw_noc.copy()


def build_silver(
    bronze_events: pd.DataFrame,
    bronze_noc: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cleanse and standardise Bronze data into the Silver layer.

    Applies the following transformations:
      - Fills missing medals with the string "None" for consistency.
      - Coerces Age, Height, and Weight to numeric, setting invalid
        values to NaN rather than raising errors.
      - Strips leading/trailing whitespace from athlete names.
      - Normalises NOC codes to uppercase for consistent joining.

    Args:
        bronze_events: Raw athlete events from the Bronze layer.
        bronze_noc: Raw NOC regions from the Bronze layer.

    Returns:
        Tuple of (silver_events, silver_noc) — cleansed DataFrames.
    """
    logger.info("Building silver layer...")

    events = bronze_events.copy()
    events["Medal"] = events["Medal"].fillna("None")
    events["Age"] = pd.to_numeric(events["Age"], errors="coerce")
    events["Height"] = pd.to_numeric(events["Height"], errors="coerce")
    events["Weight"] = pd.to_numeric(events["Weight"], errors="coerce")
    events["Name"] = events["Name"].str.strip()
    events["NOC"] = events["NOC"].str.strip().str.upper()

    noc = bronze_noc.copy()
    noc["NOC"] = noc["NOC"].str.strip().str.upper()

    return events, noc


def build_dim_athlete(
    silver: pd.DataFrame,
    existing: pd.DataFrame,
    as_of: datetime,
) -> pd.DataFrame:
    """Build or incrementally update DIM_ATHLETE using SCD Type 2.

    Deduplicates athletes by ID, keeping the most recent record per
    athlete (sorted by Year descending). Physical attributes
    height_cm and weight_kg are tracked as SCD Type 2 — a change
    in either creates a new dimension record and expires the old one,
    preserving the full history of an athlete's physical profile.

    Name and sex are treated as SCD Type 1 (overwrite in place),
    as corrections to these fields are not considered historical events.

    Args:
        silver: Cleansed athlete events from the Silver layer.
        existing: Current state of DIM_ATHLETE (empty on first run).
        as_of: Effective datetime for this batch run.

    Returns:
        Updated DIM_ATHLETE DataFrame with SCD2 applied.
    """
    logger.info("Building dim_athlete...")
    snap = (
        silver
        .sort_values("Year", ascending=False)
        .drop_duplicates(subset=["ID"], keep="first")
        [["ID", "Name", "Sex", "Height", "Weight"]]
        .rename(columns={
            "ID": "athlete_nk",
            "Name": "name",
            "Sex": "sex",
            "Height": "height_cm",
            "Weight": "weight_kg",
        })
        .reset_index(drop=True)
    )
    return apply_scd2(
        existing=existing,
        incoming=snap,
        natural_key="athlete_nk",
        tracked_cols=["height_cm", "weight_kg"],
        surrogate_key="athlete_sk",
        as_of=as_of,
    )


def build_dim_event(
    silver: pd.DataFrame,
    existing: pd.DataFrame,
    as_of: datetime,
) -> pd.DataFrame:
    """Build or incrementally update DIM_EVENT using SCD Type 2.

    Deduplicates sport/event combinations from the Silver layer.
    The natural key is a composite of sport and event name.
    Both sport and event_name are tracked as SCD Type 2, since
    Olympic event categories and sport classifications have changed
    significantly across 120 years of Games.

    Args:
        silver: Cleansed athlete events from the Silver layer.
        existing: Current state of DIM_EVENT (empty on first run).
        as_of: Effective datetime for this batch run.

    Returns:
        Updated DIM_EVENT DataFrame with SCD2 applied.
    """
    logger.info("Building dim_event...")
    snap = (
        silver
        .drop_duplicates(subset=["Sport", "Event"])
        [["Sport", "Event"]]
        .rename(columns={"Sport": "sport", "Event": "event_name"})
        .reset_index(drop=True)
    )
    snap["event_nk"] = snap["sport"] + "__" + snap["event_name"]
    return apply_scd2(
        existing=existing,
        incoming=snap,
        natural_key="event_nk",
        tracked_cols=["sport", "event_name"],
        surrogate_key="event_sk",
        as_of=as_of,
    )


def build_dim_noc(
    silver_noc: pd.DataFrame,
    existing: pd.DataFrame,
    as_of: datetime,
) -> pd.DataFrame:
    """Build or incrementally update DIM_NOC using SCD Type 2.

    The region column is tracked as SCD Type 2, reflecting the
    real-world reality that countries have been renamed, unified,
    or dissolved over the 120-year history of the Olympics
    (e.g. USSR -> Russia, Yugoslavia -> multiple nations).

    Notes is treated as SCD Type 1 (overwrite), as it holds
    administrative annotations with no historical significance.

    Args:
        silver_noc: Cleansed NOC regions from the Silver layer.
        existing: Current state of DIM_NOC (empty on first run).
        as_of: Effective datetime for this batch run.

    Returns:
        Updated DIM_NOC DataFrame with SCD2 applied.
    """
    logger.info("Building dim_noc...")
    snap = (
        silver_noc
        .rename(columns={
            "NOC": "noc_code",
            "region": "region",
            "notes": "notes",
        })
        .reset_index(drop=True)
    )
    return apply_scd2(
        existing=existing,
        incoming=snap,
        natural_key="noc_code",
        tracked_cols=["region"],
        surrogate_key="noc_sk",
        as_of=as_of,
    )


def build_dim_date(silver: pd.DataFrame) -> pd.DataFrame:
    """Build DIM_DATE as a static SCD Type 0 dimension.

    Olympic year and season combinations are immutable historical
    facts — they never change once an edition has taken place.
    For this reason, DIM_DATE uses SCD Type 0 (fixed), meaning
    records are inserted once and never updated or versioned.

    Args:
        silver: Cleansed athlete events from the Silver layer.

    Returns:
        DIM_DATE DataFrame with one row per Olympic edition.
    """
    logger.info("Building dim_date (SCD Type 0 — immutable)...")
    dates = (
        silver
        .drop_duplicates(subset=["Year", "Season"])
        [["Year", "Season", "Games"]]
        .rename(columns={
            "Year": "year",
            "Season": "season",
            "Games": "games_edition",
        })
        .sort_values(["year", "season"])
        .reset_index(drop=True)
    )
    dates["date_sk"] = range(1, len(dates) + 1)
    return dates


def build_fact_result(
    silver: pd.DataFrame,
    dim_athlete: pd.DataFrame,
    dim_event: pd.DataFrame,
    dim_noc: pd.DataFrame,
    dim_date: pd.DataFrame,
) -> pd.DataFrame:
    """Build FACT_RESULT — the central fact table of the star schema.

    Produces one row per athlete participation in an Olympic event,
    resolving all dimension natural keys to their current surrogate
    keys. Rows where any surrogate key lookup fails (orphan records)
    are silently skipped to maintain referential integrity.

    The grain of this fact table is:
      one athlete x one event x one Olympic edition.

    Args:
        silver: Cleansed athlete events from the Silver layer.
        dim_athlete: Current DIM_ATHLETE with surrogate keys.
        dim_event: Current DIM_EVENT with surrogate keys.
        dim_noc: Current DIM_NOC with surrogate keys.
        dim_date: Current DIM_DATE with surrogate keys.

    Returns:
        FACT_RESULT DataFrame ready for analytical queries.
    """
    logger.info("Building fact_result...")

    athlete_map: dict[int, int] = (
        dim_athlete[dim_athlete["is_current"]]
        .set_index("athlete_nk")["athlete_sk"]
        .to_dict()
    )
    event_dim = dim_event[dim_event["is_current"]].copy()
    event_dim["event_nk"] = event_dim["sport"] + "__" + event_dim["event_name"]
    event_map: dict[str, int] = (
        event_dim.set_index("event_nk")["event_sk"].to_dict()
    )
    noc_map: dict[str, int] = (
        dim_noc[dim_noc["is_current"]]
        .set_index("noc_code")["noc_sk"]
        .to_dict()
    )
    date_map: dict[str, int] = (
        dim_date
        .assign(nk=dim_date["year"].astype(str) + "_" + dim_date["season"])
        .set_index("nk")["date_sk"]
        .to_dict()
    )

    rows: list[dict[str, object]] = []
    for i, (_, row) in enumerate(silver.iterrows()):
        event_nk = str(row["Sport"]) + "__" + str(row["Event"])
        date_nk = str(int(row["Year"])) + "_" + str(row["Season"])
        a_sk = athlete_map.get(int(row["ID"]))
        e_sk = event_map.get(event_nk)
        n_sk = noc_map.get(str(row["NOC"]))
        d_sk = date_map.get(date_nk)
        if None in (a_sk, e_sk, n_sk, d_sk):
            continue
        rows.append({
            "result_sk": i,
            "athlete_sk": int(a_sk),  # type: ignore[arg-type]
            "event_sk": int(e_sk),  # type: ignore[arg-type]
            "noc_sk": int(n_sk),  # type: ignore[arg-type]
            "date_sk": int(d_sk),  # type: ignore[arg-type]
            "medal": str(row["Medal"]),
            "age_at_event": float(row["Age"]) if pd.notna(row["Age"]) else None,
            "year": int(row["Year"]),
            "season": str(row["Season"]),
        })

    logger.info(f"Fact table: {len(rows):,} rows.")
    return pd.DataFrame(rows)