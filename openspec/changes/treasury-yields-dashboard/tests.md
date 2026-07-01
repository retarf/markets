# Manual smoke tests

Prerequisite: `treasury-yield-data` is built and verified (yields are in Snowflake
and the dbt curve/spread/series models materialize).

## Setup

- [ ] S.1 `.env` has the NATS endpoint, gateway/query URLs, and the frontend origin
- [ ] S.2 Bring up the stack: `docker compose up -d --build` (equity + Temporal from `treasury-yield-data`, plus `api-gateway`, `yields-query-service`, `yields-ingestion-service`, NATS)
- [ ] S.3 Confirm all new containers are healthy and the gateway is reachable
- [ ] S.4 Start the frontend dev server (`npm run dev` in `frontend/`) or its container; open the dashboard URL

## 1. Ingestion event

- [ ] 1.1 Run a load that writes a new Trading Date; confirm a `treasury.yields.ingested` event is published to NATS (naming the date + tenors)
- [ ] 1.2 Run a load that writes nothing new; confirm no event is published

## 2. Serving API (via gateway)

- [ ] 2.1 `GET /api/yields/curve` returns the latest maturity-ordered curve and names the Trading Date
- [ ] 2.2 A `vs 1Y` comparison whose exact date is a holiday returns the nearest prior Trading Date and reports the resolved date
- [ ] 2.3 `GET /api/yields/spread?window=2Y` returns bp values with gaps preserved
- [ ] 2.4 Per-Tenor series endpoint returns 2Y and 10Y over the window
- [ ] 2.5 The frontend calls only go through the gateway (not the query service directly); CORS works

## 3. Dashboard UI

- [ ] 3.1 Dashboard loads: curve hero + 2s10s panel + 2Y/10Y panel render; styling matches `design-tokens.json`
- [ ] 3.2 Select `vs 1Y`: a historical curve overlays, distinguishable without color, with the resolved date labeled
- [ ] 3.3 An inverted stretch shows all four cues (shade + labeled zero line + "inverted" + below-axis); readable in greyscale
- [ ] 3.4 Hover a date on the spread panel: the 2Y/10Y panel cross-highlights the same date; tooltip shows tabular figures (2-dec %, bp)
- [ ] 3.5 Keyboard: Tab shows a visible focus ring; arrow keys move the crosshair
- [ ] 3.6 Force a partial case (missing Tenor): the curve breaks and names the omitted Tenor (no zero point)
- [ ] 3.7 Force a panel error (stop the query service): the panel shows a local error + Retry; other panels remain; total failure shows the header banner + Retry
- [ ] 3.8 The "not investment advice" disclosure is visible in every state

## 4. Live update (SSE) + regression

- [ ] 4.1 With the dashboard open, run a load that writes a new Trading Date; the panels redraw to it and a transient "Updated to <date>" indicator appears
- [ ] 4.2 With `prefers-reduced-motion` on, the update applies instantly (no animation) but is still signalled
- [ ] 4.3 Drop the SSE connection (stop the query service); the live-status shows reconnecting/offline by text+icon, not color alone
- [ ] 4.4 Regression: trigger the equity `stock_data_dag` and confirm the `STOCK_DATA` pipeline + dbt models still build unchanged
