# UX Brief — US Treasury Yields Dashboard (first frontend feature)

Grounded in `~/.claude/skills/dev-design/checklists/ux.md`, `docs/design-direction.md` (feature section), and ADRs 0003 / 0005. Copy uses `CONTEXT.md` terms exactly: **Yield**, **Tenor**, **Yield Curve**, **2s10s Spread**, **Trading Date**.

## 1. Screen inventory

One screen: **Yields Dashboard** (single dense page, no tabs, no navigation depth — matches the "one dense dashboard page" intent). Because there is exactly one screen and one user, the checklist's "current location / way back" item is satisfied by there being nowhere else to be; do not add breadcrumbs or nav chrome. Regions:

- **R0 — Page header / global control bar** (thin, quiet): app/feature title ("US Treasury Yields"), the latest **Trading Date** the page is showing, a live-status indicator, and the two global controls (comparison-date control, time-window control). Plus a persistent, subordinate "descriptive market data, not investment advice" disclosure (design-direction non-negotiable).
- **R1 — Yield Curve (hero panel)**: yield (%) on Y, **Tenor** ordered by maturity on X (`1M,3M,6M,1Y,2Y,3Y,5Y,7Y,10Y,20Y,30Y`), latest curve drawn large + optional historical overlay.
- **R2 — 2s10s Spread panel**: 10Y−2Y series over time, zero line emphasized, inverted region (spread < 0) shaded and labeled.
- **R3 — 2Y & 10Y series panel**: the two leg Yields over time, same time window as R2.

R1 is the hero; R2 and R3 are visibly subordinate in size but co-equal to each other. One clear primary job per screen: *read and compare the shape of the curve and its recession signal.*

## 2. Information architecture

Grouped the way the analyst reasons (checklist IA: group by user mental model, not storage), which is **curve shape → recession signal → underlying legs**:

- **Layout**: hero **R1** occupies the top/left dominant area. **R2 (Spread)** and **R3 (2Y & 10Y legs)** stack directly beneath/beside it and are **vertically aligned to share one time axis** so a date in R2 lines up with the same date in R3. Suggested: R1 spans the top full width (or left two-thirds); R2 above R3 in a stacked column sharing the X (time) axis. R3 sits immediately under R2 because the flow reads spread-then-legs.
- **Global vs per-panel**:
  - *Global (R0)*: the **comparison-date control** (drives R1's overlay only), the **time-window control** (drives R2 + R3's shared X range), the current **Trading Date** readout, and the **live-update status**. These live once, in the header, not repeated per panel.
  - *Per-panel*: each panel owns its **legend**, its **Y-axis label/units**, its own **state slot** (loading/empty/partial/error rendered inside that panel's frame, near the cause — checklist: error near cause), and its hover tooltip.
- **Cross-panel linking** is a global behavior but has no control — it is driven by hover (see §5).
- Chrome stays quiet; charts and numbers are the hero (design-direction tone). Tabular/monospaced figures for every numeric readout.

## 3. Primary flow (analyst's main task, end to end)

1. **Land** → page loads latest **Trading Date**; R1 shows today's **Yield Curve**, R2 shows the **2s10s Spread** over the default window, R3 shows the **2Y & 10Y** legs over the same window. Resting/nominal state, no action required to get value (design-direction: "sees a lot without drowning").
2. **Read today's curve** (R1): analyst reads shape — upward vs flat vs inverted — with Tenor ordered by maturity.
3. **Compare to history** → analyst uses the header **comparison-date control** (e.g. "1 Month ago", "1 Year ago", or a specific Trading Date). R1 overlays the historical curve on the latest one; steepening/flattening/inversion is *seen as movement* between the two lines, not inferred.
4. **See the inversion signal** (R2): analyst looks to the Spread panel; the **inverted region (spread < 0)** is shaded, sits below the emphasized zero line, and is labeled "inverted" — unmissable and never color-alone.
5. **Tie it to the legs** (R3): analyst hovers a **Trading Date** in R2; the cross-highlight lands on the same date in R3 (2Y & 10Y) and cross-highlights the corresponding point/curve context, so they see *which leg moved* to drive the spread. Tooltip gives exact figures.
6. **Adjust the lens** → analyst changes the **time-window control** to widen/narrow R2+R3; R1's comparison date is independent so the two explorations don't fight.
7. **Live** → if an SSE `treasury.yields.ingested` event arrives mid-session, panels redraw subtly to the new latest Trading Date (see §5). No dead ends, no modal interruptions; every step is reversible by changing a control (checklist: no dead ends, cheap recovery).

Read-only feature: no destructive/irreversible steps exist, so the "confirm destructive actions" checklist item is satisfied by absence.

## 4. State matrix

States per region. "Honestly" = design-direction non-negotiables: gaps not interpolated, a Tenor with no data omitted (not drawn at zero), inversion never color-alone.

| Region | Loading | Empty | Partial | Error | Live-updating | Nominal |
|---|---|---|---|---|---|---|
| **Page (R0)** | Skeleton header; controls disabled with visible disabled affordance | (n/a — single-user data source; if the whole API is unreachable, page-level Error) | If some panels loaded and others failed, header shows a neutral "some data unavailable" note | Global banner *in R0* if the query service/gateway is unreachable: what failed + a **Retry** action | "Updated to [Trading Date]" transient status chip near the Trading Date readout | Title + latest **Trading Date** + live-status "Live" indicator |
| **R1 Yield Curve** | Chart-area skeleton (axes ghosted, no fake line) | "No **Yield Curve** available" with retry; never an empty axis implying zero | **Missing Tenor**: that Tenor's point is **omitted** and the line breaks/gaps there (not zero, not interpolated); a small note lists omitted Tenors. Comparison curve missing for chosen date → show latest only + inline "no curve for [date]" | Panel-local error inside R1 frame + Retry, near the cause | Latest curve line eases to new values (reduced-motion: instant swap, no motion) | Latest curve (+ optional overlay), Tenor-ordered X, 2-decimal % |
| **R2 2s10s Spread** | Chart skeleton | "No **2s10s Spread** data for this window" | **FRED gaps** (holiday/missing print) rendered as **breaks in the line**, not bridged; zero line still drawn | Panel-local error + Retry | New point(s) appended; zero-line and shading recompute subtly | Spread series over time, zero line emphasized, **inverted region shaded + "inverted" label + below-axis position** |
| **R3 2Y & 10Y series** | Chart skeleton | "No 2Y / 10Y **Yield** data for this window" | If only one leg has data, draw the one present, label the other "no data" in legend (don't fabricate) | Panel-local error + Retry | New points appended subtly | Two legs, distinguishable by more than color (see §5), 2-decimal %, shared X with R2 |

State rules:
- **Loading is a skeleton, never a blank panel** (checklist). Axes may ghost in; no placeholder data line that could be mistaken for real Yields.
- **Error is local to the panel that failed** and states what failed + Retry (checklist: recover near cause). Only a total serving-tier failure escalates to the R0 banner.
- **Partial is the honest-presentation core**: gaps are gaps; a Tenor/leg with no data is omitted and *named*, never zero-filled or interpolated.
- **Empty** (cold start, no data at all) gives a clear next action (Retry / "check ingestion"), not a dead blank.

## 5. Interactions

- **Hover cross-highlight (linked panels)**: hovering a **Trading Date** in R2 or R3 draws a shared crosshair at that date in *both* time-series panels and highlights the matching context; conversely the crosshair's date can drive an emphasis in R1's overlay. Highlight must use position + a visible marker, not color alone.
- **Tooltips**: a single tooltip per hover, **tabular/monospaced figures**. Curve tooltip: Tenor + Yield to **2 decimals %** (and delta vs the overlay curve if one is shown). Spread tooltip: value in **basis points (bp)**, with an explicit "inverted" flag when negative. Series tooltip: 2Y and 10Y each to 2 decimals %, plus their difference in bp. Trading Date shown in full.
- **Comparison-date control (R1)**: a segmented/preset control — "Latest only", "vs 1 Month ago", "vs 1 Year ago", plus a specific Trading Date option. Choosing a preset resolves to the nearest available Trading Date (honest: if that exact date is a FRED gap, snap to the prior available Trading Date and *say so* in the overlay label). Every selection has a visible result (overlay appears/updates) — checklist: every action has a visible result.
- **Time-window control (R2+R3)**: presets (e.g. 6M / 1Y / 2Y / 5Y / Max) governing the shared X range of the two time-series panels only. Independent of the comparison-date control.
- **SSE live redraw**: on `treasury.yields.ingested`, panels ease to the new latest Trading Date with a subtle transition and a transient "Updated to [date]" chip in R0. **Reduced-motion**: swap instantly, no animation, chip still shown so the update isn't silent (checklist: nothing lost silently; design-direction: respect reduced-motion). The live indicator distinguishes "Live" (connected) from "Reconnecting"/"Offline" (SSE dropped) with text + icon, not color alone.
- **Keyboard / focus (power user)**: logical focus order R0 controls → R1 → R2 → R3. Controls (comparison presets, window presets) are keyboard-operable with a **visible focus indicator**. Provide keyboard access to move the crosshair along the time axis (arrow keys once a panel is focused) so a non-mouse analyst can read exact points. Focusable targets are **≥24px** with adequate spacing (checklist accessibility).

## 6. Controls / forms

No data-mutating forms exist (read-only feature), so form-submission, unsaved-changes, and destructive-confirm items are satisfied by absence — the designer should not invent a Save/Submit anywhere. Two selection controls only:

- **Comparison-date control** — preset segmented control with real, visible **labels** ("Latest only", "vs 1M", "vs 1Y", "Custom Trading Date…"), not placeholder-only. Sensible default: "Latest only" (no overlay) so first paint is uncluttered. Custom picker is bounded to available **Trading Dates**; unavailable dates are disabled with a tooltip saying why (FRED gap) rather than silently rejected.
- **Time-window control** — preset segmented control, real labels, default sized so the 2s10s inversion history is legible (suggest 2Y default; designer confirms with real data density). Selecting outside available range clamps to Max and notes it.

Both controls: interactive affordance is obvious, the active selection is indicated by more than color (weight/underline/fill + text), targets ≥24px, and every change produces an immediate visible redraw.

## Accessibility summary the designer must satisfy (checklist §Accessibility)
- Body text and all numeric readouts **≥4.5:1** on their surface; large chart labels **≥3:1**. Dark-first, considered light mode.
- The two curve overlay lines (latest vs historical) and the two legs (2Y vs 10Y) must be **distinguishable without color** — differ by line style/marker/weight and a real legend label.
- Inversion in R2 = **shaded region + emphasized zero line + "inverted" label + below-axis position** (four cues; never color alone). This is the single most important honesty requirement.
- Visible focus indicator on every control and on the keyboard crosshair; logical focus order top-down.
