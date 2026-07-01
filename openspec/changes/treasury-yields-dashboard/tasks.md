Depends on `treasury-yield-data` (its dbt models + ingestion activities must exist).

## 1. Ingestion event (delta on treasury-yield-data)

- [ ] 1.1 Add a NATS publish to the shared ingestion activities: emit `treasury.yields.ingested {trading_date, tenors}` after a load advances the warehouse; emit nothing when zero new rows loaded
- [ ] 1.2 Add the NATS endpoint config to `.env.example` (and `.env`)

## 2. Serving tier (Docker Compose)

- [ ] 2.1 Add NATS to `docker-compose.yml` (Temporal already added by `treasury-yield-data`)
- [ ] 2.2 `yields-ingestion-service` — containerize the Treasury activities + Temporal worker; wire the NATS publisher
- [ ] 2.3 `yields-query-service` (FastAPI) — endpoints: latest/by-date curve, comparison curve (resolve nearest prior Trading Date + report it), 2s10s spread over window, per-Tenor series over window; read dbt models directly; preserve gaps in responses
- [ ] 2.4 `yields-query-service` — subscribe to `treasury.yields.ingested`; expose an SSE endpoint that pushes updates to connected clients
- [ ] 2.5 `api-gateway` — route `/api/yields/*` to the query service, CORS for the frontend origin, SSE passthrough
- [ ] 2.6 Verify the whole stack (equity + yields data + serving) comes up together

## 3. Frontend (React + TS + Vite) — build to `design/layout.svg`

- [ ] 3.1 Scaffold `frontend/` (Vite + React + TS, strict mode); wire root `design-tokens.json` into styling (CSS variables / Tailwind theme)
- [ ] 3.2 API client + server-state layer (e.g. TanStack Query) against the gateway; typed responses; loading/error/empty handling
- [ ] 3.3 Choose the charting lib (visx or Recharts) deliberately; set up the shared time-axis + linked-crosshair primitives
- [ ] 3.4 Yield Curve hero panel — maturity-ordered X; comparison control (Latest/1M/1Y/custom) with historical overlay distinguishable without color; resolved-date label
- [ ] 3.5 2s10s Spread panel — emphasized labeled zero line + inverted region with four non-color cues (shade + zero line + "inverted" label + below-axis)
- [ ] 3.6 2Y & 10Y series panel — two legs distinguishable without color; shared time axis with the spread panel
- [ ] 3.7 Header control bar — Trading Date readout, comparison control, time-window control (active state non-color), live-status (connected/reconnecting/offline by text+icon), "not investment advice" disclosure
- [ ] 3.8 Panel states — loading skeleton (no fake line), empty (next action), partial (omit + name missing Tenor; gaps as breaks), error (panel-local + Retry), plus the header total-failure banner
- [ ] 3.9 SSE live update — subtle redraw + transient "Updated to <date>" chip; reduced-motion instant swap still signalled
- [ ] 3.10 Accessibility — visible focus rings, keyboard-movable crosshair, ≥24px targets, tabular figures, AA contrast (tokens already AA)

## 4. Wiring & docs

- [ ] 4.1 End-to-end: a new load → NATS event → query endpoints → dashboard renders → SSE live update
- [ ] 4.2 Update `README.md` architecture/flow to include the serving tier and the frontend
- [ ] 4.3 Frontend + service tests (Vitest/Testing Library for UI; pytest for services) green; lint/typecheck clean
