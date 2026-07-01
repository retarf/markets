# Temporal alongside Airflow: scheduled data plane vs durable backfill

## Context

Orchestration today is **Airflow**: the equity pipeline runs as scheduled DAGs
with dynamic task mapping and Asset-driven scheduling. For the new Treasury-yield
domain we want to both (a) pull Treasury data on a daily schedule and (b) run
**on-demand historical backfills** over arbitrary date ranges (e.g. 2015–2024),
resumable across failures and paced against Treasury's rate limits.

A daily Treasury pull is a textbook **batch job** — periodic, short-lived, stateless
between runs, idempotent by Trading Date — which Airflow already does well.
An on-demand, long-running, resumable, rate-paced backfill is a **durable
workflow**, which Airflow handles clumsily and Temporal is purpose-built for.

The project also has a portfolio goal of demonstrating distributed-systems
judgment, so the risk to avoid is using Temporal *decoratively* — wrapping a cron
in a workflow engine that its daily-pull code never exercises.

## Decision

Run **both**, with a boundary drawn by workload shape, not by domain:

- **Airflow = scheduled data plane.** It keeps owning the equity pipeline and
  also runs the **daily** Treasury-yield pull. No new tool for the cron-shaped job.
- **Temporal = durable/triggerable service workflows.** It owns the **on-demand
  historical backfill** for yields: a long-running, resumable workflow with
  idempotent activities, retries, progress, and Treasury rate-limit pacing.

Each tool is therefore visibly doing what it is *good at*; Temporal is justified
by a workload Airflow is bad at, not by re-implementing a schedule.

## Considered options

- **Airflow only** (param-driven backfill DAG) — no second system; simplest. But
  Airflow backfills of long, resumable, rate-paced ranges are awkward, and the
  portfolio goal of showing Temporal is unmet. Rejected for this project's goals.
- **Temporal for all yield workflows** (including the daily pull) — one engine for
  the new domain, but the daily pull under-uses Temporal and its code looks like
  an Airflow task, weakening the "right tool for the job" story. Rejected.
- **Temporal replaces Airflow** — biggest commitment; deprecates working,
  tested Airflow. Out of scope now.

## Consequences

- Two orchestrators run concurrently. This is intentional and boundary-documented
  (schedule vs durable workflow); without this ADR it would read as duplication.
- New infrastructure: a Temporal cluster + its datastore in Docker Compose, and a
  worker in the yields-ingestion-service. Operational surface grows.
- The daily pull and the backfill share the same underlying Treasury
  fetch/validate/load **activities**, so logic is not duplicated across the two
  orchestrators — only the *triggering* differs.
- If the "right tool" boundary ever blurs (e.g. Airflow gains what we needed, or
  we standardize on one engine), this split should be revisited.
