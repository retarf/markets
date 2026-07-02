# yields-dashboard-ui Specification

## Purpose
TBD - created by archiving change treasury-yields-dashboard. Update Purpose after archive.
## Requirements
### Requirement: A React app renders the single-page Yields Dashboard

A new `frontend/` app (React + TypeScript + Vite) SHALL render one dense
dashboard page — no tabs, no nav chrome — matching `design/layout.svg`: a **Yield
Curve** hero panel, a **2s10s Spread** panel, and a **2Y & 10Y series** panel,
plus a header control bar. It SHALL derive all colors, spacing, type, and radii
from the project `design-tokens.json` (no hard-coded style values).

#### Scenario: Dashboard loads with data

- **WHEN** the app loads and the query service returns data
- **THEN** the hero shows the latest **Yield Curve**, the spread panel shows the
  **2s10s Spread**, and the series panel shows the **2Y** and **10Y** legs
- **AND** styling resolves from `design-tokens.json`

### Requirement: The Yield Curve panel supports historical comparison

The curve panel SHALL plot Yield (%) against Tenor ordered by maturity and SHALL
support overlaying a historical curve via a header comparison control (`Latest
only` / `vs 1M` / `vs 1Y` / a custom Trading Date). The two curves SHALL be
distinguishable **without color** (line style + markers + legend). When a
comparison date is unavailable, the resolved nearest Trading Date SHALL be shown
in the overlay label.

#### Scenario: Overlay a year-ago curve

- **WHEN** the analyst selects `vs 1Y`
- **THEN** the panel overlays the resolved year-ago curve on the latest one, with
  the two lines distinguishable without color and the resolved date labeled

### Requirement: The Spread panel shows inversion with four non-color cues

The 2s10s Spread panel SHALL emphasize the zero line and SHALL mark the inverted
region (spread `< 0`) with **four** independent cues: a shaded region, the
emphasized labeled zero line, an "inverted" text label, and the line's below-axis
position. Inversion SHALL NOT be conveyed by color alone.

#### Scenario: Inverted stretch is unmistakable

- **WHEN** the spread series dips below zero for a stretch
- **THEN** that stretch is shaded, sits below the labeled zero line, and is
  labeled "inverted" — legible without relying on color

### Requirement: Panels are linked on a shared time axis

The Spread and series panels SHALL share one time axis; hovering a Trading Date in
either SHALL show a shared crosshair at that date in both and a tabular-figure
tooltip (Yields to 2 decimals `%`, spread in basis points). The crosshair SHALL be
keyboard-movable (arrow keys) once a panel is focused.

#### Scenario: Cross-highlight ties spread to legs

- **WHEN** the analyst hovers a Trading Date on the spread panel
- **THEN** the same date is highlighted on the 2Y/10Y series panel and the tooltip
  shows both legs and their difference in basis points

### Requirement: Every data state is handled honestly

Each panel SHALL render loading (skeleton, no fabricated data line), empty (clear
next action, no zero-implying axis), partial (a missing Tenor omitted and named,
gaps shown as breaks — never zero-filled or interpolated), and error (panel-local
message + a Retry action) states; a total serving-tier failure SHALL surface a
header-level banner with Retry.

#### Scenario: Missing Tenor is omitted, not zeroed

- **WHEN** the latest curve is missing the `20Y` Tenor
- **THEN** the curve breaks at that Tenor (no point at zero) and a note names the
  omitted Tenor

#### Scenario: Panel error is recoverable in place

- **WHEN** the query service call for one panel fails
- **THEN** that panel shows what failed and a Retry control, without blanking the
  other panels

### Requirement: The dashboard updates live via SSE

The app SHALL connect to the SSE stream and, on a `treasury.yields.ingested`
update, redraw to the new latest Trading Date with a subtle transition and a
transient "Updated to <Trading Date>" indicator. Under reduced-motion the update
SHALL apply instantly (no animation) while still signalling the update. The live
status SHALL distinguish connected / reconnecting / offline by text + icon, not
color alone.

#### Scenario: Live redraw on new data

- **WHEN** an SSE update for a new Trading Date arrives while the dashboard is open
- **THEN** the panels update to that date and a transient "Updated to <date>"
  indicator appears

#### Scenario: Reduced motion

- **WHEN** the user prefers reduced motion and an update arrives
- **THEN** the change applies with no animation, and the update is still signalled

### Requirement: The dashboard states it is not investment advice

The page SHALL carry a persistent, subordinate disclosure that it shows
descriptive market data and is not investment advice.

#### Scenario: Disclosure present

- **WHEN** the dashboard is shown in any state
- **THEN** the "not investment advice" disclosure is visible

