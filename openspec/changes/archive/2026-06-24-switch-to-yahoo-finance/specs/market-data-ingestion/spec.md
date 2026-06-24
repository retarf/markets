## ADDED Requirements

### Requirement: Daily bars are fetched from Yahoo Finance

The system SHALL fetch daily OHLCV bars from the Yahoo Finance chart endpoint
(`query1.finance.yahoo.com/v8/finance/chart/{symbol}`) using a plain HTTP GET
with a simple `User-Agent`, requesting the full available history at daily
interval via `period1=0&period2=<far-future>&interval=1d`. The Provider Symbol
sent in the request SHALL be the Ticker.

#### Scenario: Successful fetch for a listed instrument

- **WHEN** the fetch runs for Ticker `PKN.WA`
- **THEN** the system requests the Yahoo chart endpoint for `PKN.WA` with daily
  interval and full history
- **AND** receives an HTTP 200 JSON response containing `chart.result[0]` whose
  `meta.dataGranularity` is `1d`

#### Scenario: No headless browser is used

- **WHEN** the fetch makes its request
- **THEN** it uses only an HTTP client (no headless browser / JS execution)

### Requirement: Ticker identity is the Yahoo symbol

The canonical Ticker stored in the warehouse SHALL be the Yahoo Finance symbol,
including its market suffix (e.g. `XTB.WA`, `PKN.WA`, `PZU.WA`). The configured
ticker universe SHALL be defined in exactly one place and SHALL list Yahoo
symbols.

#### Scenario: Dotted symbol keeps its suffix end to end

- **WHEN** a bar for `XTB.WA` is fetched, written to `XTB.WA.csv`, and loaded
- **THEN** the Ticker derived from the file path is `XTB.WA` (the market suffix
  is preserved, not truncated to `XTB`)

#### Scenario: Single source of truth for the ticker universe

- **WHEN** the configured list of tickers is read
- **THEN** it resolves to a single canonical definition listing Yahoo symbols
  (`XTB.WA`, `PKN.WA`, `PZU.WA`), with no conflicting copies elsewhere

### Requirement: Stored bars use raw quote prices

The system SHALL store the raw `indicators.quote[0]` open/high/low/close/volume
values from the Yahoo response (split-adjusted, dividend-unadjusted). Bars whose
open, high, low, close, or volume is null SHALL be dropped before writing.

#### Scenario: Incomplete bar is dropped

- **WHEN** the Yahoo response contains a trading date whose close or volume is
  null
- **THEN** that bar is excluded from the written CSV

#### Scenario: Prices are internally consistent

- **WHEN** a bar is written
- **THEN** its open/high/low/close all come from the same raw `quote[]` series
  (no adjusted close substituted into the OHLC tuple)

### Requirement: Datalake CSV contract is preserved

The fetch SHALL write one CSV file per Ticker per run with a header row and
columns `Date,Open,High,Low,Close,Volume`, ISO dates (`YYYY-MM-DD`), to the
dated datalake path. The contract SHALL match the existing PySpark
`input_schema` so downstream loading, dbt, and Snowflake are unaffected.

#### Scenario: Output matches the existing schema

- **WHEN** a fetched file is read by the PySpark loader with the existing
  `input_schema`
- **THEN** all columns parse correctly and no schema change is required

### Requirement: Fetch validation detects no-data and error responses

The system SHALL reject a Yahoo response that contains no usable data — a
non-null `chart.error`, an empty or null `chart.result`, or no timestamps — by
raising a validation error for that Ticker. The legacy `"Brak danych"` byte
check SHALL be removed.

#### Scenario: Unknown or delisted symbol

- **WHEN** the fetch requests a symbol Yahoo does not recognise and the response
  carries `chart.error` or an empty `result`
- **THEN** the system raises a validation error naming the Ticker
- **AND** no CSV file is written for that Ticker

#### Scenario: One bad Ticker does not abort the others

- **WHEN** the fetch fails validation for one Ticker in a dynamically mapped run
- **THEN** only that Ticker's mapped task fails; the other Tickers proceed
