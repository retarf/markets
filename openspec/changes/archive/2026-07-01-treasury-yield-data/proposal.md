## Why

We are adding **US Treasury yields** as a new asset class, to back the project's
first frontend feature (a yields dashboard). This change lands the **data half**:
getting Treasury yields into a local warehouse and modelling the Yield Curve and 2s10s Spread
— everything needed to *query* the data. The serving tier and the React dashboard
are a separate, dependent change (`treasury-yields-dashboard`).

A **Yield** is a rate `(Tenor, Trading Date) → %`, not an equity **Daily Bar** —
no OHLC, no volume — and it comes from the **U.S. Treasury** (the keyless *Daily
Treasury Par Yield Curve Rates* CSV feed), not Yahoo. Forcing it through the equity
path would corrupt the glossary and break the `volume > 0` quality check, so it
lands as a **parallel `YIELD_DATA` domain** (ADR 0003) that reuses the equity
pipeline's *patterns* (dated datalake, metastore-driven incremental load,
validate-before-write) but not its schema. Backfilling history is a durable,
resumable job, so **Temporal** owns it while **Airflow** owns the daily pull
(ADR 0004).

## What Changes

- **New `YIELD_DATA` domain** — U.S. Treasury constant-maturity yields (`1M,3M,6M,
  1Y,2Y,3Y,5Y,7Y,10Y,20Y,30Y`) from the keyless Treasury CSV feed (full curve, one
  request per year), normalized to `(Tenor, Trading Date, Yield)`, landed in
  `datalake/YIELD_DATA/dt=YYYY-MM-DD/`, and loaded to a **local DuckDB** raw table
  (no Snowflake/Spark for this domain — ADR 0006) with a **yield-appropriate**
  quality check (no `volume` rule) and a **per-Tenor metastore** for incremental
  loading. Because the dataset is tiny, the load is plain Python + DuckDB.
- **Gaps stay gaps** — an empty Treasury cell is dropped end to end, never
  zero-filled or interpolated.
- **Orchestration** — Airflow runs the **daily** pull; **Temporal** owns
  **on-demand historical backfill**. Both invoke the same fetch/validate/load
  activities.
- **New dbt models** — `stg_treasury_yields`, a **Yield Curve** model (yield vs
  Tenor per Trading Date, maturity-ordered), a **2s10s Spread** model (`10Y − 2Y`
  in basis points, derived from stored legs), and a per-Tenor series accessor.

## Capabilities

### New Capabilities

- `treasury-yield-ingestion`: how Treasury yields are sourced from the U.S.
  Treasury feed, validated, landed in the `YIELD_DATA` datalake, loaded with
  per-Tenor incremental state, and orchestrated (Airflow daily + Temporal
  backfill).
- `treasury-yield-modeling`: the dbt analytical layer — Yield Curve, 2s10s Spread,
  and per-Tenor series — with honest gap handling.

## Impact

- **New code:** a Treasury fetch/normalize module and a plain-Python DuckDB
  load/metastore/quality module for the `YIELD_DATA` domain; an Airflow yields DAG;
  a Temporal backfill workflow + worker; new dbt-duckdb models.
- **Config / infra:** `.env.example` gains the keyless Treasury CSV URL template
  (no API key) and an optional `YIELD_WAREHOUSE_DB` path; the DuckDB warehouse is a
  single local file created on first load (no migration/server); `docker-compose.yml`
  gains **Temporal** (+ its datastore) and a worker host for the backfill.
- **Unchanged:** the equity `STOCK_DATA` pipeline, its Airflow DAG, PySpark schema,
  quality checks, dbt models, and Snowflake objects.
- **External dependency:** the U.S. Treasury CSV feed (keyless, no key/payment);
  Python deps `duckdb` (+ `dbt-duckdb`, and `temporalio` for the backfill worker);
  a Temporal dev-server container added to the local stack.
- **Backend-only:** no frontend, no serving API, no NATS in this change.

## Downstream

The serving tier (API gateway + query service + NATS `treasury.yields.ingested`
event + SSE) and the React dashboard build on these models in the dependent change
`treasury-yields-dashboard`.
