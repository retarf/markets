# Manual smoke tests

## Setup

- [ ] S.1 `.env` has the U.S. Treasury yield-curve CSV URL template (keyless — no API key); optional `YIELD_WAREHOUSE_DB` path
- [x] S.2 Python env has `duckdb` (+ `dbt-duckdb` for section 4). No Snowflake, no Docker required for sections 1–4
- [x] S.3 Automated gate is green: `PYTHONPATH=src python -m pytest src/yield_data/ -q`
- [x] S.4 (Only for the Temporal backfill scenarios) Temporal + worker running; the Temporal UI is reachable (used the running Temporal on localhost:7233; worker on the `yield-backfill` task queue)

## 1. Ingestion — happy path

- [x] 1.1 Run the daily fetch/load for the current year
- [x] 1.2 A normalized CSV exists at `datalake/YIELD_DATA/dt=<today>/` with header `Tenor,Date,Yield` and ISO dates
- [x] 1.3 In the DuckDB warehouse, `RAW_TREASURY_YIELDS` has rows keyed `(TENOR, TRADING_DATE, YIELD)` for the tracked Tenors; spot-check the latest 10Y against home.treasury.gov (10Y=4.44 on 2026-06-30)
- [x] 1.4 No row has a null Tenor/Date/Yield and none is a zero/placeholder for an empty Treasury cell
- [x] 1.5 The per-Tenor metastore advanced for each Tenor

## 2. Ingestion — gaps and bad data

- [x] 2.1 Pick a date spanning a US market holiday; confirm the holiday is **absent** (no row), not zero-filled or interpolated (2026-05-25 Memorial Day: 0 rows; 2026-05-22: 11)
- [x] 2.2 Point the fetch at a year with no data / a malformed response; confirm it raises and writes no CSV (empty + missing-column both raise ValidationError before save)

## 3. Incremental + Temporal backfill

- [x] 3.1 Re-run the daily load for the same date; confirm no duplicate `(Tenor, Trading Date)` rows (re-run wrote 0 new; count unchanged; 0 dupes)
- [x] 3.2 Start a Temporal backfill over a range of years; confirm it loads history (ran `TreasuryBackfillWorkflow` 2024–2025 via the worker → 5489 rows loaded through Temporal)
- [x] 3.3 Kill the worker mid-backfill and restart; confirm it resumes without re-loading already-loaded rows (kill+restart resumed loading further years with 0 duplicates; idempotent re-run via Temporal loaded 0 rows. Added `heartbeat_timeout=30s` so crash-resume is prompt rather than waiting out start_to_close_timeout.)

## 4. dbt models (dbt-duckdb, local)

- [x] 4.1 `YIELD_WAREHOUSE_DB=<path> dbt build --project-dir dbt/duckdb --profiles-dir dbt/duckdb` completes green; `fct_yield_curve` and `fct_2s10s_spread` materialize (PASS=18)
- [x] 4.2 `fct_yield_curve` for a date lists Tenors in maturity order (`tenor_order`); a Tenor with no value is absent (not `0`) (latest = 11 tenors, strictly ordered)
- [x] 4.3 `fct_2s10s_spread` equals `10Y − 2Y` in bp (`is_inverted` flag correct); a date missing a leg has no spread row (verified 0 single-leg spread rows)

## 5. Regression

- [ ] 5.1 Trigger the equity `stock_data_dag` and confirm the `STOCK_DATA` pipeline + dbt models still build unchanged
