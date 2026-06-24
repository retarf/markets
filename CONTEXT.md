# Markets

Domain language for the market-data pipeline that ingests stock prices and
derives trading signals. First market is Polish (GPW); the design intentionally
leaves room for foreign markets. This file is a glossary only — no
implementation details.

## Language

**Ticker**:
The identity of a listed instrument, stored in the warehouse and used as part
of the `(ticker, trading_date)` key. Uses the Yahoo Finance symbol notation
(e.g. `PKN.WA` for Orlen, `XTB.WA`, and later e.g. `AAPL`, `BMW.DE`). One shared
namespace across every market, chosen so foreign instruments are just another
symbol.
_Avoid_: code, instrument id. Note the GPW-native code (`PKN`) is **not** the
Ticker on its own — the market suffix (`.WA`) is part of it.

**Data Provider**:
The upstream source of market data. Yahoo Finance. Because the Ticker uses
Yahoo's symbol notation, the provider is part of the warehouse identity by
design (see ADR). Previously stooq.pl (abandoned).
_Avoid_: data source, feed, API (when you mean the provider specifically).

**Trading Date**:
The business date of a single Daily Bar. The unit of incremental progress —
the metastore tracks the latest loaded Trading Date per Ticker.
_Avoid_: date, day, timestamp.

**Daily Bar**:
One Trading Date's open/high/low/close/volume for one Ticker. The grain of the
raw data.
_Avoid_: row, record, candle, OHLCV (informal).

**Datalake**:
The dated local file store where fetched Daily Bars land as CSV before loading,
partitioned by capture date (`dt=YYYY-MM-DD`).
_Avoid_: staging, landing zone.

## Example dialogue

> **Dev:** What's the Ticker for Orlen?
> **Domain:** `PKN.WA` — the Yahoo symbol, suffix included. That's what we store.
> **Dev:** Why carry the `.WA`? Isn't `PKN` enough on GPW?
> **Domain:** Because the same pipeline will pull foreign markets. `.WA` is
> Warsaw, `.DE` is Frankfurt, bare symbols are US. One namespace, no per-market
> code scheme.
> **Dev:** So adding a German stock is just a new Ticker like `BMW.DE`?
> **Domain:** Exactly. No mapping table, no new identity rules.
