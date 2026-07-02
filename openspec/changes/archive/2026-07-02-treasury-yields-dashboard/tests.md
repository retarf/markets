# Manual smoke tests

Prerequisite: `treasury-yield-data` is built and verified (yields are in Snowflake
and the dbt curve/spread/series models materialize).

## Setup

- [ ] S.1 `.env` has the NATS endpoint, gateway/query URLs, and the frontend origin
- [x] S.2 Bring up the stack: `docker compose up -d --build` — all 9 services up (equity + Temporal + `api-gateway`, `yields-query-service`, `yields-ingestion-service`, NATS, `frontend`)
- [x] S.3 Confirm all new containers are healthy and the gateway is reachable — temporal `healthy`, gateway `/health` → `{"status":"ok"}`
- [x] S.4 Start the frontend (compose `frontend` service, Vite) — dashboard at http://localhost:5173 serves 200

## 1. Ingestion event

- [x] 1.1 Run a load that writes a new Trading Date; confirm a `treasury.yields.ingested` event is published — verified during e2e: backfill emitted events naming dates (2025-12-31, 2026-07-01) + tenor lists, captured via SSE
- [x] 1.2 Run a load that writes nothing new; confirm no event — idempotent re-ingest of 2025 loaded 0 rows; SSE stream showed only `: connected`, zero `event:` frames

## 2. Serving API (via gateway)

- [x] 2.1 `GET /api/yields/curve` returns the latest maturity-ordered curve and names the Trading Date — `2026-07-01`, 1M→30Y in tenor_order
- [x] 2.2 A comparison whose exact date is a holiday returns the nearest prior Trading Date and reports it — `vs=2025-07-04` (July 4) resolved to `2025-07-03`, 11 points
- [x] 2.3 `GET /api/yields/spread?window=2Y` returns bp values with gaps preserved — 374 points, +32→+31 bp
- [x] 2.4 Per-Tenor series endpoint returns 2Y and 10Y over the window — 374 points each
- [x] 2.5 The frontend calls only go through the gateway; CORS works — all 3 requests hit `localhost:8090` only, ACAO present

## 3. Dashboard UI

- [x] 3.1 Dashboard loads: curve hero + 2s10s panel + 2Y/10Y panel render; styling matches `design-tokens.json` (dark `#0b0e14` bg, `#4c8dff` primary, tabular figures)
- [x] 3.2 Select `vs 1Y`: a historical curve overlays (dashed + hollow-square markers, distinguishable without color) with the resolved date labeled ("1Y ago (Jul 1, 2025)")
- [x] 3.3 An inverted stretch shows all four cues — verified against a rebuilt 2022–2026 warehouse (541 inverted points, min −108 bp): 4 shaded bands + labeled "0 bp" zero line + "inverted" text + below-axis; **confirmed readable in greyscale** (grayscale(1) screenshot)
- [x] 3.4 Hover a date on the spread panel: the 2Y/10Y panel cross-highlights the same date (both at "Oct 1, 2025"); tabular tooltips — spread "+57 bp / normal", series "2Y 3.55% / 10Y 4.12% / 10Y−2Y +57 bp"
- [x] 3.5 Keyboard: focused chart shows a visible outline; ArrowRight moved the crosshair Oct 1 → Oct 3, 2025 (+57 → +55 bp)
- [x] 3.6 Force a partial case (missing Tenor): the curve breaks and names the omitted Tenor (no zero point) — **now exercisable** via the added "Custom Trading Date…" picker (ux-brief §6). Compared vs **2006-01-18** (30Y reintroduced Feb 9 2006, so blank that day): the dashed comparison overlay renders **10 hollow-square markers and breaks at 20Y — the 30Y is omitted (not zero-filled)**, the note reads "Comparison curve omits 30Y (no data at that date)", and the legend labels "as of Jan 18, 2006". (Also surfaced a real behaviour: ingestion `validate_data` rejects a whole missing *column* — see the notes to dev-ship.)
- [x] 3.7 Force a panel error (stopped `yields-query-service`): all 3 panels show a local "Couldn't load this panel" + Retry, and total failure shows the header banner + Retry (4 Retry buttons); recovers on restart. Per-panel isolation is structural (each `Panel` owns its state slot)
- [x] 3.8 The "not investment advice" disclosure is visible in every state — present in nominal + error-state screenshots

## 4. Live update (SSE) + regression

- [x] 4.1 With the dashboard open (Live), an ingestion event over NATS → the browser SSE received it, queries invalidate/redraw, and the transient "Updated to Jul 1, 2026" chip appeared (load→event proven in 1.1; event→UI proven here)
- [x] 4.2 Reduced-motion — chart redraws are instant by default (no easing animation implemented), so the update always applies instantly; the "Updated to" chip signals it regardless, and `theme.css` disables the minor CSS transitions under `prefers-reduced-motion`. (Note: the brief's "ease then snap" easing for non-reduced-motion users was not implemented — instant-only.)
- [x] 4.3 Dropped the SSE (stopped `yields-query-service` while connected): live-status flipped to "◐ Reconnecting" (glyph+text); a cold-start failure shows "○ Offline" — both by text+icon, not color alone
- [~] 4.4 Regression: trigger the equity `stock_data_dag` — **regression intent PASS (this change is innocent); equity pipeline has a separate pre-existing failure.** This change touched only `yield_data`+`services`+`frontend` (equity code byte-for-byte unchanged); all DAGs parse with **no import errors**. But triggering `stock_data_dag` fails at `get_file_params` → `TypeError: missing 1 required positional argument: 'ds'` — an **Airflow 3.1.8 incompatibility** (`ds` no longer auto-injected). Pre-existing & unrelated: today's scheduled runs failed identically; last success 2026-04-09. Belongs in its own change. dbt/snowflake models untouched (not independently compiled — needs Snowflake creds).
