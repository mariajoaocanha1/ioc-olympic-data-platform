"""
test_scd.py
-----------
Unit tests for the SCD Type 2 implementation.

Covers the three core scenarios:
  1. No change detected: Existing record unchanged.
  2. Tracked attribute changes: Old record expired, new version inserted.
  3. New natural key: Record inserted as current.
"""
from datetime import datetime

import pandas as pd

from src.olympics_pipeline.scd import apply_scd2

T0 = datetime(2000, 1, 1)
T1 = datetime(2004, 7, 1)


def make_existing() -> pd.DataFrame:
    """Return a minimal DIM_ATHLETE with one current record."""
    return pd.DataFrame([{
        "athlete_sk": 1,
        "athlete_nk": 42,
        "name": "Michael Phelps",
        "height_cm": 193.0,
        "weight_kg": 91.0,
        "valid_from": T0,
        "valid_to": None,
        "is_current": True,
    }])


def test_no_change_keeps_one_record() -> None:
    """When no tracked attribute changes, the dimension is unchanged."""
    existing = make_existing()
    incoming = pd.DataFrame([{
        "athlete_nk": 42,
        "name": "Michael Phelps",
        "height_cm": 193.0,
        "weight_kg": 91.0,
    }])
    result = apply_scd2(
        existing, incoming, "athlete_nk",
        ["height_cm", "weight_kg"], "athlete_sk", T1,
    )
    assert len(result) == 1
    assert bool(result.iloc[0]["is_current"]) is True


def test_change_creates_new_version() -> None:
    """When a tracked attribute changes, old record is expired and new one inserted."""
    existing = make_existing()
    incoming = pd.DataFrame([{
        "athlete_nk": 42,
        "name": "Michael Phelps",
        "height_cm": 193.0,
        "weight_kg": 88.0,
    }])
    result = apply_scd2(
        existing, incoming, "athlete_nk",
        ["height_cm", "weight_kg"], "athlete_sk", T1,
    )
    assert len(result) == 2
    old = result[result["athlete_sk"] == 1].iloc[0]
    new = result[result["athlete_sk"] == 2].iloc[0]
    assert bool(old["is_current"]) is False
    assert old["valid_to"] == T1
    assert bool(new["is_current"]) is True
    assert new["weight_kg"] == 88.0


def test_new_athlete_is_inserted() -> None:
    """A new natural key is inserted as a current record."""
    existing = make_existing()
    incoming = pd.DataFrame([{
        "athlete_nk": 99,
        "name": "New Athlete",
        "height_cm": 180.0,
        "weight_kg": 75.0,
    }])
    result = apply_scd2(
        existing, incoming, "athlete_nk",
        ["height_cm", "weight_kg"], "athlete_sk", T1,
    )
    assert len(result) == 2
    new = result[result["athlete_nk"] == 99].iloc[0]
    assert bool(new["is_current"]) is True
    assert new["athlete_sk"] == 2
