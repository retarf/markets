# Design direction — Markets research platform

Design intent captured during the grill that scoped the frontend. This is
**intent, not glossary** (see `CONTEXT.md`) and not a spec — it exists so a future
`dev-design` phase and the `web-designer` / `ux-researcher` agents start from
stated direction rather than guessing.

## Who and what
- **One user for now** — a single analyst doing research, not a mass-market
  product. Optimize for depth of analysis and speed of insight over onboarding.
- An **analytical & research platform**: explore prices, Daily Bars, and trading
  signals; pick Tickers, adjust indicator/signal parameters, compare instruments,
  read charts alongside dense tables.

## Tone & aesthetic
- **Data-first and calm** — reference points are TradingView / Bloomberg terminal
  / Observable: information-dense but not noisy. Not a marketing-splash look.
- **Dark mode is first-class** (analysts live in dark UIs); provide a considered
  light mode too.
- Restrained, professional palette. Charts and numbers are the hero, chrome is
  quiet.

## Density & legibility
- Research-grade density is desired: tables and charts side by side, many rows,
  progressive disclosure over hiding.
- **Tabular/monospaced figures** for prices and numeric columns.
- Sensible defaults so the analyst sees a lot without drowning.

## Non-negotiables
- **State is never encoded by color alone** — up/down/neutral and signal states
  must pair color with shape, label, or position (accessibility + honesty).
- Strong contrast, visible focus, respect reduced-motion.
- **Honest presentation**: never imply precision or advice the data lacks. This is
  educational/portfolio work, **not investment advice**. Surface empty/partial
  states plainly (missing Trading Dates, a signal that never fired).
- UI copy uses `CONTEXT.md` terms exactly: **Ticker**, **Daily Bar**,
  **Trading Date**.

## Stack constraints
- React + TypeScript + Vite; token-driven styling (design tokens + Tailwind / CSS
  variables) owned by `web-designer` and consumed by `frontend-engineer`.
- Charting library chosen deliberately for time series (e.g. lightweight-charts /
  visx / Recharts) — must handle gaps, large ranges, and many series legibly.

---

# Feature: US Treasury yields & yield curve (first frontend feature)

Design intent captured during the grill that scoped this feature. Domain terms
(`Yield`, `Tenor`, `Yield Curve`, `2s10s Spread`) are defined in `CONTEXT.md`.

## What it shows
A **single dense dashboard page** (no tabs) with three linked panels:
1. **Yield Curve (hero)** — yield (%) vs Tenor for the latest Trading Date, drawn
   large. A **date scrubber** overlays a historical curve (e.g. today vs 1 month /
   1 year ago) so steepening, flattening, and inversion are *visible as movement*,
   not inferred. X-axis is Tenor ordered by maturity (3M…30Y); label ticks, don't
   space linearly by years unless it reads clearly.
2. **2s10s Spread** — the 10Y−2Y series over time, with the **inverted region
   (spread < 0) shaded** (red/negative treatment) and the zero line emphasized.
   This is the recession-signal panel; make inversion unmissable.
3. **2Y & 10Y series** — the two underlying yields over time, same time window as
   the spread, so the reader ties spread moves back to the legs.

## Interaction & feel
- **Data-first, calm, dark-first** (inherits the platform direction above).
- Panels are **linked**: hovering a date in the spread/series highlights the
  corresponding curve; the curve scrubber date drives what "historical overlay"
  means. Cross-hair + tabular-figure tooltips showing exact bp values.
- **Live update**: when the query service pushes an SSE `treasury.yields.ingested`
  event, the curve/spread redraw with a subtle, non-jarring transition (respect
  reduced-motion — no flashy animation).
- Honest empty/partial states: data gaps (holidays, missing print) shown as gaps,
  not interpolated silently; a Tenor with no data is omitted from the curve, not
  drawn at zero.

## Non-negotiables (in addition to platform-wide ones)
- **Inversion is never encoded by color alone** — pair the red shade with the
  zero line, a label ("inverted"), and position below axis.
- Yields shown to 2 decimals (%) with tabular figures; spreads may be shown in
  basis points.
- Never imply forecasting or advice — this is descriptive market data
  (educational/portfolio), **not investment advice**.

## Suggested charting approach (frontend-engineer finalizes)
The curve needs a custom, ordinal-by-maturity X-axis and shaded regions on the
spread — **visx** (D3 scales, full control) or **Recharts** (faster, less
control) fit better than candle-oriented libraries like lightweight-charts here.
Pick one deliberately and keep all series legible together.

## Tenor set (default, from the U.S. Treasury constant-maturity curve)
`1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y`. The 2s10s Spread uses the 2Y
and 10Y legs. Trim the curve set later if it reads as cluttered.
