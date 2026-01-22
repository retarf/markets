# 📊 Markets — Data Engineering & Analytics Project

## Overview

**Markets** is a data engineering and analytics project focused on researching historical returns of a **simple trading strategy based on three Simple Moving Averages (SMA)**.

The project demonstrates an end-to-end data pipeline built with **modern data engineering and analytics engineering practices**, including:
- batch data ingestion,
- warehouse-centric transformations,
- workflow orchestration,
- and signal generation for financial time-series data.

The project is intentionally designed as a **demo / portfolio project**.  
It focuses on **data pipelines, transformations, and analytical logic**, not on real-time trading or production execution.

---

## Project Goals

- Demonstrate **data engineering best practices**
- Build a reproducible, layered data model for market data
- Generate trading signals based on **three SMA indicators**
- Orchestrate batch workflows using **Apache Airflow**
- Prepare a foundation for further **strategy return analysis**

---

## Scope and Limitations

### In scope (current state)
- Batch ingestion of market data as CSV files
- Workflow orchestration with Apache Airflow
- Data transformations using dbt
- Snowflake as the analytical warehouse
- Technical indicators (SMA), trends, and signals

### Out of scope (current state)
- Real-time / streaming ingestion
- Trade execution
- Predictive modeling or alpha generation
- API layer or frontend

### Planned extensions
- Strategy return analysis using **pandas** and **PySpark**
- API layer for querying results
- Simple React-based frontend for visualization

---

## Data Source

- Input data is provided as **CSV files**
- CSV files are downloaded via an external API
- The data provider is intentionally **abstracted and not included** due to licensing and non-commercial usage restrictions
- The project focuses on **data processing and analytics**, not vendor-specific ingestion logic

---

## Input Data Format

The pipeline expects market data in **CSV format** with a consistent schema.

### Expected CSV Structure

| Column name     | Type    | Description |
|-----------------|---------|-------------|
| `trading_date`  | DATE    | Trading date |
| `ticker`        | STRING  | Market symbol (e.g. AAPL, MSFT) |
| `open`          | NUMERIC | Opening price |
| `high`          | NUMERIC | Highest price |
| `low`           | NUMERIC | Lowest price |
| `close`         | NUMERIC | Closing price |
| `volume`        | NUMERIC | Trading volume |

### Assumptions

- Dates are in **ISO format (`YYYY-MM-DD`)**
- Prices are assumed to be **adjusted prices**
- Data is historical and append-only
- Data quality checks (nulls, duplicates, ordering) are handled in dbt staging models

The CSV schema is treated as a **data contract**, enforced during transformations.

---

## Architecture Overview

The project follows a **batch-oriented, warehouse-first architecture**:

```
External API
   ↓
CSV files
   ↓
Apache Airflow (orchestration)
   ↓
Snowflake (raw data)
   ↓
dbt staging models
   ↓
dbt fact models
   ↓
dbt marts / signals
```

All analytical and business logic is implemented as **SQL models in dbt**, ensuring:
- reproducibility,
- testability,
- transparency of transformations.

---

## Workflow Orchestration (Apache Airflow)

Apache Airflow is used to orchestrate the data pipeline.

Airflow responsibilities include:
- scheduling pipeline runs,
- managing task dependencies,
- coordinating ingestion and transformation steps.

Typical workflow:
1. Download market data and store it as CSV
2. Load raw CSV data into Snowflake
3. Execute dbt models (staging → facts → marts/signals)

The Airflow DAGs define execution order, retries, and failure handling for the pipeline.

---

## dbt Layered Model

### Staging Layer
- Cleans and standardizes raw CSV data
- Applies type casting and basic validation
- No business logic
- One-to-one mapping with raw inputs

### Fact Layer
- Core market facts (prices per ticker and date)
- Time-series–oriented structure
- Prepared for analytical calculations

### Marts / Signals Layer
- Calculation of Simple Moving Averages
- Trend detection
- Signal generation based on SMA relationships

Each layer has a single, well-defined responsibility.

---

## Trading Strategy (Current)

The current strategy is based on:
- **three Simple Moving Averages**
- relative positioning of short-, medium-, and long-term SMAs
- trend and signal derivation from SMA relationships

The project does **not** claim profitability or predictive power.  
Its purpose is to **analyze historical behavior**, not to provide investment advice.

---

## Tech Stack

- **Python**
- **Apache Airflow**
- **dbt**
- **Snowflake**
- **SQL**
- **CSV-based datasets**

Planned / future usage:
- pandas
- PySpark
- REST API
- React (UI)

---

## Why This Project Exists

This project was built to:
- practice and demonstrate **data engineering and analytics engineering**
- show clean data modeling for financial time-series data
- combine orchestration, warehousing, and transformations in a single pipeline
- serve as a portfolio project for data-focused engineering roles

---

## Disclaimer

This project is for **educational and demonstration purposes only**.  
It does not constitute financial advice, trading recommendations, or investment guidance.
