# Markets

Domain language for the market-data pipeline that ingests market data and
derives trading signals. The first asset class is equities (first market Polish,
GPW); a second asset class, US Treasury yields, is being added. The design
intentionally leaves room for more markets and asset classes. This file is a
glossary only — no implementation details.

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
The upstream source of market data, chosen per asset class. Equities come from
Yahoo Finance (its symbol notation is the Ticker, so the provider is part of the
warehouse identity by design — see ADR). US Treasury yields come from the
**U.S. Department of the Treasury** (the official *Daily Treasury Par Yield Curve
Rates* / constant-maturity feed), a keyless public source. Previously stooq.pl
(abandoned).
_Avoid_: data source, feed, API (when you mean the provider specifically).

**Yield**:
The annualized rate of return on a US Treasury of a given Tenor on a given
Trading Date, expressed in percent. The unit of the Treasury asset class — a
rate, **not** a price and **not** a Daily Bar (no open/high/low/close, no
volume). Warehouse identity is `(Tenor, Trading Date)`.
_Avoid_: price, rate (unqualified), interest.

**Tenor**:
The standardized time-to-maturity label of a constant-maturity Treasury Yield
(e.g. `3M`, `2Y`, `5Y`, `10Y`, `30Y`). The Treasury analogue of a Ticker — it
identifies *which* yield, independent of date.
_Avoid_: maturity date, duration, term.

**Yield Curve**:
The cross-section of Yields across every Tenor on a single Trading Date — yield
plotted against Tenor. Normal when it slopes up (long > short), *inverted* when
short exceeds long.
_Avoid_: term structure (informal here), rate curve.

**2s10s Spread**:
The 10Y Yield minus the 2Y Yield on a Trading Date. Negative means the curve is
inverted at that point — a widely watched recession signal. A derived series,
not raw data.
_Avoid_: spread (unqualified), 10-2, curve spread.

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
