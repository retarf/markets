# Yahoo Finance as data provider; Yahoo symbol as canonical Ticker

## Context

The pipeline originally fetched daily OHLCV from **stooq.pl** via a plain
`requests.get` against `/q/d/l/?s={ticker}&i=d`. stooq has since put automated
downloads behind a **JavaScript browser-verification wall** (confirmed on both
`stooq.pl` and `stooq.com`): a default User-Agent gets HTTP 404, a browser-like
User-Agent gets a JS challenge page instead of CSV. Passing it would require
running a headless browser (Playwright/Selenium) in the fetch step — heavy,
fragile, and hostile to a daily scheduled DAG. The old `validate_data` only
detected stooq's `"Brak danych"` payload, so the new challenge response would
flow downstream undetected.

## Decision

Switch the Data Provider to **Yahoo Finance**, fetched via its public chart
endpoint (`query1.finance.yahoo.com/v8/finance/chart/{symbol}`) with a plain
`requests` GET — no headless browser, no library dependency. We store raw
`quote[]` OHLCV (split-adjusted, dividend-unadjusted), pull `range=max` each run,
and let the existing metastore-driven incremental load decide what is new. The
CSV contract (`Date,Open,High,Low,Close,Volume`) is preserved, so PySpark, dbt,
and Snowflake are untouched.

The **canonical Ticker stored in the warehouse is the Yahoo symbol itself**,
suffix included (`PKN.WA`, `XTB.WA`, `PZU.WA`), rather than a GPW-native code
(`PKN`) or a provider-independent identity with a mapping table.

## Considered options

- **Stay on stooq with a headless browser** — preserves the exact CSV format but
  adds a browser engine to the pipeline and remains a ToS gray area.
- **Provider-independent canonical Ticker + symbol mapping** — cleanest
  decoupling, but adds a mapping layer and a per-market code scheme.

## Consequences

- **Provider lock-in is accepted by design**: Yahoo's symbol notation is the
  warehouse identity. The upside is one symbol namespace across every market
  Yahoo covers, so adding foreign instruments (e.g. `AAPL`, `BMW.DE`) is just a
  new Ticker — supporting the project's multi-market goal. The downside is that
  a future provider switch would require re-keying historical data.
- Yahoo's chart endpoint is unofficial and may change; it currently needs no
  cookie/crumb auth.
- SMA signals shift slightly versus the old stooq series, which was
  dividend-adjusted; ours are not.
- Legacy rows keyed `ORL` (a stooq-ism for Orlen) do not reconcile with the new
  `PKN.WA`; acceptable given negligible existing history.
