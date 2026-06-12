# Olympic Data Platform (ioc-olympic-data-platform)

A batch data pipeline built for the International Olympic Committee (IOC).

Processes 120 years of Olympic history data through a medallion architecture
(Bronze → Silver → Gold), producing a star schema ready for analytical queries.

## Assessment Deliverables

| Deliverable | Description |
|-------------|-------------|
| [olympic_data_platform_assessment.pdf](./olympic_data_platform_assessment.pdf) | Architecture diagram, star schema, executive summary and SCD specification |
| [src/olympics_pipeline/](./src/olympics_pipeline/) | Full pipeline implementation |

## Architecture

The pipeline follows a medallion data lake architecture with three layers:

- **Bronze** — Raw CSV data ingested and persisted as Parquet, unchanged
- **Silver** — Cleansed, typed, and validated data
- **Gold** — Star schema dimensions and fact table, ready for analytics

Implemented locally with pandas and Parquet, following the same logical
separation that would apply in a production environment.

The architecture is execution-engine agnostic — business logic remains
unchanged regardless of whether the pipeline runs locally or on a 
distributed platform.

## Repository Structure

```
ioc-olympic-data-platform/
├── olympic_data_platform_assessment.pdf  # Assessment deliverable
├── README.md
├── Makefile                              # run, test, lint, typecheck
├── requirements.txt
├── pyproject.toml                        # 'mypy' and 'ruff' configuration
├── docs/                                 # Architecture and schema diagrams
├── src/
│   └── olympics_pipeline/
│       ├── config.py                     # Paths and constants
│       ├── io.py                         # Read/Write Parquet and CSV
│       ├── main.py                       # Pipeline entrypoint
│       ├── quality.py                    # Data quality validation
│       ├── scd.py                        # SCD Type 2 logic
│       ├── schemas.py                    # Typed dataclasses
│       └── transformations.py            # Bronze to Silver to Gold
├── tests/
│   ├── test_quality.py                   # Quality gate unit tests
│   └── test_scd.py                       # SCD Type 2 unit tests
└── data/                                 # Content not tracked (Generated at runtime)
    ├── raw/                              # Place Kaggle CSVs here
    ├── bronze/
    ├── silver/
    └── gold/
``` 

## Star Schema

One fact table connected to four dimensions:

| Table | Description |
|-------|-------------|
| FACT_RESULT | One row per athlete per Olympic event |
| DIM_ATHLETE | Athlete profiles (SCD Type 2) |
| DIM_EVENT | Sport and event names (SCD Type 2) |
| DIM_NOC | Country/Region data (SCD Type 2) |
| DIM_DATE | Olympic edition (SCD Type 0) | 

## SCD Types

| Table | Column | SCD Type | Rationale |
|-------|--------|----------|-----------|
| DIM_ATHLETE | name | Type 1 | Overwrite, name corrections (Not historical events) |
| DIM_ATHLETE | sex | Type 1 | Overwrite (No historical value) |
| DIM_ATHLETE | height_cm | Type 2 | Physical changes matter for analysis |
| DIM_ATHLETE | weight_kg | Type 2 | Weight changes affect performance analysis |
| DIM_EVENT | sport | Type 2 | Sports reorganised across Olympic editions |
| DIM_EVENT | event_name | Type 2 | Event names changed over 120 years |
| DIM_NOC | region | Type 2 | Countries renamed, unified or dissolved |
| DIM_NOC | notes | Type 1 | Administrative (No historical value) |
| DIM_DATE | all | Type 0 | Olympic dates are immutable | 

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

# 4. Run everything
make all
``` 

## Pipeline Output

| Table | Rows |
|-------|------|
| dim_athlete | 135,571 |
| dim_event | 765 |
| dim_noc | 230 |
| dim_date | 51 |
| fact_result | 270,767 | 

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11 | Core language |
| pandas 2.2 | Data processing |
| pyarrow | Parquet read/write |
| mypy (strict) | Static type checking |
| pytest | Unit testing |
| ruff | Linting | 