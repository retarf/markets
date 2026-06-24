## Why

The data provider, stooq.pl, has put automated CSV downloads behind a JavaScript
browser-verification wall — a plain `requests.get` now receives an anti-bot
challenge page instead of data, so the daily fetch silently produces garbage
(the old validation only recognised stooq's `"Brak danych"` payload). Passing the
wall would require running a headless browser in the pipeline. We switch the
provider to Yahoo Finance, which serves daily OHLCV over a plain HTTP GET and
covers many markets under one symbol namespace.

## What Changes

- Replace the stooq fetch with a call to the **Yahoo Finance chart endpoint**
  (`query1.finance.yahoo.com/v8/finance/chart/{symbol}`) via plain `requests`,
  pulling full daily history (`period1=0&period2=<far-future>&interval=1d`) per
  run and parsing `indicators.quote[]` JSON into the existing CSV contract.
  (Note: `range=max` was the original plan but Yahoo downsamples it to monthly;
  `period1/period2` is required to keep daily granularity.)
- **BREAKING (warehouse identity):** the canonical `TICKER` becomes the **Yahoo
  symbol** (suffix included): `XTB.WA`, `PKN.WA`, `PZU.WA`. Legacy stooq-keyed
  rows (`XTB`, `ORL`, `PZU`) no longer reconcile.
- Store **raw `quote[]` OHLCV** (split-adjusted, dividend-unadjusted); drop
  null/incomplete bars before writing.
- Rewrite `validate_data` to detect Yahoo's no-data / error responses
  (`chart.error`, empty `result`) instead of the `"Brak danych"` byte check.
- Fix `get_ticker_from_path` to use `Path.stem` so dotted symbols keep their
  market suffix (`XTB.WA.csv` → `XTB.WA`, not `XTB`).
- Consolidate the three drifted `TICKER_LIST` definitions into the single
  canonical `airflow/src/stock_data/constants.py`, updated to Yahoo symbols.
- The datalake CSV contract (`Date,Open,High,Low,Close,Volume`) is **preserved**,
  so PySpark `input_schema`, the incremental load, dbt models, and Snowflake are
  unchanged.

## Capabilities

### New Capabilities

- `market-data-ingestion`: how daily stock bars are fetched from the Data
  Provider, identified by Ticker, validated, and landed in the datalake as CSV.

### Modified Capabilities

<!-- None: openspec/specs/ is empty; this change bootstraps the capability spec. -->

## Impact

- **Code:** `src/stock_data/fetch_data/operations.py` (fetch + validate),
  `src/stock_data/fetch_data/run.py` and `.../utils.py` (stale TICKER_LIST /
  ticker helpers), `src/stock_data/load_data/operations.py`
  (`get_ticker_from_path`), `airflow/src/stock_data/constants.py` (TICKER_LIST).
- **Config:** `.env` / `.env.example` `DATA_SOURCE_URI` repointed to the Yahoo
  chart URL template.
- **Unchanged:** PySpark schema, incremental load + metastore, dbt, Snowflake.
- **External dependency:** Yahoo Finance public chart endpoint (unofficial, no
  auth required today); stooq dependency removed.
