from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RawAthleteEvent:
    id: int
    name: str
    sex: str
    age: Optional[float]
    height: Optional[float]
    weight: Optional[float]
    team: str
    noc: str
    games: str
    year: int
    season: str
    city: str
    sport: str
    event: str
    medal: Optional[str]


@dataclass
class RawNocRegion:
    noc: str
    region: Optional[str]
    notes: Optional[str]


@dataclass
class DimAthlete:
    athlete_sk: int
    athlete_nk: int
    name: str
    sex: str
    height_cm: Optional[float]
    weight_kg: Optional[float]
    valid_from: datetime
    valid_to: Optional[datetime]
    is_current: bool


@dataclass
class DimEvent:
    event_sk: int
    event_nk: str
    sport: str
    event_name: str
    valid_from: datetime
    valid_to: Optional[datetime]
    is_current: bool


@dataclass
class DimNoc:
    noc_sk: int
    noc_code: str
    region: Optional[str]
    notes: Optional[str]
    valid_from: datetime
    valid_to: Optional[datetime]
    is_current: bool


@dataclass
class DimDate:
    date_sk: int
    year: int
    season: str
    games_edition: str


@dataclass
class FactResult:
    result_sk: int
    athlete_sk: int
    event_sk: int
    noc_sk: int
    date_sk: int
    medal: Optional[str]
    age_at_event: Optional[float]
    year: int
    season: str
