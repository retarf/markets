# Expand scope to a single-user research platform: React frontend over FastAPI microservices

## Context

The project was deliberately scoped as a **batch, warehouse-first** data pipeline
(Yahoo → Datalake → Airflow/PySpark → Snowflake → dbt), and the README explicitly
listed a **public API and a frontend application as out of scope**. The pipeline
ends at dbt analytical models and trading signals; there is no way to *look at*
the results other than querying Snowflake directly.

We now want a way to explore prices, Daily Bars, and trading signals
interactively — an **analytical & research platform for a single user (for now)**:
pick Tickers, adjust indicator/signal parameters, compare instruments, read
charts and dense tables. React cannot read Snowflake directly, so something must
serve the warehouse's data as an API.

This is a real scope change, not an implementation detail, so it is recorded here.

## Decision

Extend the pipeline with a serving and presentation tier:

- **FastAPI microservices** run on the existing Docker Compose stack (for now) and
  query Snowflake/dbt models, returning JSON. Python-native, consistent with the
  rest of the stack.
- A **React + TypeScript + Vite** frontend consumes those services and renders the
  analytical & research UI (charts, tables, ticker/indicator/signal exploration).

New flow:

```
… → Snowflake (raw + metastore) → dbt (models/signals)
   → FastAPI microservices (Docker Compose) → React + TS + Vite (single-user UI)
```

Ownership seams: **data-engineer** owns FastAPI *data correctness* (the queries);
**python-specialist** owns FastAPI *service code quality*; **web-designer** owns
the visual/style system; **frontend-engineer** owns the React implementation;
**ux-researcher** and **financial-markets-specialist** advise. These are captured
as project subagents under `.claude/agents/`.

## Considered options

- **Python-native BI (Streamlit / Dash)** — faster to build and needs no
  JavaScript, since the whole stack is already Python. Rejected: weaker as an
  engineering/portfolio showcase and a poorer fit for a bespoke, dense research UI
  with custom charting and interaction.
- **Frontend queries a thin query proxy / BI embed** — avoids a hand-written API
  but couples the UI to warehouse internals and is less conventional.
- **Stay backend-only** — keeps the original narrow scope; rejected because the
  results are currently only reachable by querying Snowflake by hand.

## Consequences

- **README scope changes**: "public API" and "frontend application" move from
  out-of-scope to in-scope; the architecture overview gains the FastAPI and React
  tiers.
- **Two new subsystems** to build, run, and maintain (an API service layer and a
  JS frontend) — larger surface, more tooling (Node/Vite), more moving parts in
  Docker Compose. This is the main reversal cost.
- **Provider/identity model is unaffected**: the UI reads the same
  `(Ticker, Trading Date)` warehouse truth and must present it honestly (this is
  educational/portfolio work, **not investment advice**).
- **Single-user for now**: no auth or multi-tenant concerns yet; a later move to
  multiple users would add authn/z and per-user state as a further scope step.
- "Microservices on Docker Compose (for now)" signals the serving tier may later
  move to a different runtime; the API contract, not the deployment, is the stable
  boundary.
