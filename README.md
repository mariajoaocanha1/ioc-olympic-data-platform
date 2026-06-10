# Olympic Data Platform (ioc-olympic-data-platform)

A batch data pipeline built for the International Olympic Committee (IOC) analytics platform.

Processes 120 years of Olympic history data through a medallion architecture (Bronze → Silver → Gold), producing a star schema ready for analytical queries.

---

## Architecture

The pipeline follows a medallion lakehouse architecture with three layers:

- **Bronze** — raw CSV data ingested and persisted as Parquet, unchanged
- **Silver** — cleansed, typed, and validated data
- **Gold** — star schema dimensions and fact table, ready for analytics

Implemented locally with pandas and Parquet, following the same logical separation that would apply in a production environment.
The architecture is designed to be execution-engine agnostic, the business logic remains unchanged regardless of whether the pipeline runs locally or on a distributed platform.

---

## Star Schema

One fact table connected to four dimensions:

| Table | Description |
|-----------|----------|
| FACT_RESULT | One row per athlete per Olympic event |
| DIM_ATHLETE | Athlete profiles |
| DIM_EVENT | Sport and event names |
| DIM_NOC | Country/Region data |
| DIM_DATE | Olympic edition |

---

## SCD Types

| Table | Column | SCD Type | Rationale |
|-------|--------|----------|-----------|
| DIM_ATHLETE | name | Type 1 | Name corrections, not historical events |
| DIM_ATHLETE | sex | Type 1 | Overwrite — no historical value |
| DIM_ATHLETE | height_cm | Type 2 | Physical changes matter for analysis |
| DIM_ATHLETE | weight_kg | Type 2 | Weight changes affect performance analysis |
| DIM_EVENT | sport | Type 2 | Sports reorganised across Olympic editions |
| DIM_EVENT | event_name | Type 2 | Event names changed over 120 years |
| DIM_NOC | region | Type 2 | Countries renamed, unified or dissolved |
| DIM_NOC | notes | Type 1 | Administrative — no historical value |
| DIM_DATE | all | Type 0 | Olympic year and season are immutable |

---

## Project Structure

```
src/olympics_pipeline/
├── config.py           # paths and constants
├── schemas.py          # typed dataclasses
├── io.py               # read/write Parquet and CSV
├── quality.py          # data validation
├── scd.py              # SCD Type 2 logic
├── transformations.py  # Bronze to Silver to Gold
└── main.py             # pipeline entrypoint
```

---


## Quick Start

```bash
# 1. Clone
git clone https://github.com/mariajoaocanha1/ioc-olympic-data-platform.git
cd ioc-olympic-data-platform

# 2. Environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Add data
# Download from Kaggle and place both CSV files in data/raw/
# https://www.kaggle.com/datasets/heesoo37/120-years-of-olympic-history-athletes-and-results

# 4. Run pipeline
make run

# 5. Run tests
make test

# 6. Type check
make typecheck
```

---

## Pipeline Output

| Table | Rows |
|-------|------|
| dim_athlete | 135,571 |
| dim_event | 765 |
| dim_noc | 230 |
| dim_date | 51 |
| fact_result | 270,767 |

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11 | Core language |
| pandas 2.2 | Data processing |
| pyarrow | Parquet read/write |
| mypy (strict) | Static type checking |
| pytest | Unit testing |
| ruff | Linting |

---