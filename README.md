# markets

# Financial Market Data Pipeline (Airflow + PostgreSQL + Parquet)

This project is an end-to-end data pipeline built with **Apache Airflow**, designed to collect, transform, and load financial market data into a PostgreSQL database.  
It uses public data from **source** and modern Python data processing tools such as **Polars** and **PyArrow**.

---

## Overview

The pipeline automates the full ETL flow:

1. **Pull stock data** – downloads daily market data (CSV) for selected tickers from financial data website.).
2. **Reformat to Parquet** – converts raw CSV files to columnar Parquet format for efficient storage and further processing.
3. **Load to Database** – loads Parquet data into PostgreSQL tables (one per ticker symbol).

---

## ⚙️ Architecture

```text
          +--------------------+
          |   Source API (CSV)  |
          +---------+----------+
                    |
                    v
        +-----------+------------------+
        | pull_stock_data_dag          |
        |  (API -> requests -> CSV)    |
        +------------------+-----------+
                    |
                    v
        +-----------+-------------------+
        | reformat_to_parquet_dag       |
        |  (CSV -> PyArrow -> Parquet)  |
        +-----------+-------------------+
                    |
                    v
        +-----------+--------------------------+
        | load_parquet_to_database_dag         |
        |  (Parquet -> Polars -> PostgreSQL)   |
        +--------------------------------------+
````

---

## Technologies Used

| Category               | Tools                                                  |
| ---------------------- | ------------------------------------------------------ |
| Workflow Orchestration | Apache Airflow                                         |
| Data Processing        | Python, Polars, PyArrow                                |
| Storage                | Parquet                                                |
| Database               | PostgreSQL                                             |
| HTTP Client            | requests                                               |
| Infrastructure         | Docker (optional), environment variables for DB config |

---

## DAGs Description

### `pull_stock_data_dag.py`

Downloads CSV files with daily stock prices from source website for a list of tickers.
Each ticker runs as a separate Airflow task.

**Key modules:**

* `requests` for fetching data
* simple validation to skip empty tickers

**Example output:**
`/project/datalake/xtb.csv`

---

### `reformat_to_parquet_dag.py`

Converts CSV files into Parquet format for optimized analytical storage.

**Key modules:**

* `pyarrow.csv`
* `pyarrow.parquet`

**Example output:**
`/project/datalake/xtb.parquet`

---

### `load_parquet_to_database_dag.py`

Loads Parquet data into PostgreSQL database tables using Polars.

**Key modules:**

* `polars`
* `write_database()` for efficient bulk inserts

**Environment variables required:**

```bash
DATA_SOURCE_URI=
DB_PASSWORD=
DB_NAME=
DB_USER=
DB_HOST=db
DB_PORT=5432
AIRFLOW_HOME=/project/airflow
AIRFLOW_UID=
AIRFLOW_GID=
```

---

## How to Run Locally

1. Clone the repository:

   ```bash
   git clone https://github.com/retarf/markets.git
   cd markets
   ```

2. Set up environment variables (e.g. in `.env` file or Airflow UI).

3. Start Airflow:

   ```bash
   docker-compose up -d
   ```

4. Check DAGs in Airflow UI and trigger:

   * `pull_stock_data_dag`
   * `reformat_to_parquet_dag`
   * `load_parquet_to_database_dag`

---

## Learning Goals

This project demonstrates:

* building a complete **data ingestion → transformation → loading** workflow,
* orchestrating tasks with **Airflow DAGs**,
* working with **columnar data (Parquet)**,
* using **Polars and PyArrow** for high-performance ETL,
* storing and managing data in **PostgreSQL**.

---

## Possible Improvements

To make this project even more impressive and valuable on the job market:

| Area              | Suggestion                                                                           |
| ----------------- | ------------------------------------------------------------------------------------ |
| **Monitoring**    | Add Airflow task logging and retry logic. Integrate with Prometheus or Slack alerts. |
| **Data Quality**  | Implement data validation (e.g. Great Expectations or custom checks in Polars).      |
| **Storage Layer** | Add S3 (or MinIO locally) as a data lake layer.                                      |
| **Metadata**      | Store ETL run metadata (execution date, data range, row count).                      |
| **Automation**    | Add scheduling (daily runs) and notifications for failures.                          |
| **Analytics**     | Build a small Streamlit / Grafana dashboard to visualize price trends.               |
| **Testing**       | Include unit tests for each operation (`pytest` + mock data).                        |
| **CI/CD**         | Use GitHub Actions to lint, test, and deploy DAGs automatically.                     |

---

## Example Use Cases

* Tracking daily financial instrument data (stocks, indices, FX).
* Demonstrating end-to-end ETL orchestration in a **data engineer portfolio**.
* Integrating with AWS (S3, RDS) or GCP (BigQuery) for cloud-based data pipelines.

---

##  Author

**Łukasz Długajczyk**
Python Developer | Data Engineering Enthusiast
[LinkedIn Profile](https://www.linkedin.com/in/lukaszdlugajczyk/) | [GitHub Profile](https://github.com/retarf)

```
