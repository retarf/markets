# Event-driven serving tier: API gateway + NATS + SSE live push

## Context

[ADR 0002](0002-react-research-platform-over-fastapi.md) established a React
frontend served by FastAPI microservices on Docker Compose. The first feature
(Treasury yields & yield curve) makes the serving tier concrete, and — as a
deliberate portfolio showcase of distributed-systems patterns — we want the
services wired with an API gateway and an event bus (NATS), not a single
monolithic API.

The risk is decoration: a once-a-day dataset does not *need* an event bus, and
NATS sitting between one producer and one consumer that could be a function call
is worse than no NATS at all. So the tier is designed around an event that
actually crosses service boundaries and drives visible behavior.

## Decision

A three-service serving tier behind a gateway, connected by a NATS event:

- **`api-gateway`** — single ingress; routes `/api/yields/*`, handles CORS and
  SSE passthrough, and holds the (future) auth slot.
- **`yields-query-service`** (FastAPI) — read API (latest curve, curve-by-date,
  2s10s series, per-Tenor series); reads the Snowflake **dbt** models directly
  (the dataset is tiny — no separate read store). Also a **NATS consumer** and an
  **SSE endpoint**.
- **`yields-ingestion-service`** — houses the Treasury fetch/validate/load activities
  (shared by the Airflow daily task and the Temporal backfill worker) and
  **publishes** `treasury.yields.ingested {trading_date, tenors}` after a
  successful load.
- **NATS** carries that event; on receipt the query service refreshes and **pushes
  an SSE update to the React frontend**, so the curve/spread redraw the moment new
  data lands.

The event therefore decouples ingestion from serving *and* drives a live UI
update — a real loop, not a placeholder.

## Considered options

- **Single combined yields-service behind the gateway** — fewer moving parts, but
  the NATS producer and consumer collapse into one process, so the event loop is
  unconvincing (an in-process call in disguise). Rejected for the showcase.
- **No NATS; query service reads Snowflake directly on request** — leanest and
  perfectly adequate for a daily dataset, but no event-driven story and no live
  push. Rejected given the portfolio goal (revisit if the goal changes).
- **Dedicated notification/SSE service** — more "correct" microservices split but
  over-engineered for one feature; folded into the query service for now.

## Consequences

- New infrastructure: NATS plus a gateway in Docker Compose; two app services
  where one would functionally do. Justified by the decoupling + live-push
  behavior, not by data volume.
- The `treasury.yields.ingested` event becomes a **published contract**; future
  consumers (other asset classes, alerting, cache warmers) can subscribe without
  touching ingestion — the main upside of the bus.
- SSE (not WebSocket) is chosen: updates are one-directional server→client and
  low-frequency, so SSE is simpler and sufficient.
- If the event ever has only one possible consumer forever and live push is
  dropped, NATS should be reconsidered to avoid decorative infrastructure.
