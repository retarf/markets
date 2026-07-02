# yields-serving Specification

## Purpose
TBD - created by archiving change treasury-yields-dashboard. Update Purpose after archive.
## Requirements
### Requirement: A single API gateway fronts the yields services

All frontend HTTP traffic SHALL enter through an `api-gateway` service that routes
`/api/yields/*` to the `yields-query-service`, applies CORS for the frontend
origin, and passes through the SSE stream. The frontend SHALL NOT call the query
service directly.

#### Scenario: Frontend reaches the query service via the gateway

- **WHEN** the frontend requests `/api/yields/curve`
- **THEN** the gateway routes it to the `yields-query-service` and returns its
  response
- **AND** cross-origin requests from the frontend origin are permitted

### Requirement: The query service serves curve, spread, and series reads

The `yields-query-service` SHALL expose read endpoints that read the dbt models
directly (no separate read store), returning JSON:

- the **Yield Curve** for the latest Trading Date or a specified date, as
  maturity-ordered `(tenor, yield)` points;
- a **historical-comparison** curve for a base date and a comparison selector
  (`1M` / `1Y` / a specific Trading Date), resolving an unavailable date to the
  nearest prior available Trading Date and reporting the resolved date;
- the **2s10s Spread** series over a requested time window, in basis points;
- one or more **per-Tenor series** (e.g. `2Y`, `10Y`) over a requested window.

Responses SHALL preserve gaps (absent points, not zeros) and identify the
`trading_date` they represent.

#### Scenario: Latest curve

- **WHEN** `GET /api/yields/curve` is called with no date
- **THEN** the response is the latest Trading Date's maturity-ordered curve points
  and names that Trading Date

#### Scenario: Comparison date snapped to nearest available

- **WHEN** a comparison curve is requested `vs 1Y` and exactly one year ago was a
  Treasury non-publication day
- **THEN** the service returns the nearest prior available Trading Date's curve
- **AND** the response reports the resolved Trading Date used

#### Scenario: Spread window in basis points

- **WHEN** `GET /api/yields/spread?window=2Y` is called
- **THEN** the response is the 2s10s Spread per Trading Date over ~2 years, in
  basis points, with gaps preserved

### Requirement: The query service consumes the ingestion event and pushes SSE

The `yields-query-service` SHALL subscribe to the NATS `treasury.yields.ingested`
event and expose an **SSE** endpoint (via the gateway) that pushes an update to
connected frontends when the event arrives, carrying at least the new
`trading_date`. The stream SHALL be one-directional (server→client).

#### Scenario: Live push on new data

- **WHEN** a `treasury.yields.ingested` event for `2026-07-01` is received while a
  frontend is connected to the SSE stream
- **THEN** the service pushes an update naming `2026-07-01` to that client

#### Scenario: No client connected

- **WHEN** the event arrives with no SSE clients connected
- **THEN** the service handles it without error (no delivery required)

### Requirement: The services run on the local Docker Compose stack

The serving tier SHALL be defined in `docker-compose.yml` and SHALL start with the
local stack — the `api-gateway`, `yields-query-service`, `yields-ingestion-service`,
**NATS**, and **Temporal** services. The ingestion service SHALL host the Temporal
worker and the Treasury activities and SHALL publish the ingestion event; the
equity/Airflow services SHALL remain runnable.

#### Scenario: Stack comes up

- **WHEN** the local stack is brought up
- **THEN** the gateway, query service, ingestion service, NATS, and Temporal
  containers are running and the gateway is reachable from the frontend

