## 1. Config & warehouse bootstrap

- [x] 1.1 Add the U.S. Treasury yield-curve CSV URL template (per-year, keyless) to `.env.example` (and `.env`) — no API key needed
- [x] 1.2 Define the canonical Tenor→Treasury-column map in one place (`1M→"1 Mo", 3M→"3 Mo", 6M→"6 Mo", 1Y→"1 Yr", 2Y→"2 Yr", 3Y→"3 Yr", 5Y→"5 Yr", 7Y→"7 Yr", 10Y→"10 Yr", 20Y→"20 Yr", 30Y→"30 Yr"`) — in `src/yield_data/__init__.py`
- [x] 1.3 Warehouse bootstrap for `YIELD_DATA`: DuckDB `RAW_TREASURY_YIELDS` (PK `(TENOR, TRADING_DATE)`) + `METASTORE_LAST_TRADING_DATE`, created idempotently — `yield_data/load_data/warehouse.py:ensure_tables` (local DuckDB, no Snowflake; ADR 0006)

## 2. Treasury ingestion (YIELD_DATA domain)

- [x] 2.1 Implement the fetch for a year: GET the keyless Treasury CSV for `<year>`, return the raw CSV text — `yield_data/fetch_data/operations.py:fetch_data`
- [x] 2.2 Parse the wide CSV → normalized `(Tenor, Date, Yield)` rows: US date `MM/DD/YYYY`→ISO, keep only tracked Tenor columns, drop empty cells (gaps) — never zero/carry-forward/interpolate — `parse_curve_to_rows`
- [x] 2.3 Validate the response (empty/no rows/missing expected columns → raise); write nothing on invalid — `validate_data`
- [x] 2.4 Write the normalized CSV (`Tenor,Date,Yield`, ISO dates) to `datalake/YIELD_DATA/dt=YYYY-MM-DD/` — `build_csv` + `create_dated_directory` + `save_data`, driven by `run.py`
- [x] 2.5 Implement the load: read the normalized CSV, apply yield-appropriate quality checks (non-null Tenor/Date/Yield, Yield within a configurable sane band, validated before write; NO volume/HIGH>=LOW rules), upsert to the DuckDB raw table — `load_data/{operations,quality_checks}.py`
- [x] 2.6 Implement the per-Tenor metastore incremental filter (load only newer than last-loaded per Tenor; advance state on success; idempotent on `(Tenor, Trading Date)`) — `load_data/{metastore,operations}.py`
- [x] 2.7 Extract fetch/normalize/load as reusable **activities** callable by both Airflow and Temporal — `yield_data/activities.py` (+ `backfill.py`); unit-tested (fetch stubbed; land+load real)

## 3. Orchestration

- [ ] 3.1 Airflow DAG for the daily yields pull — authored `airflow/dags/yield_data_dag.py` (fetch current-year curve → DuckDB load; equity DAG untouched). Needs a running Airflow + a runner image with `duckdb` to gate. (dev-verify)
- [x] 3.2 Temporal in `docker-compose.yml` — added a minimal `temporal` dev-server service (SQLite, no separate datastore); `docker compose config` validates. Backfill verified end-to-end against a running Temporal server in dev-verify.
- [x] 3.3 Temporal backfill workflow — `src/yield_data/temporal_backfill.py` (per-year retryable activity, resumable, reuses `ingest_year_activity`; `heartbeat_timeout=30s`). Verified live in dev-verify: 2024–25 backfill loaded 5489 rows; re-run loaded 0; kill+restart resumed with 0 duplicates.

## 4. dbt modeling (dbt-duckdb)

- [x] 4.1 Add a `dbt-duckdb` project/profile (`dbt/duckdb/`) pointing at the local DuckDB warehouse (`YIELD_WAREHOUSE_DB`); register `raw_treasury_yields` as a dbt source
- [x] 4.2 `stg_treasury_yields` — typed, deduplicated one row per `(Tenor, Trading Date)`, gaps preserved (`models/stg`)
- [x] 4.3 `fct_yield_curve` — yield per Tenor per Trading Date with a maturity rank (`tenor_order`); missing Tenor absent (not zero)
- [x] 4.4 `fct_2s10s_spread` — `10Y − 2Y` in basis points + `is_inverted`, derived from stored legs; absent when a leg is missing
- [x] 4.5 Per-Tenor series is served from `fct_yield_curve` (filter by Tenor over a window) — no separate model needed; documented rather than duplicated
- [x] 4.6 dbt tests: not_null on all model columns, uniqueness on `(Tenor, Trading Date)` and spread date, yield within-band singular test — `dbt build` PASS=18/18

## 5. Verification (live — handled in dev-verify, see tests.md)

- [ ] 5.1 Backfill history via Temporal, run the daily DAG, and confirm `dbt build` produces the curve/spread/series models
