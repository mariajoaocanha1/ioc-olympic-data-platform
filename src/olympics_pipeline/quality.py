"""
quality.py
----------
Data quality validation gates for the pipeline.

Applied at the Bronze - Silver transition to ensure that only clean, well-formed records progress to the analytical layers.

Invalid rows are dropped and logged as warnings so that data issues are visible without stopping the pipeline.

Functions:
    validate_athlete_events: Validates the main events dataset
    validate_noc_regions: Validates the NOC/country dataset
"""

import pandas as pd
from loguru import logger


def validate_athlete_events(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and filter the athlete events dataset.

    Applies three quality rules:
      1. Drops rows with NULL values in required columns
         (ID, Name, NOC, Year, Season, Sport, Event).
      2. Drops rows with a Year value before 1800
         (data integrity check — Olympics started in 1896).
      3. Drops rows with invalid Sex values
         (only M and F are accepted).

    Args:
        df: Raw athlete events DataFrame from Bronze layer.

    Returns:
        Validated DataFrame with invalid rows removed.
    """
    initial = len(df)
    df = df.dropna(subset=["ID", "Name", "NOC", "Year", "Season", "Sport", "Event"])
    df = df[df["Year"] > 1800]
    df = df[df["Sex"].isin(["M", "F"])]
    dropped = initial - len(df)
    if dropped > 0:
        logger.warning(f"Quality check: dropped {dropped:,} invalid rows")
    logger.info(f"Quality check passed: {len(df):,} rows remaining")
    return df.reset_index(drop=True)


def validate_noc_regions(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and filter the NOC regions dataset.

    Applies two quality rules:
      1. Drops rows with a NULL NOC code (unusable without a key).
      2. Removes duplicate NOC codes (keeps first occurrence).

    Args:
        df: Raw NOC regions DataFrame from Bronze layer.

    Returns:
        Validated DataFrame: One row per unique NOC code.
    """
    df = df.dropna(subset=["NOC"])
    df = df.drop_duplicates(subset=["NOC"])
    logger.info(f"NOC regions validated: {len(df):,} rows")
    return df.reset_index(drop=True)