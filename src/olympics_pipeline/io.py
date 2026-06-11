"""
io.py
-----
Input/Output utilities for the pipeline.

Centralises all file read and write operations so that the rest
of the pipeline never interacts with the file system directly.
If the storage format changes (e.g. from Parquet to Delta Lake),
only this file needs to be updated.

Functions:
    read_csv     : Reads a CSV file into a pandas DataFrame
    read_parquet : Reads a Parquet file; returns empty DataFrame
                   if the file does not exist yet (first run)
    write_parquet: Writes a DataFrame to Parquet using pyarrow
"""

from pathlib import Path

import pandas as pd
from loguru import logger


def read_csv(path: Path, **kwargs: object) -> pd.DataFrame:
    """Read a CSV file from disk into a pandas DataFrame.
S
    Args:
        path: Full path to the CSV file.
        kwargs: Optional arguments forwarded to pandas read_csv
                (e.g. dtype, encoding, sep).

    Returns:
        DataFrame with the file contents.
    """

    logger.info(f"Reading CSV: {path}")
    df: pd.DataFrame = pd.read_csv(path, **kwargs)  # type: ignore[call-overload]
    logger.info(f"Loaded {len(df):,} rows from {path.name}")
    return df


def read_parquet(path: Path) -> pd.DataFrame:
    """Read a Parquet file from disk.

    Returns an empty DataFrame if the file does not exist, which
    happens on the first pipeline run before any Gold layer files
    have been created.

    Args:
        path: Full path to the Parquet file.

    Returns:
        DataFrame with the file contents, or empty DataFrame.
    """
    if not path.exists():
        logger.warning(f"Parquet not found: {path} — returning empty DataFrame")
        return pd.DataFrame()
    df = pd.read_parquet(path, engine="pyarrow")
    logger.info(f"Read {len(df):,} rows from {path.name}")
    return df


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame to disk as a Parquet file.

    Creates the parent directory if it does not exist.

    Args:
        df: DataFrame to write.
        path: Destination file path (including filename).
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow")
    logger.info(f"Wrote {len(df):,} rows to {path.name}")
