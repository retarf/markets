# Markets — Data Engineering & Analytics Project

Markets is a portfolio project focused on building an end-to-end batch pipeline for historical stock market data.

The project combines:

- **Python** for ingestion logic
- **Apache Airflow** for orchestration
- **PySpark** for loading and validating data
- **Snowflake** as the analytical warehouse
- **dbt** for downstream SQL transformations
- **Docker Compose** for local development

The current implementation is intentionally **batch-oriented** and **warehouse-first**. It is meant to demonstrate data engineering practices around ingestion, orchestration, validation, incremental loading, and layered transformations rather than real-time trading or investment automation.

## Project goals

- build a reproducible market data pipeline
- orchestrate ingestion and warehouse loading with Airflow
- validate raw input data before loading it into Snowflake
- support incremental processing using a metastore table
- prepare a clean base for analytical models and trading signals in dbt
- showcase production-minded project structure for a Data Engineering portfolio

## Current scope

### In scope

- downloading historical market data from an external source as CSV files
- storing raw files in a dated local datalake structure
- orchestrating ingestion with Airflow DAGs
- loading recent data into Snowflake with PySpark
- running basic data quality checks before write
- keeping incremental-load state in a Snowflake metastore table
- modeling downstream analytical layers in dbt
- serving warehouse data over FastAPI microservices (Docker Compose, for now)
- a single-user analytical & research frontend in React + TypeScript + Vite
  (see [ADR 0002](docs/adr/0002-react-research-platform-over-fastapi.md))

### Out of scope

- real-time / streaming ingestion
- order execution or broker integration
- predictive modeling / ML
- multi-user accounts / auth (single user for now)
- production observability stack

## Architecture overview

The pipeline currently follows this flow:

```text
External data source
        ↓
CSV files in local datalake
        ↓
Airflow DAGs
        ↓
PySpark ingestion and validation
        ↓
Snowflake raw + metastore tables
        ↓
dbt transformations
        ↓
Analytical models / signals
        ↓
FastAPI microservices (Docker Compose)
        ↓
React + TypeScript + Vite frontend (single-user research platform)
```

This separation is deliberate:

- **Airflow** controls execution and dependencies
- **PySpark** handles file reading, filtering, validation, and loading
- **Snowflake** stores raw and metadata tables
- **dbt** owns analytical SQL transformations
- **FastAPI** serves warehouse data to the frontend as JSON
- **React + TypeScript + Vite** renders the single-user analytical & research UI

## Repository structure

The README below reflects the current repository layout:

```text
markets/
├── airflow/
│   ├── dags/
│   │   └── stock_data/
│   │       ├── fetch_data_dag.py
│   │       └── ingest_to_snowflake_dag.py
│   ├── .gitignore
│   └── airflow.cfg
├── dbt/
│   ├── .gitignore
│   └── snowflake/
│       ├── analyses/
│       ├── macros/
│       ├── models/
│       ├── seeds/
│       ├── snapshots/
│       ├── tests/
│       ├── .gitignore
│       ├── .user.yml
│       ├── README.md
│       ├── dbt_project.yml
│       ├── package-lock.yml
│       ├── packages.yml
│       └── profiles-example.yml
├── dockerfile/
│   └── airflow/
│       ├── Dockerfile
│       ├── requirements.in
│       └── requirements.txt
├── migrations/
│   └── snowflake/
│       └── migrate.py
├── src/
│   ├── stock_data/
│   │   ├── fetch_data/
│   │   │   ├── __init__.py
│   │   │   ├── operations.py
│   │   │   └── utils.py
│   │   ├── push_data/
│   │   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── operations.py
│   │   │   └── quality_checks.py
│   │   └── __init__.py
│   ├── warehouse/
│   │   ├── snowflake/
│   │   │   ├── libs/
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   └── table.py
│   │   └── __init__.py
│   ├── .gitignore
│   ├── __init__.py
│   └── assets.py
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Pipeline components

### 1. Fetch DAG

`airflow/dags/stock_data/fetch_data_dag.py`

This DAG runs daily and uses **dynamic task mapping** to fetch data for each ticker from `TICKER_LIST`. It writes CSV files into a deterministic dated directory under the datalake and emits an Airflow asset after the fetch step completes. citeturn992202view0turn992202view2turn185540view0

Current tickers are defined in code and the fetched files are stored under a directory structure based on execution date, for example `dt=YYYY-MM-DD`. The fetch logic also validates the response and rejects a known “no data” payload. citeturn185540view0

### 2. Ingestion DAG

`airflow/dags/stock_data/ingest_to_snowflake_dag.py`

This DAG runs daily and processes files from the datalake. Its current flow is:

1. find the latest eligible dated directory,
2. list CSV files in that directory,
3. process each file with dynamic task mapping,
4. load recent rows into Snowflake. citeturn992202view1

### 3. PySpark loading logic

`src/stock_data/push_data/operations.py`

The PySpark ingestion layer:

- reads CSV files with an explicit schema,
- identifies ticker and processing date from the file path,
- loads the metastore table from Snowflake,
- determines the latest already-loaded business date for the ticker,
- filters only recent rows,
- applies quality checks,
- writes raw data to Snowflake,
- writes the newest processed date back to the metastore table. citeturn185540view1turn808173view0turn992202view3

This is the most important production-minded idea in the project right now: **incremental loading is controlled by state kept in Snowflake rather than by reloading everything every time**. citeturn185540view1turn808173view0

## Data quality checks

Basic validation is implemented in `src/stock_data/push_data/quality_checks.py`.

Current checks verify:

- required fields are not null,
- prices and volume are greater than zero,
- `HIGH >= LOW`. citeturn992202view4

This is a good direction because quality is enforced before write, not left entirely to downstream modeling.

## Incremental loading and metastore

The project already contains a metastore pattern.

`src/stock_data/push_data/__init__.py` defines a Snowflake metastore table for storing the last loaded trading date per ticker, and `migrations/snowflake/migrate.py` creates that table during setup. citeturn808173view0turn185540view4

This allows the ingestion logic to:

- read the previously loaded date,
- keep only newer records,
- update state after a successful load. citeturn185540view1

That is much better than reloading the full history every day.

## Snowflake setup

Snowflake bootstrap is handled in `migrations/snowflake/migrate.py` using the Snowflake Python connector.

The migration script currently creates:

- the database,
- raw and development schemas,
- the raw stock data table,
- the metastore schema,
- the metastore table,
- users / roles / grants for dbt and PySpark service users. citeturn185540view4

This is a strong point of the project because infrastructure/bootstrap concerns are separated from the main pipeline runtime.

## Warehouse access layer

The Snowflake access helpers live under `src/warehouse/snowflake/`.

- `session.py` builds Spark sessions and Snowflake connector options,
- `table.py` provides reusable `load_table` and `save_table` helpers. citeturn185540view2turn992202view3

This keeps connector details out of the DAG code and out of the business logic.

## dbt layer

The repository contains a dedicated dbt project under `dbt/snowflake/` with the standard dbt structure: `models`, `macros`, `tests`, `seeds`, `snapshots`, and configuration files such as `dbt_project.yml` and `profiles-example.yml`. citeturn196408view3

That gives the project a good separation between:

- ingestion and loading,
- warehouse storage,
- analytical SQL modeling.

## Local development

The project uses Docker Compose to run the local environment. The compose file builds an Airflow-based service from `dockerfile/airflow/Dockerfile`, mounts the project directories, loads environment variables from `.env`, and starts a Postgres service as well. It also supports a custom home directory mount through `DOCKER_HOME_DIR`. citeturn915894view2

Typical startup:

```bash
docker compose up --build
```

## Environment configuration

The repository contains `.env.example`, which should be copied to `.env` and filled with local values before running the project. The project relies on environment variables for:

- Snowflake account and warehouse settings,
- db / service-user credentials,
- key file paths for Snowflake authentication,
- external data source URI. citeturn185540view0turn185540view2turn185540view4

## What this project already shows well

This repo already demonstrates several good data engineering practices:

- clear separation of ingestion, orchestration, warehouse access, and transformations,
- deterministic datalake directory structure,
- explicit input schema for CSV loading,
- pre-load quality checks,
- incremental loading via a metastore table,
- Snowflake bootstrap separated into migrations,
- Airflow dynamic task mapping. citeturn185540view0turn185540view1turn185540view4turn992202view0turn992202view1

## Known limitations / next improvements

To make the project look even more production-minded, the next high-value improvements would be:

1. add a pipeline run history table in addition to the current last-date metastore,
2. make idempotency behavior explicit in the README and code comments,
3. add stronger tests around ingestion and metastore behavior,
4. document the dbt models and signal layer more clearly,
5. review the directory selection logic in the ingestion DAG carefully,
6. add logging / observability notes and failure-recovery strategy.

## Disclaimer

This project is for educational and portfolio purposes only.
It is not investment advice and it is not intended for live trading.

## Author

Łukasz — Python / backend engineer transitioning into Data Engineering.
