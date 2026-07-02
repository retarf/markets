## Context

`treasury-yield-data` lands US Treasury yields in Snowflake and models the Yield
Curve, the 2s10s Spread, and per-Tenor series in dbt. This change adds the serving
tier and the first frontend feature on top of those models — and, as a deliberate
portfolio showcase, the app platform beneath it.

There is no serving tier or frontend in the repo yet. The visual design is already
accepted (phase 1.5): the mockup is `design/layout.svg` (regenerable via
`design/gen.py`), the UX authority is `design/ux-brief.md`, and the theme is the
root `design-tokens.json`. This phase specs the change *around* that design and
does not redraw it. See ADRs 0002 and 0005 and `CONTEXT.md`.

## Goals / Non-Goals

**Goals:**
- Stand up the serving tier (gateway + query + ingestion services, NATS) where
  each piece does real work.
- Ship the React dashboard to the accepted design, with live SSE updates and
  honest states.
- Add exactly one behaviour to ingestion: publish the ingestion event.

**Non-Goals:**
- Ingestion/modeling itself (owned by `treasury-yield-data`).
- Multi-user / auth (single user for now).
- A separate read store / cache for the query service (the dataset is tiny; read
  dbt models directly). Predictive/forecasting features.

## Decisions

- **Gateway + query + ingestion services, NATS event, SSE** (ADR 0005). The
  ingestion side publishes `treasury.yields.ingested {trading_date, tenors}`; the
  query side consumes it and pushes SSE so the dashboard redraws live. This makes
  NATS a real cross-service loop rather than decoration. _Rejected:_ one combined
  service (collapses the event into an in-process call); no NATS (adequate for a
  daily dataset but no live story — the showcase goal). **SSE, not WebSocket** —
  updates are one-directional and low-frequency.
- **Query service reads dbt models directly.** The yield dataset is a few thousand
  rows; a separate read store / cache is unwarranted. The NATS event drives SSE
  push (and optional in-memory refresh), not a materialized projection.
- **Comparison date resolves to nearest prior available Trading Date**, and the
  response reports the resolved date — honest handling of data gaps at the API
  boundary so the UI never silently mislabels an overlay.
- **React + TS + Vite, token-driven.** `design-tokens.json` is the single source of
  truth wired into styling (CSS variables / Tailwind theme) on this first frontend
  change. Charting: the curve needs an ordinal-by-maturity X axis and the spread
  needs shaded regions — **visx** (D3 scales, full control) or **Recharts**;
  `frontend-engineer` picks one deliberately (candle-oriented libs like
  lightweight-charts fit worse here). Honesty rules from the direction note are
  binding: gaps as gaps, missing Tenor omitted, inversion never color-alone.

## Risks / Trade-offs

- [NATS/gateway are heavy for one daily dataset] → justified only by the live-push
  loop + service decoupling; if live push is ever dropped, revisit (ADR 0005).
- [The event publish couples this change back into ingestion] → confined to a
  single added requirement/hook; ingestion logic itself is unchanged.
- [Frontend charting complexity (ordinal-by-maturity curve + shaded inversion)] →
  chart lib chosen deliberately; the accepted `layout.svg` fixes the target.

## Migration Plan

1. Add the NATS endpoint, gateway/query URLs, and the frontend origin to `.env` /
   `.env.example`.
2. Add the event publish to the shared ingestion activities (from
   `treasury-yield-data`).
3. Bring up gateway + query + ingestion + NATS in Docker Compose (Temporal already
   present); wire the event → SSE loop.
4. Scaffold `frontend/`, wire `design-tokens.json`, build the dashboard to
   `design/layout.svg`, point it at the gateway.
5. Rollback: additive and isolated — remove the new services and the frontend, and
   drop the event publish; `treasury-yield-data` and the equity pipeline are
   unaffected.

## Open Questions

- Default time-window for the spread/series panels (`2Y` proposed in the brief) —
  confirm against real data density.
- visx vs Recharts — `frontend-engineer` to finalize in build.
