# treasury-yield-modeling Specification

## Purpose
TBD - created by archiving change treasury-yield-data. Update Purpose after archive.
## Requirements
### Requirement: Staging model types the raw yields

A dbt staging model `stg_treasury_yields` SHALL expose one typed row per
`(Tenor, Trading Date)` with a numeric `yield` (percent), sourced from the
`YIELD_DATA` raw table. It SHALL NOT invent rows for Trading Dates a Tenor has no
observation for.

#### Scenario: Staging preserves gaps

- **WHEN** `10Y` has no observation for a US market holiday date
- **THEN** `stg_treasury_yields` has no `(10Y, that date)` row (the gap is not
  filled)

### Requirement: Yield Curve model exposes yield vs Tenor per Trading Date

A model SHALL expose the **Yield Curve**: for each Trading Date, the Yield at each
available Tenor, with a stable **maturity ordering** (`1M < 3M < 6M < 1Y < 2Y <
3Y < 5Y < 7Y < 10Y < 20Y < 30Y`) so consumers can plot Tenor on an axis ordered by
maturity. A Tenor with no observation on a given Trading Date SHALL be absent for
that date, not present with a zero Yield.

#### Scenario: Curve for a date lists only available Tenors in maturity order

- **WHEN** the curve is read for a Trading Date where `20Y` has no print
- **THEN** the returned points cover the other Tenors ordered by maturity
- **AND** `20Y` is absent (not a `0.00` point)

### Requirement: 2s10s Spread is derived from the stored legs

A model SHALL expose the **2s10s Spread** per Trading Date as `10Y − 2Y`,
available in basis points, computed from the stored `10Y` and `2Y` Yields (not
fetched as a separate ready-made series, for internal consistency with the curve). A
Trading Date missing either leg SHALL have no spread value for that date.

#### Scenario: Spread computed where both legs exist

- **WHEN** `2Y = 4.90%` and `10Y = 4.27%` on a Trading Date
- **THEN** the 2s10s Spread for that date is `-63` basis points (negative =
  inverted)

#### Scenario: Spread absent when a leg is missing

- **WHEN** the `2Y` leg has no observation for a Trading Date
- **THEN** that Trading Date has no 2s10s Spread value (not `0`, not carried
  forward)

### Requirement: Per-Tenor series is queryable over a time window

The modeling layer SHALL let a consumer read a single Tenor's Yield series over a
Trading Date range (used for the 2Y and 10Y series panel), preserving gaps.

#### Scenario: Leg series over a window

- **WHEN** the `2Y` series is requested for a 2-year window
- **THEN** the result is the `2Y` Yield per Trading Date over that window, with
  gaps where the Treasury feed had no value

