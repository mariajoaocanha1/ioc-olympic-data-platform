from pathlib import Path
import pandas as pd
from loguru import logger


def read_csv(path: Path, **kwargs: object) -> pd.DataFrame:
    logger.info(f"Reading CSV: {path}")
    df: pd.DataFrame = pd.read_csv(path, **kwargs)  # type: ignore[call-overload]
    logger.info(f"Loaded {len(df):,} rows from {path.name}")
    return df


def read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        logger.warning(f"Parquet not found: {path} — returning empty DataFrame")
        return pd.DataFrame()
    df = pd.read_parquet(path, engine="pyarrow")
    logger.info(f"Read {len(df):,} rows from {path.name}")
    return df


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow")
    logger.info(f"Wrote {len(df):,} rows to {path.name}")