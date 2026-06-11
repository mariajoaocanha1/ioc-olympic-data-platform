"""
Slowly Changing Dimension — Type 2 implementation.

When a tracked attribute changes, the old record is expired (valid_to = now, is_current = False) and
a new record is inserted (valid_from = now, valid_to = None, is_current = True).

SCD types used per column:

DIM_ATHLETE:
  name        SCD Type 1 (Overwrite for name corrections)
  sex         SCD Type 1 (Overwrite)
  height_cm   SCD Type 2 (Physical changes matter for analysis)
  weight_kg   SCD Type 2 (Weight changes matter for analysis)

DIM_EVENT:
  sport       SCD Type 2 (Sports reorganised across Olympic editions)
  event_name  SCD Type 2 (Event names changed)

DIM_NOC:
  region      SCD Type 2 (Countries renamed or unified)
  notes       SCD Type 1 (No historical value)

DIM_DATE:
  all cols    SCD Type 0 (immutable, Olympic date never changes)
"""

from datetime import datetime
from typing import Optional
import pandas as pd
from loguru import logger


def _differs(a: object, b: object) -> bool:
    if pd.isna(a) and pd.isna(b):  # type: ignore[call-overload]
        return False
    if pd.isna(a) or pd.isna(b):  # type: ignore[call-overload]
        return True
    return bool(a != b)


def apply_scd2(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
    natural_key: str,
    tracked_cols: list[str],
    surrogate_key: str,
    as_of: Optional[datetime] = None,
) -> pd.DataFrame:
    now: datetime = as_of or datetime.utcnow()

    if existing.empty:
        logger.info("Initial load — inserting all records.")
        result = incoming.copy()
        result["valid_from"] = now
        result["valid_to"] = pd.NaT
        result["is_current"] = True
        result[surrogate_key] = range(1, len(result) + 1)
        return result

    current = existing[existing["is_current"]].copy()
    max_sk: int = int(existing[surrogate_key].max())
    new_rows: list[dict[str, object]] = []
    expire_sks: list[int] = []

    for _, inc in incoming.iterrows():
        nk = inc[natural_key]
        match = current[current[natural_key] == nk]

        if match.empty:
            max_sk += 1
            row = inc.to_dict()
            row[surrogate_key] = max_sk
            row["valid_from"] = now
            row["valid_to"] = None
            row["is_current"] = True
            new_rows.append(row)
        else:
            ext = match.iloc[0]
            changed = any(
                _differs(ext.get(c), inc.get(c))
                for c in tracked_cols
                if c in inc.index
            )
            if changed:
                expire_sks.append(int(ext[surrogate_key]))
                max_sk += 1
                row = inc.to_dict()
                row[surrogate_key] = max_sk
                row["valid_from"] = now
                row["valid_to"] = None
                row["is_current"] = True
                new_rows.append(row)

    updated = existing.copy()
    if expire_sks:
        mask = updated[surrogate_key].isin(expire_sks)
        updated.loc[mask, "valid_to"] = now
        updated.loc[mask, "is_current"] = False
        logger.info(f"Expired {len(expire_sks)} records.")

    if new_rows:
        logger.info(f"Inserting {len(new_rows)} new/updated records.")
        updated = pd.concat([updated, pd.DataFrame(new_rows)], ignore_index=True)

    return updated