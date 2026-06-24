## Context

The fetch step is a CLI (`fetch_data/run.py`) invoked per ticker by an Airflow
DAG via dynamic task mapping. It currently does `requests.get(DATA_SOURCE_URI
.format(ticker=...))` against stooq.pl and saves the raw response bytes verbatim
to `datalake/STOCK_DATA/dt={ds}/{ticker}.csv`. A PySpark loader reads that CSV
with an explicit `input_schema` (`Date,Open,High,Low,Close,Volume`), derives the
Ticker from the file path, applies quality checks, and loads to Snowflake
`RAW_STOCK_DATA` with a metastore-driven incremental filter; dbt builds
`stg → fct signals → mart_return_data` on top.

A spike (`curl` with default vs browser User-Agent, against `stooq.pl` and
`stooq.com`) confirmed stooq now serves a JavaScript browser-verification
challenge instead of CSV. The same spike confirmed the Yahoo chart endpoint
(`/v8/finance/chart/XTB.WA`) returns clean JSON (currency PLN, exchange WSE) over
a plain GET with no cookie/crumb auth. See `docs/adr/0001-yahoo-finance-as-data-
provider.md` and `CONTEXT.md`.

## Goals / Non-Goals

**Goals:**
- Restore automated daily ingestion of Polish (GPW) bars without a headless
  browser.
- Confine the change to the fetch step plus two latent bug fixes; keep the
  datalake CSV contract and everything downstream untouched.
- Make the Ticker a single multi-market namespace (Yahoo symbols) to support the
  project's intended expansion to foreign markets.

**Non-Goals:**
- Re-keying or migrating any historical stooq-keyed data.
- Dividend-adjusted prices, an adj-close column, currency column, or a run-history
  table (possible later; out of scope here).
- Changing PySpark schema, the incremental-load/metastore logic, dbt models, or
  Snowflake objects.

## Decisions

- **Yahoo over stooq.** stooq's JS wall needs a headless browser (heavy, fragile,
  ToS gray area); Yahoo answers a plain GET. _Alternatives:_ stooq + Playwright
  (rejected — operational weight); a third/paid provider (rejected — key/cost,
  weaker free GPW coverage).
- **Direct chart endpoint, not `yfinance`.** Keeps the existing `requests`
  "GET → transform → save" shape, adds no `pandas`/transitive deps into the env
  that already had Airflow/PySpark conflicts (commit `6ca5421`). _Trade-off:_ we
  own crumb/cookie handling if Yahoo adds it; today none is required.
- **Yahoo symbol as canonical Ticker.** One namespace across markets; foreign
  instruments are just another symbol. _Alternative:_ provider-independent code
  + mapping table (rejected — extra layer, and a per-market code scheme to
  invent). _Trade-off:_ Yahoo lock-in in the warehouse identity (recorded in the
  ADR).
- **Raw `quote[]` OHLCV.** Internally consistent and matches `input_schema` with
  zero downstream change; an adjusted close can fall outside raw `[low, high]`
  and break the `low_greater_than_high` / `greater_than_zero` quality checks.
  _Trade-off:_ SMA differs slightly from the old dividend-adjusted stooq series.
- **Full daily history via `period1=0&period2=<far-future>&interval=1d` per
  run.** Mirrors the old full-history-every-day behaviour; the metastore
  incremental filter still decides what is new. Trivial at ~250 bars/yr/ticker
  and bulletproof for backfill/outage gaps. _Note (empirical):_ the original plan
  used `range=max`, but Yahoo silently downsamples `range=max` to `1mo`
  granularity; `period1/period2` is required to keep `1d`.
- **Simple `User-Agent` (`Mozilla/5.0`).** The default python-requests UA is
  rejected, but a *full* desktop-browser UA gets a persistent HTTP 429 (the API
  treats it as a browser scraping the API). A minimal client UA returns 200
  reliably (verified by interleaved A/B requests).
- **`Path.stem` for ticker extraction.** `name.split('.')[0]` truncates
  `XTB.WA.csv` to `XTB`, silently dropping the market suffix that is now part of
  the identity. `stem` yields `XTB.WA`.

## Risks / Trade-offs

- [Yahoo endpoint is unofficial and may change shape or add auth] → isolated in
  one function; validation fails loudly on unexpected/empty payloads rather than
  writing garbage.
- [Yahoo may rate-limit/challenge datacenter IPs (as seen when probing stooq)] →
  only 2–3 tickers/day; if it appears, revisit `yfinance` (handles crumb/cookie)
  as a fallback.
- [Yahoo `quote` arrays can contain interleaved nulls on holidays/half-days] →
  null bars are dropped before write so quality checks stay valid.
- [Ticker identity change orphans legacy `ORL`/`XTB`/`PZU` rows] → accepted;
  negligible existing history.

## Migration Plan

1. Land code changes and repoint `DATA_SOURCE_URI` (`.env`, `.env.example`) to the
   Yahoo chart URL template.
2. Run the fetch + load for the new symbols; new bars key on `XTB.WA` etc.
3. Optionally drop legacy stooq-keyed rows from `RAW_STOCK_DATA` (cosmetic; dedup
   keys on `(ticker, trading_date)` so they simply never match new data).
4. Rollback: revert the code change and repoint `DATA_SOURCE_URI` to stooq (note
   stooq remains broken — rollback restores the prior code, not a working feed).

## Open Questions

- None blocking. If Yahoo later adds crumb/cookie auth to the chart endpoint,
  re-evaluate `yfinance`.
