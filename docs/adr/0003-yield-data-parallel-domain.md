# US Treasury yields as a parallel YIELD_DATA domain, not the equity model

## Context

The warehouse is built entirely around **equities**: the raw grain is a
**Daily Bar** — `(Ticker, Trading Date)` OHLCV — sourced from Yahoo Finance,
landed under `datalake/STOCK_DATA/`, and gated by quality checks including
`greater_than_zero_quality_check`, which **rejects any row with `volume <= 0`**
(`src/stock_data/load_data/quality_checks.py`).

We are adding **US Treasury yields** (10Y, 2Y, and the full constant-maturity
curve) to drive the first frontend feature. A yield is structurally unlike a
Daily Bar: it is a **rate in percent** for a **Tenor** on a Trading Date — no
open/high/low/close, no volume — and it comes from the **U.S. Treasury** feed,
not Yahoo. Forcing it through the equity path would mean inventing OHLC values,
setting a fake `volume`, and disabling the volume quality check.

The datalake is already namespaced (`datalake/STOCK_DATA/`), which anticipated
additional domains.

## Decision

Model Treasury yields as a **separate, parallel domain** — provisional name
`YIELD_DATA`:

- **Provider**: the U.S. Department of the Treasury *Daily Treasury Par Yield
  Curve Rates* (constant-maturity / CMT) feed — a keyless public CSV and the
  primary source FRED republishes as its `DGS*` series. A per-asset-class Data
  Provider distinct from Yahoo.
- **Grain / identity**: `(Tenor, Trading Date) → Yield %`. `Tenor` (e.g. `2Y`,
  `10Y`) is the Treasury analogue of a Ticker.
- **Own everything**: own datalake namespace, own raw table, own Treasury-feed
  ingestion, own quality checks (yield-appropriate — no volume rule), own dbt
  models (curve snapshot, 2s10s Spread, per-Tenor series).
- **Reuse patterns, not schema**: keep the proven metastore-driven incremental
  load, dated datalake layout, and validate-before-write discipline — but do not
  share the equity table shape.

## Considered options

- **Reuse Ticker / Daily Bar** — model each series as a pseudo-Ticker (`US10Y`)
  with the yield in `close` and `volume = 1`. Reuses code immediately but
  corrupts the glossary (a Yield is not a Daily Bar), forces fake OHLC, and
  requires weakening the volume quality check for everyone. Rejected.
- **Generalize STOCK_DATA into a unified "instrument observation" model** that
  both equities and yields specialize. Cleanest long term, but a large refactor
  of working, tested equity code *before* shipping the first feature. Deferred —
  the parallel domain can be unified later if a third asset class justifies it.

## Consequences

- Two domains now coexist; some pattern duplication (ingestion scaffolding,
  metastore) is accepted in exchange for schema honesty and isolation — a bug in
  yields cannot touch the equity pipeline.
- `CONTEXT.md` gains `Yield`, `Tenor`, `Yield Curve`, `2s10s Spread`; `Data
  Provider` becomes per-asset-class (Yahoo for equities, U.S. Treasury for yields).
- A future unification (the generalize option) remains open but is now a
  deliberate, separate decision rather than a default.
- The `(Tenor, Trading Date)` key mirrors the equity `(Ticker, Trading Date)`
  key, so downstream analytics and the serving API stay conceptually consistent.
