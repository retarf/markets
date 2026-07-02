## ADDED Requirements

### Requirement: Yields are sourced from the U.S. Treasury CMT feed

The system SHALL fetch daily constant-maturity Treasury yields from the U.S.
Department of the Treasury *Daily Treasury Par Yield Curve Rates* CSV feed, which
returns the full curve for a whole calendar year in one keyless request (no API
key). The Data Provider for the `YIELD_DATA` domain is the U.S. Treasury; Yahoo is
not used. The canonical Tenor set the system tracks SHALL be `1M, 3M, 6M, 1Y, 2Y,
3Y, 5Y, 7Y, 10Y, 20Y, 30Y`, defined in exactly one place as a mapping from Tenor
label to the Treasury CSV column (e.g. `10Y → "10 Yr"`).

#### Scenario: Successful fetch for a year

- **WHEN** the fetch runs for year `2026`
- **THEN** the system requests the Treasury yield-curve CSV for `2026` with no API
  key
- **AND** receives one row per Trading Date with a column per Tenor

#### Scenario: Tenor set is defined in one place

- **WHEN** the configured Tenor universe is read
- **THEN** it resolves to a single canonical mapping of Tenor label → Treasury CSV
  column, with no conflicting copies

### Requirement: A missing Treasury value is a gap, never a value

The system SHALL drop a missing Treasury value before writing and SHALL NOT coerce
it to zero, carry it forward, or interpolate it. The Treasury CSV reports a missing
value as an empty cell.

#### Scenario: Missing value is dropped

- **WHEN** the Treasury CSV has an empty cell for a Tenor on a Trading Date
- **THEN** no `(Tenor, Trading Date)` observation is produced for it
- **AND** no `0` or interpolated Yield is written for that Trading Date

### Requirement: Fetched yields are normalized to (Tenor, Trading Date, Yield)

The system SHALL parse the wide Treasury CSV — US-format dates (`MM/DD/YYYY`) and a
Yield column per Tenor — into normalized `(Tenor, Trading Date, Yield)` rows,
keeping only the tracked Tenor columns, converting dates to ISO (`YYYY-MM-DD`), and
Yield as a decimal percent (e.g. `4.44`).

#### Scenario: Wide row becomes per-Tenor rows

- **WHEN** a Treasury CSV row for `06/30/2026` carries `2 Yr = 4.14` and
  `10 Yr = 4.44`
- **THEN** it yields normalized rows `(2Y, 2026-06-30, 4.14)` and
  `(10Y, 2026-06-30, 4.44)` (plus the other tracked Tenors present)

### Requirement: Yields land in the YIELD_DATA datalake as CSV

The fetch SHALL write output to a dated datalake namespace separate from equities
(`datalake/YIELD_DATA/dt=YYYY-MM-DD/`), with a header row and columns
`Tenor,Date,Yield`, ISO dates, so the load reads a stable normalized contract.

#### Scenario: Output is namespaced away from equities

- **WHEN** a fetch completes for capture date `2026-07-01`
- **THEN** a normalized CSV exists under `datalake/YIELD_DATA/dt=2026-07-01/`
- **AND** nothing is written under `datalake/STOCK_DATA/`

### Requirement: Yields load to a dedicated raw table with yield-appropriate quality checks

The system SHALL load yields into a dedicated raw table for the `YIELD_DATA` domain
keyed by `(Tenor, Trading Date)` with the Yield value. The default warehouse is a
local **DuckDB** file (no Snowflake/Spark required for this domain — see ADR 0006);
Snowflake MAY be added later as an optional target. Quality checks SHALL be
appropriate to a rate, not a Daily Bar: `Trading Date`, `Tenor`, and `Yield` SHALL
be non-null and the `Yield` SHALL fall within a sane band (configurable; e.g.
`-5%..25%`), validated for the whole batch **before** any write. The equity
`volume > 0` and `HIGH >= LOW` checks SHALL NOT be applied.

#### Scenario: Rate outside the sane band is rejected

- **WHEN** a loaded row carries a `Yield` outside the configured band
- **THEN** the load fails a quality check naming the Tenor and Trading Date
- **AND** no rows from that batch are written

#### Scenario: Equity volume rule is not applied

- **WHEN** yields are loaded
- **THEN** the loader does not require a `volume` column and does not reject rows
  for `volume <= 0` (yields carry no volume)

### Requirement: Incremental load uses a per-Tenor metastore

The system SHALL keep incremental-load state per Tenor in a `YIELD_DATA` metastore
(the last loaded Trading Date per Tenor) and SHALL load only observations newer
than that date, updating the state after a successful load. A re-run for an
already-loaded Trading Date SHALL NOT create duplicate `(Tenor, Trading Date)`
rows.

#### Scenario: Only new observations load

- **WHEN** the metastore shows `10Y` last loaded at `2026-06-30` and the fetch
  returns observations through `2026-07-01`
- **THEN** only the `2026-07-01` observation for `10Y` is written
- **AND** the metastore advances `10Y` to `2026-07-01`

#### Scenario: Re-run is idempotent

- **WHEN** the load runs twice for the same Trading Date and Tenor
- **THEN** the warehouse holds exactly one row for that `(Tenor, Trading Date)`

### Requirement: Airflow runs the scheduled daily pull

The scheduled daily ingestion of yields SHALL run as an Airflow DAG, separate from
the equity DAG, fetching the current year's Treasury curve and loading all tracked
Tenors via the shared fetch/normalize/load activities. The equity `stock_data_dag`
SHALL be unaffected.

#### Scenario: Daily DAG ingests the latest curve

- **WHEN** the yields DAG runs for a business day
- **THEN** the current-year curve is fetched, normalized, validated, and loaded,
  advancing each Tenor's metastore date

### Requirement: Temporal owns durable on-demand backfill

Historical backfill over a range of years SHALL run as a **Temporal** workflow with
idempotent activities, resumable across worker failures, and paced to respect the
Treasury endpoint. It SHALL reuse the same fetch/normalize/load activities as the
daily pull (no duplicated ingestion logic) and SHALL be safe to re-run (idempotent
by `(Tenor, Trading Date)`).

#### Scenario: Backfill resumes after a failure

- **WHEN** a backfill workflow for years `2015..2024` is interrupted partway
- **THEN** on resume it continues from where it left off without re-loading
  already-loaded `(Tenor, Trading Date)` rows

#### Scenario: Backfill and daily pull share ingestion logic

- **WHEN** the Temporal backfill and the Airflow daily pull both ingest yields
- **THEN** both call the same fetch/normalize/load activity code path
