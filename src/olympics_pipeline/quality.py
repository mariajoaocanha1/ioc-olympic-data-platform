import pandas as pd
from loguru import logger


def validate_athlete_events(df: pd.DataFrame) -> pd.DataFrame:
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
    df = df.dropna(subset=["NOC"])
    df = df.drop_duplicates(subset=["NOC"])
    logger.info(f"NOC regions validated: {len(df):,} rows")
    return df.reset_index(drop=True)