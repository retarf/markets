## Why

The `treasury-yield-data` change lands US Treasury yields in Snowflake and models
the Yield Curve and 2s10s Spread. This change builds the **serving + presentation
half**: the project's first frontend feature — a single-user dashboard that tracks
the 2Y and 10Y yields, the **2s10s Spread** (the recession signal), and the full
**Yield Curve** — plus the app tier that serves it.

This feature is the deliberate vehicle for standing up the serving/app tier as a
**portfolio showcase** (ADR 0002): FastAPI microservices behind an API gateway,
and **NATS + SSE** so the dashboard updates live when new yields land (ADR 0005).
Each piece is scoped to do real work, not decoration.

**Depends on `treasury-yield-data`** — it reads that change's dbt models and hooks
its ingestion activities to publish an event.

## What Changes

- **Ingestion event (delta)** — the ingestion activities from `treasury-yield-data`
  gain a NATS publish: `treasury.yields.ingested {trading_date, tenors}` after a
  load advances the warehouse.
- **Serving tier (Docker Compose)** — three FastAPI-family services:
  `api-gateway` (single ingress, CORS, SSE passthrough), `yields-query-service`
  (read endpoints for curve / spread / series, reads the dbt models directly; NATS
  consumer; SSE endpoint), `yields-ingestion-service` (hosts the Treasury activities +
  Temporal worker as a container and publishes the event). Adds **NATS** as infra.
- **React frontend** — a new `frontend/` app (React + TypeScript + Vite) rendering
  the accepted `design/layout.svg`: one dense dashboard with the Yield Curve hero
  (+ historical comparison overlay), the 2s10s Spread panel (inversion shown with
  four non-color cues), and the 2Y/10Y series panel — linked panels, honest
  empty/partial/loading/error states, SSE live update, keyboard-accessible.
- **Design tokens** — `design-tokens.json` (persisted at project root by
  `dev-design`) is wired into the frontend as the source of truth for styling.

## Capabilities

### New Capabilities

- `yields-serving`: the API gateway + query service, its read endpoints, the NATS
  `treasury.yields.ingested` event consumption, and the SSE live-update stream.
- `yields-dashboard-ui`: the React dashboard feature and its behaviour (panels,
  controls, states, accessibility) built around the accepted `layout.svg`.

### Modified Capabilities

- `treasury-yield-ingestion`: adds one requirement — publish the
  `treasury.yields.ingested` NATS event after a successful load (the hook the
  serving tier consumes).

## Impact

- **New code:** `frontend/` (React app); `services/api-gateway/`,
  `services/yields-query-service/`, `services/yields-ingestion-service/` (or
  equivalent); a NATS publisher in the ingestion activities and a consumer + SSE
  endpoint in the query service.
- **Config / infra:** `docker-compose.yml` gains gateway, query, ingestion, and
  NATS services (Temporal already added by `treasury-yield-data`); `.env.example`
  gains NATS endpoint and the gateway/query URLs and the frontend origin.
- **Unchanged:** the equity `STOCK_DATA` pipeline; the `treasury-yield-data`
  ingestion/modeling behaviour except for the added event publish.
- **External dependency:** NATS added to the local stack.
- **Design:** consumes the accepted `design/layout.svg`, `design/ux-brief.md`, and
  root `design-tokens.json` from `dev-design` (phase 1.5). This phase does not
  redraw the mockup.

## Dependency

Requires `treasury-yield-data` to be built first (this change reads its dbt models
and extends its ingestion activities).
