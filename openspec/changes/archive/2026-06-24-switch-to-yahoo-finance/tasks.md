## 1. Ticker universe & identity

- [x] 1.1 Update `airflow/src/stock_data/constants.py` `TICKER_LIST` to Yahoo symbols `["XTB.WA", "PKN.WA", "PZU.WA"]`
- [x] 1.2 Remove the stale `TICKER_LIST` copies in `src/stock_data/fetch_data/run.py` and `src/stock_data/fetch_data/operations.py`; import the canonical one where needed
- [x] 1.3 Fix `get_ticker_from_path` in `src/stock_data/load_data/operations.py` to use `Path(path).stem` so `XTB.WA.csv` → `XTB.WA`
- [x] 1.4 Fix/remove `get_ticker_from_file_name` in `src/stock_data/fetch_data/utils.py` so dotted symbols keep their suffix (or drop it if unused)

## 2. Yahoo fetch

- [x] 2.1 Repoint `DATA_SOURCE_URI` in `.env.example` (and `.env`) to the Yahoo chart URL template `https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1=0&period2=9999999999&interval=1d` (daily; `range=max` downsamples to monthly)
- [x] 2.2 Rewrite `fetch_data(ticker)` in `fetch_data/operations.py` to GET the Yahoo endpoint with a simple `User-Agent` (`Mozilla/5.0`; a full browser UA triggers HTTP 429) and return the parsed JSON
- [x] 2.3 Parse `chart.result[0]` into rows: `timestamp[]` → ISO `Date`, `indicators.quote[0]` → open/high/low/close/volume
- [x] 2.4 Drop rows where any of open/high/low/close/volume is null
- [x] 2.5 Serialise rows to CSV with header `Date,Open,High,Low,Close,Volume` and write to the existing dated datalake path (preserve the contract)

## 3. Validation

- [x] 3.1 Rewrite `validate_data` to raise `ValidationError(ticker)` when `chart.error` is non-null, `chart.result` is empty/null, or there are no timestamps
- [x] 3.2 Remove the `NO_DATA_ROW` / `"Brak danych"` byte check and unused constants
- [x] 3.3 Ensure validation runs before the file is written so no CSV is produced for an invalid ticker

## 4. Verification (live — handled in dev-verify, see tests.md)

- [ ] 4.1 Run the fetch CLI locally for `XTB.WA` and confirm a well-formed CSV lands in the datalake
- [ ] 4.2 Run the PySpark load against the new CSV and confirm rows load with `TICKER = "XTB.WA"` (suffix intact) and quality checks pass
- [ ] 4.3 Run the Airflow `stock_data_dag` end to end for all tickers and confirm dbt models build unchanged
- [ ] 4.4 Confirm an invalid symbol fails only its own mapped task
