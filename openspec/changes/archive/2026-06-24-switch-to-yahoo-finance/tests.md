# Manual smoke tests

## Setup

- [ ] S.1 `.env` has `DATA_SOURCE_URI` pointing at the Yahoo chart template (`.../v8/finance/chart/{ticker}?period1=0&period2=9999999999&interval=1d` — daily granularity)
- [ ] S.2 Bring up the local stack: `docker compose up -d --build`
- [ ] S.3 Confirm Snowflake creds / key files are present (`migrations/snowflake/migrate.py` has been run at least once)
- [ ] S.4 Clear any prior datalake output for today's `dt=` partition to observe a clean fetch

## 1. Fetch — happy path

- [ ] 1.1 Run the fetch for one ticker: `python src/stock_data/fetch_data/run.py --date <today> --ticker XTB.WA`
- [ ] 1.2 A file `datalake/STOCK_DATA/dt=<today>/XTB.WA.csv` exists
- [ ] 1.3 Its header is exactly `Date,Open,High,Low,Close,Volume` and dates are `YYYY-MM-DD`
- [ ] 1.4 Spot-check the latest close against finance.yahoo.com/quote/XTB.WA (raw, dividend-unadjusted)
- [ ] 1.5 No row has a null/empty O/H/L/C/V

## 2. Fetch — invalid ticker

- [ ] 2.1 Run the fetch for a bogus symbol: `... --ticker NOPE.WA`
- [ ] 2.2 The command exits with a validation error naming the ticker
- [ ] 2.3 No CSV file was written for `NOPE.WA`

## 3. Load — ticker identity preserved

- [ ] 3.1 Run the load for the fetched file: `python src/stock_data/load_data/run.py --path "/project/datalake/STOCK_DATA/dt=<today>/XTB.WA.csv"`
- [ ] 3.2 In Snowflake `RAW_STOCK_DATA`, the loaded rows have `TICKER = 'XTB.WA'` (suffix intact, not `XTB`)
- [ ] 3.3 Quality checks passed (no null fields, prices/volume > 0, HIGH >= LOW)
- [ ] 3.4 The metastore last-loaded date advanced for `XTB.WA`

## 4. End-to-end DAG

- [ ] 4.1 Trigger `stock_data_dag` in Airflow for all tickers (`XTB.WA`, `PKN.WA`, `PZU.WA`)
- [ ] 4.2 All `fetch_data` and `load_data` mapped tasks succeed
- [ ] 4.3 `dbt build` (stg → fct → mart) completes with no schema change required
- [ ] 4.4 `stg_stock_data` shows the three new tickers with their `.WA` suffix

## 5. Regression — incremental load

- [ ] 5.1 Re-run the DAG for the same date
- [ ] 5.2 No duplicate `(ticker, trading_date)` rows appear in `stg_stock_data` (dedup + metastore filter still hold)
