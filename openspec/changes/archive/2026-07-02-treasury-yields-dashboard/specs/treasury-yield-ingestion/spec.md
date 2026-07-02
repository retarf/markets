## ADDED Requirements

### Requirement: A successful load publishes an ingestion event

The ingestion side SHALL publish an event to NATS after a load (daily or backfill)
successfully advances the warehouse. The event SHALL be named
`treasury.yields.ingested` and SHALL carry at least the affected `trading_date`
and the set of `tenors` updated. This extends the ingestion activities introduced
by the `treasury-yield-data` change with the NATS hook the serving tier consumes.

#### Scenario: Event published after load

- **WHEN** a load writes new observations for `2026-07-01` covering `2Y` and `10Y`
- **THEN** a `treasury.yields.ingested` event is published naming `2026-07-01` and
  the updated Tenors

#### Scenario: No event when nothing new loaded

- **WHEN** a run loads zero new observations
- **THEN** no `treasury.yields.ingested` event is published
