## Context

The repo today is a batch data pipeline: Yahoo → dated datalake → Airflow/PySpark
→ Snowflake (`RAW_STOCK_DATA` + metastore) → dbt (`stg → fct signals → mart`).
This change adds a new asset class — US Treasury yields — as the data foundation
for a later yields dashboard.

A **Yield** is `(Tenor, Trading Date) → %` — a rate, no OHLC, no volume — sourced
from the **U.S. Treasury** keyless CSV feed, not Yahoo. The equity quality check
`greater_than_zero_quality_check` rejects `volume <= 0`, so yields cannot flow
through the equity path. They land as a **parallel `YIELD_DATA` domain** that
reuses the equity pipeline's *patterns* (dated datalake, metastore-driven
incremental load, validate-before-write) but not its schema. See ADRs 0003–0004
and `CONTEXT.md` (`Yield`, `Tenor`, `Yield Curve`, `2s10s Spread`).

## Goals / Non-Goals

**Goals:**
- Ingest U.S. Treasury constant-maturity yields into an isolated `YIELD_DATA` domain with
  honest, rate-appropriate quality and gap handling.
- Model the Yield Curve, the 2s10s Spread, and per-Tenor series in dbt so a
  serving layer can read them directly.
- Leave the equity `STOCK_DATA` pipeline completely untouched.

**Non-Goals:**
- The serving API, NATS event, SSE, and the React dashboard (the dependent
  `treasury-yields-dashboard` change).
- Foreign or Polish government yields (US Treasuries only).
- Replacing Airflow with Temporal (both coexist — ADR 0004).

## Decisions

- **Parallel `YIELD_DATA` domain, not the equity model** (ADR 0003). A Yield is
  not a Daily Bar; reusing `Ticker`/OHLCV would force fake OHLC + `volume` and
  weaken the shared quality check. _Alternative:_ generalize `STOCK_DATA` into a
  unified observation model — rejected now as a large refactor of working code.
- **Local DuckDB warehouse + plain Python (no Snowflake/Spark for yields)**
  (ADR 0006). The dataset is a few thousand rows, so Spark and a cloud warehouse
  are overkill; DuckDB is a single local file, free and offline, which makes the
  whole pipeline runnable and unit-testable with no Docker/Snowflake. Snowflake
  stays the equity warehouse and MAY be added as an optional yields target later.
  _Trade-off:_ the yields domain uses a different warehouse/engine than equities,
  and dbt runs a separate `dbt-duckdb` target; dbt SQL is kept dialect-portable.
- **U.S. Treasury CSV feed, full curve per year.** Keyless (no API key/payment),
  authoritative (FRED republishes it as `DGS*`), and one request returns every
  Tenor for a whole year — so there is no per-Tenor fan-out and backfill iterates
  years. An empty cell marks a gap and is dropped. Dates are `MM/DD/YYYY`
  (parsed to ISO); we keep only the tracked Tenor columns. The Tenor→column map
  (`10Y→"10 Yr"`, …) lives in one place. _Considered:_ FRED's keyless
  `fredgraph.csv` (also no key, but per-series and secondary) — Treasury is the
  primary source and gives the whole curve in one call.
- **2s10s derived from stored legs in dbt**, not fetched as FRED `T10Y2Y`. Keeps
  the spread internally consistent with the curve we store; mirrors the equity
  "store raw, derive downstream" stance. _Trade-off:_ a date missing either leg has
  no spread (correct — no fabricated value).
- **Airflow daily pull + Temporal on-demand backfill** (ADR 0004). The daily pull
  is a cron-shaped batch job Airflow already does; backfill is long-running,
  resumable, rate-paced — Temporal's shape. Both call the **same**
  fetch/validate/load activities, so ingestion logic is not duplicated. _Rejected:_
  Temporal for the daily pull too (under-uses it).
- **Yield-appropriate quality checks.** Non-null Date/Yield + a configurable sane
  band (e.g. `-5%..25%`); the equity `volume > 0` and `HIGH >= LOW` rules do not
  apply.

## Risks / Trade-offs

- [Treasury endpoint/format changes] → isolated in the fetch module; validation
  fails loudly on unexpected/empty payloads; backfill is paced.
- [Gaps (empty cells) silently interpolated] → explicitly dropped in ingestion and
  modeling — the single most important honesty requirement.
- [Two orchestrators (Airflow + Temporal)] → boundary documented (schedule vs
  durable backfill); they share activity code (ADR 0004).

## Migration Plan

1. Add the keyless Treasury CSV URL template to `.env` / `.env.example` (no key).
2. The DuckDB warehouse (`RAW_TREASURY_YIELDS` + per-Tenor metastore) is created
   on first load — a single local file, independent of the equity warehouse.
3. Build ingestion (Treasury activities), the Airflow yields DAG, and the Temporal
   backfill worker; backfill history via Temporal.
4. Build the dbt models (curve, 2s10s, series).
5. Rollback: additive and isolated — remove the new DAG/worker and the
   `YIELD_DATA` objects; the equity pipeline is unaffected.

## Open Questions

- Exact band for the yield sanity check (`-5%..25%` proposed) — confirm against
  real data during build.
