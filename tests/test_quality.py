"""
test_quality.py
---------------
Unit tests for the data quality validation functions.

Covers the two main validation scenarios:
  1. Rows with missing required fields are dropped.
  2. Rows with invalid Sex values are dropped.
"""
import pandas as pd
from src.olympics_pipeline.quality import validate_athlete_events


def _make_valid_row(athlete_id: int, name: str, sex: str) -> dict[str, object]:
    """Helper to build a valid athlete event row."""

    return {
        "ID": athlete_id,
        "Name": name,
        "NOC": "USA",
        "Year": 2000,
        "Season": "Summer",
        "Sport": "Swimming",
        "Event": "100m Freestyle",
        "Sex": sex,
    }


def test_drops_rows_missing_required_fields() -> None:
    """Rows with null ID are removed by the quality check."""

    df = pd.DataFrame([
        _make_valid_row(1, "Valid Athlete", "M"),
        {**_make_valid_row(2, "Missing ID", "F"), "ID": None},
    ])
    result = validate_athlete_events(df)
    assert len(result) == 1
    assert result.iloc[0]["Name"] == "Valid Athlete"


def test_drops_invalid_sex_values() -> None:
    """Rows with Sex values other than M or F are removed."""

    df = pd.DataFrame([
        _make_valid_row(1, "Valid Athlete", "M"),
        _make_valid_row(2, "Invalid Sex", "X"),
    ])
    result = validate_athlete_events(df)
    assert len(result) == 1
    assert result.iloc[0]["Name"] == "Valid Athlete"


def test_valid_rows_are_preserved() -> None:
    """All valid rows pass through the quality check unchanged."""
    
    df = pd.DataFrame([
        _make_valid_row(1, "Athlete One", "M"),
        _make_valid_row(2, "Athlete Two", "F"),
    ])
    result = validate_athlete_events(df)
    assert len(result) == 2