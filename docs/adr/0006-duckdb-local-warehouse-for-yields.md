# DuckDB as the local warehouse for the YIELD_DATA domain (no Snowflake/Spark)

## Context

The equity pipeline loads to **Snowflake** via **PySpark** (`src/warehouse/snowflake/`,
`migrations/snowflake/`, a Snowflake dbt profile). Snowflake is a paid cloud
warehouse and PySpark needs the Docker `markets-pyspark` image, so *any* run or
test of that path requires cloud credentials and containers.

The new `YIELD_DATA` domain (US Treasury yields) is tiny — the whole curve is a
few thousand `(Tenor, Trading Date)` rows per year. Running it through Spark and a
cloud warehouse would be disproportionate, and it would make local development
and CI depend on Snowflake credentials. We want this feature to be runnable and
unit-testable **locally, for free, with no Docker and no Snowflake**.

## Decision

Use **DuckDB** as the default warehouse for the `YIELD_DATA` domain, accessed with
**plain Python** (no PySpark):

- The warehouse is a single local DuckDB file (path via `YIELD_WAREHOUSE_DB`,
  default under the datalake). `ensure_tables` creates `RAW_TREASURY_YIELDS`
  (PK `(TENOR, TRADING_DATE)`, giving idempotent upserts) and a per-Tenor
  `METASTORE_LAST_TRADING_DATE` on first use — no migration or server.
- The load, quality checks (non-null + sane band, validated before write), the
  incremental filter, and the metastore are ordinary Python functions taking a
  DuckDB connection, so tests run against an in-memory database.
- dbt models for yields run on a separate **`dbt-duckdb`** target; SQL is kept
  dialect-portable so Snowflake can be added as an optional target later.
- The equity `STOCK_DATA` pipeline is unchanged — it keeps Snowflake + PySpark.

## Considered options

- **Snowflake + PySpark (as for equities)** — consistent with the existing
  pipeline, but forces cloud credentials + Docker for every run/test and is
  overkill for a few thousand rows. Rejected for local-first development.
- **Postgres (local, via Docker)** — free and dbt-friendly, and Spark could write
  over JDBC, but it needs a running container and is not a columnar/analytical
  engine. Heavier than DuckDB for no benefit at this scale.
- **Snowflake free trial** — 30 days of credits only; does not give durable free
  local development.

## Consequences

- The project now uses **two warehouse engines**: Snowflake (equities) and DuckDB
  (yields). This is deliberate and isolated by domain; the trade-off is two dbt
  targets and some dialect care rather than one warehouse.
- The entire yields ingestion pipeline (fetch → normalize → load → quality →
  metastore) is runnable and green **offline**:
  `PYTHONPATH=src python -m pytest src/yield_data/` — no Snowflake, no Docker.
- Spark is not used for yields; the tiny dataset makes plain Python simpler and
  faster to test. If yields grow by orders of magnitude, revisit.
- Snowflake remains available as a future optional target for yields; promoting
  DuckDB models to Snowflake is a later, deliberate step, not a default.
- New Python dependencies: `duckdb` (and `dbt-duckdb` for modeling).
