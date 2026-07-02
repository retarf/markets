Depends on `treasury-yield-data` (its dbt models + ingestion activities must exist).

## 1. Ingestion event (delta on treasury-yield-data)

- [x] 1.1 Add a NATS publish to the shared ingestion activities: emit `treasury.yields.ingested {trading_date, tenors}` after a load advances the warehouse; emit nothing when zero new rows loaded — `yield_data/events.py`, wired into `load_csv`; no-op when `NATS_URL` unset (offline-safe); mock-gated (real NATS = dev-verify)
- [x] 1.2 Add the NATS endpoint config to `.env.example` (`NATS_URL`, `YIELD_WAREHOUSE_DB`, `FRONTEND_ORIGIN`)

## 2. Serving tier (Docker Compose)

- [x] 2.1 Add NATS to `docker-compose.yml` (Temporal already added by `treasury-yield-data`) — `nats:2` on 4222/8222; `docker compose config` validates
- [x] 2.2 `yields-ingestion-service` — containerize the Treasury activities + Temporal worker; wire the NATS publisher. Shared `images/services/Dockerfile` (+ `requirements.txt`) runs all three serving processes; compose services `yields-ingestion-service` (Temporal worker, `TEMPORAL_ADDRESS`/`NATS_URL`), `yields-query-service` (uvicorn :8000), `api-gateway` (uvicorn :8080→host 8090); `temporal_backfill.temporal_address()` now env-configurable; `docker compose config` validates
- [x] 2.3 `yields-query-service` (FastAPI) — endpoints: latest/by-date curve, comparison curve (resolve nearest prior Trading Date + report it), 2s10s spread over window, per-Tenor series over window; reads DuckDB dbt models directly; gaps preserved. `services/yields_query_service/`; 10 pytest + real-data smoke green
- [x] 2.4 `yields-query-service` — subscribe to `treasury.yields.ingested` (lifespan NATS consumer → broadcaster) + `/yields/stream` SSE endpoint. Broadcaster fan-out + SSE framing pytest-gated; live NATS push = dev-verify
- [x] 2.5 `api-gateway` — `services/api_gateway/`: routes `/api/yields/*` to the query service (streaming, SSE-passthrough), CORS for `FRONTEND_ORIGIN`. 5 pytest incl. real in-process proxy to the query app
- [x] 2.6 Verify the whole stack (equity + yields data + serving) comes up together — `docker compose up -d --build` brings all 8 services up; temporal `healthy` (named-volume SQLite + `operator cluster health` gate), ingestion worker polls the `yield-backfill` queue, query-service connects to NATS + serves (graceful 503 when the warehouse is absent), gateway proxies over the compose net + on host 8090. Host ports `TEMPORAL_GRPC_PORT`/`YIELDS_QUERY_PORT`/`AIRFLOW_PORT` overridable for local clashes. Live data flow (backfill→dbt→curve/SSE) is 4.1

## 3. Frontend (React + TS + Vite) — build to `design/layout.svg`

- [x] 3.1 Scaffold `frontend/` (Vite + React + TS, strict mode); `design-tokens.json` mirrored into `theme.css` (CSS variables) + `tokens.ts`. Runs as a compose `frontend` service (Vite dev on 5173)
- [x] 3.2 API client + TanStack Query against the gateway (`api/client.ts`, `api/hooks.ts`, typed `api/types.ts`); per-panel loading/error/empty handling
- [x] 3.3 Charting lib = **visx** (deliberate: ordinal-by-maturity X + shaded regions + full control over honesty/a11y cues); shared time-axis (`chartUtils.sharedDomain` + identical margins) + linked crosshair across R2/R3
- [x] 3.4 Yield Curve hero panel — maturity-ordered ordinal X; comparison control (Latest/1M/1Y **+ Custom Trading Date picker**, added in dev-verify) with dashed + hollow-square overlay (non-color); resolved-date label (verified "1Y ago (Jul 1, 2025)" and "as of Jan 18, 2006"); missing Tenor omitted + line breaks (verified vs 2006-01-18 → 30Y omitted + named)
- [x] 3.5 2s10s Spread panel — emphasized labeled "0 bp" zero line + inverted region with four non-color cues (shade + zero line + "inverted" label + below-axis)
- [x] 3.6 2Y & 10Y series panel — 2Y solid / 10Y dashed (distinguishable without color) + legend; shared time axis aligned with the spread panel
- [x] 3.7 Header control bar — Trading Date readout, comparison + window segmented controls (active = fill+weight+underline, non-color), live-status by glyph+text (connecting/live/reconnecting/offline), "not investment advice" disclosure, total-failure banner
- [x] 3.8 Panel states — loading skeleton (ghosted axes, no fake line), empty (message + Retry), partial (omit + name missing Tenor/leg; gaps as line breaks via `segmentsByGap`), error (panel-local + Retry), header banner on gateway-unreachable
- [x] 3.9 SSE live update — `useSSE` invalidates the yields query tree on `yields.ingested` → panels refetch/redraw; transient "Updated to <date>" chip; reduced-motion handled by `theme.css`
- [x] 3.10 Accessibility — visible focus rings, keyboard-movable crosshair (arrow keys on focused time-series panels), ≥24–26px control targets, tabular figures (`.num`), AA tokens

## 4. Wiring & docs

- [x] 4.1 End-to-end **fully proven in-browser**: Temporal backfill 2025–2026 = **4114 rows** → **NATS `treasury.yields.ingested`** → query-service **SSE** (indicator shows "Live") → dbt-duckdb `fct_yield_curve` + `fct_2s10s_spread` (**16 tests pass**) → gateway → **dashboard renders** the curve (Jul 1 2026, 1M 3.67…30Y ~5%), 2s10s (2Y window, 0-bp line), 2Y/10Y legs, and the comparison overlay resolves "1Y ago (Jul 1 2025)". Note: dbt-duckdb transform still run via ephemeral container (warehouse root-owned by the worker) — a persistent dbt-duckdb runner is the remaining infra nicety
- [x] 4.2 Update `README.md` architecture/flow to include the serving tier and the frontend — added two-domain intro, YIELD_DATA scope items, a dedicated STOCK_DATA vs YIELD_DATA architecture diagram (Treasury→DuckDB→dbt marts→NATS→query-service/SSE→gateway→React), a "Treasury yields serving tier" section with the verified end-to-end run steps + port-override note; frontend marked in-progress
- [x] 4.3 Tests green: frontend **8 Vitest** (format + chartUtils) + **`tsc -b` clean** + **`vite build` clean**; services **pytest** (query-service + gateway) green; yield_data **27 pytest** green
