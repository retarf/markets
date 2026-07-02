#!/usr/bin/env python3
"""Render layout.svg for the US Treasury Yields dashboard (first frontend feature).

Dark-first, data-first composition drawn ONLY from the bundled svglib primitives
and a project theme derived from the design-direction note. This is the FIRST
frontend change, so the theme is derived + refined here and proposed alongside the
mockup; it is NOT persisted (that happens on user acceptance).
"""

import os
import sys
from html import escape

sys.path.insert(0, os.path.expanduser("~/.claude/skills/dev-design/lib"))
import svglib as L  # noqa: E402
from svglib import Svg, tokens_from_theme, contrast  # noqa: E402


# --- Theme: derive from direction, then refine to a dark-first palette --------
# derive_theme() gives a light scaffold led by a hue; the direction is
# "data-first, calm, dark-first, TradingView/Bloomberg-calm" with a restrained
# professional blue accent. We refine derive_theme("blue") into a dark theme and
# verify every text/line/button contrast against the visual-design checklist.
theme = L.derive_theme("blue")
theme["color"] = {
    "primary":       "#4c8dff",  # calm terminal blue — accent/emphasis + latest series
    "primarySubtle": "#86b0ff",  # lighter blue for subordinate accents/focus fills
    "onPrimary":     "#0b0e14",  # dark ink on the bright accent (AA 6.04:1, white was 3.2)
    "bg":            "#0b0e14",  # deep slate canvas behind panels (dark-first)
    "surface":       "#131722",  # chart/panel surface (TradingView-calm)
    "elev":          "#1c2230",  # segmented track / default buttons / chips
    "border":        "#2a3242",  # quiet dividers / panel + input borders
    "text":          "#e6e9ef",  # primary text/figures (AA 14.7:1 on surface)
    "dim":           "#8a93a6",  # secondary text/axes (AA 5.8:1 on surface)
    "danger":        "#f0524b",  # error + negative/inversion treatment (paired, never alone)
    "onDanger":      "#0b0e14",  # dark ink on a filled danger surface (AA 5.5:1; #1f2430 was 4.44)
    "ok":            "#3fb950",  # live/connected + positive
}
theme["radius"] = 8
t = tokens_from_theme(theme)
ON_DANGER = theme["color"]["onDanger"]  # not carried by Tokens; read from theme

# Contrast guardrails (fail loudly if a refinement regresses accessibility).
assert contrast(t.text, t.surface) >= 4.5
assert contrast(t.dim, t.surface) >= 4.5
assert contrast(t.accent, t.surface) >= 3.0          # chart line / large label
assert contrast(t.on_accent, t.accent) >= 4.5        # filled primary button
assert contrast(t.danger, t.surface) >= 3.0
assert contrast(ON_DANGER, t.danger) >= 4.5           # filled danger button label

MONO = "'JetBrains Mono','SF Mono',ui-monospace,Menlo,Consolas,monospace"
FS = t.type_scale  # (12,14,16,20,28)

s = Svg(t)
W, H = 1440, 1520


# --- Low-level helpers (raw SVG on top of the bundled primitives) -------------
def mono(x, y, txt, size=13, fill=None, weight=400, anchor="start"):
    s.emit(f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" '
           f'font-weight="{weight}" fill="{fill or t.text}" '
           f'text-anchor="{anchor}" letter-spacing="0.2">{escape(txt)}</text>')


def vtext(x, y, txt, size=12, fill=None, weight=500):
    s.emit(f'<text x="{x}" y="{y}" font-family="{t.font}" font-size="{size}" '
           f'font-weight="{weight}" fill="{fill or t.dim}" text-anchor="middle" '
           f'transform="rotate(-90 {x} {y})">{escape(txt)}</text>')


def polyline(pts, stroke, sw=2, dash=None, opacity=None):
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' opacity="{opacity}"' if opacity is not None else ""
    s.emit(f'<polyline points="{p}" fill="none" stroke="{stroke}" '
           f'stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"{d}{o}/>')


def polygon(pts, fill, opacity=1.0):
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    s.emit(f'<polygon points="{p}" fill="{fill}" opacity="{opacity}"/>')


def dot(x, y, r, fill, stroke=None, sw=1.5):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    s.emit(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"{st}/>')


def square(x, y, r, fill, stroke=None, sw=1.5):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    s.emit(f'<rect x="{x-r:.1f}" y="{y-r:.1f}" width="{2*r}" height="{2*r}" '
           f'fill="{fill}"{st}/>')


def chip(x, y, label, fg, bg, w=None):
    fs = FS[0]
    w = w or int(len(label) * L.char_w(fs) + 20)
    s.rect(x, y, w, 20, bg, rx=6, stroke=t.border, sw=1)
    s.text(x + w / 2, y + 14, label, fs, fg, 600, "middle")
    return w


def panel(gid, x, y, w, h, title, subtitle=None):
    s.rect(x, y, w, h, t.surface, rx=t.radius, stroke=t.border, sw=1)
    s.text(x + 20, y + 30, title, FS[2], t.text, 700)
    if subtitle:
        tw = len(title) * L.char_w(FS[2]) + 30
        s.text(x + 20 + tw, y + 30, subtitle, FS[0], t.dim, 400)


def custom_seg(x, y, w, opts, active, focus=None):
    """Segmented control with a high-contrast active delineation: the active
    segment carries an accent border + an accent underline + bold text (three
    non-color cues), not just a near-invisible fill. Optional focus ring."""
    h = 36
    s.rect(x, y, w, h, t.elev, rx=t.radius + 2, stroke=t.border, sw=1)
    seg_w = w / len(opts)
    for i, opt in enumerate(opts):
        sx = x + i * seg_w
        is_active = (opt == active)
        if is_active:
            s.rect(sx + 3, y + 3, seg_w - 6, h - 6, t.bg, rx=t.radius,
                   stroke=t.accent, sw=1.5)                       # accent border
            s.rect(sx + 10, y + h - 8, seg_w - 20, 2.5, t.accent, rx=1)  # underline
        s.text(sx + seg_w / 2, y + h / 2 + 5, opt, FS[1],
               t.text if is_active else t.dim, 700 if is_active else 400, "middle")
        if focus is not None and opt == focus:
            s.emit(f'<rect x="{sx-2:.1f}" y="{y-2}" width="{seg_w+4:.1f}" '
                   f'height="{h+4}" rx="{t.radius+3}" fill="none" '
                   f'stroke="{t.accent_sub}" stroke-width="2" '
                   f'stroke-dasharray="3 2"/>')                   # visible focus ring
    return h


# --- Canvas -------------------------------------------------------------------
s.rect(0, 0, W, H, t.bg)

M = 24                       # outer margin
CW = W - 2 * M               # content width (1392)

# ============================================================ R0 — control bar
R0_Y, R0_H = 24, 72
with s.group("R0-header-control-bar"):
    s.rect(M, R0_Y, CW, R0_H, t.surface, rx=t.radius, stroke=t.border, sw=1)

    # Title + persistent, subordinate disclosure.
    s.text(M + 20, R0_Y + 30, "US Treasury Yields", FS[3], t.text, 700)
    s.text(M + 20, R0_Y + 52,
           "descriptive market data — not investment advice", FS[0], t.dim, 400)

    # Latest Trading Date readout (tabular figures). Kept clear of the disclosure.
    dx = M + 340
    s.text(dx, R0_Y + 26, "Trading Date", FS[0], t.dim, 500)
    mono(dx, R0_Y + 50, "2026-06-30", FS[1], t.text, 600)

    # Live-updating: transient "Updated to [Trading Date]" chip beside the readout.
    ux = M + 440
    s.rect(ux, R0_Y + 25, 176, 22, t.elev, rx=6, stroke=t.ok, sw=1)
    s.text(ux + 12, R0_Y + 40, "↻ Updated to 2026-06-30", FS[0], t.ok, 600)

    # Live-status indicator: filled dot + text label (shape + word, never color alone).
    lx = M + 636
    s.text(lx, R0_Y + 26, "Status", FS[0], t.dim, 500)
    dot(lx + 6, R0_Y + 44, 4, t.ok)
    s.text(lx + 18, R0_Y + 50, "Live", FS[1], t.text, 600)
    s.text(lx + 52, R0_Y + 50, "· connected", FS[0], t.dim, 400)

    # Comparison-date control (drives R1 overlay only).
    cmp_w = 300
    tw_w = 250
    tw_x = M + CW - 20 - tw_w
    cmp_x = tw_x - 20 - cmp_w
    s.text(cmp_x, R0_Y + 26, "Compare (Yield Curve)", FS[0], t.dim, 500)
    custom_seg(cmp_x, R0_Y + 32, cmp_w,
               ["Latest only", "vs 1M", "vs 1Y", "Custom…"], active="vs 1Y")

    # Time-window control (drives R2 + R3 shared X range). Focus ring shown here.
    s.text(tw_x, R0_Y + 26, "Time window (Spread & legs)", FS[0], t.dim, 500)
    custom_seg(tw_x, R0_Y + 32, tw_w,
               ["6M", "1Y", "2Y", "5Y", "Max"], active="2Y", focus="2Y")

# ================================================= shared plot geometry (R2/R3)
PL = M + 72                  # plot left (room for Y labels)
PR = M + CW - 24            # plot right
NMONTHS = 24
XCROSS_M = 17               # linked-crosshair demo month


def tx(m):
    return PL + (m / NMONTHS) * (PR - PL)


TICK_M = [0, 4, 8, 12, 16, 20, 24]
TICK_LABEL = ["Jun '24", "Oct '24", "Feb '25", "Jun '25",
              "Oct '25", "Feb '26", "Jun '26"]


def interp(ctrl, m):
    for i in range(len(ctrl) - 1):
        m0, v0 = ctrl[i]
        m1, v1 = ctrl[i + 1]
        if m0 <= m <= m1:
            return v0 + (v1 - v0) * (m - m0) / (m1 - m0)
    return ctrl[-1][1]


SPREAD_CTRL = [(0, -50), (4, -62), (8, -58), (12, -42),
               (16, -24), (19, -6), (20, 3), (24, 12)]
TEN_CTRL = [(0, 4.20), (6, 4.05), (12, 3.95), (18, 4.00), (24, 4.05)]
spread = [interp(SPREAD_CTRL, m) for m in range(NMONTHS + 1)]
ten10 = [interp(TEN_CTRL, m) for m in range(NMONTHS + 1)]
two2 = [ten10[m] - spread[m] / 100.0 for m in range(NMONTHS + 1)]

# ============================================================ R1 — Yield Curve
R1_Y, R1_H = 112, 470
with s.group("R1-yield-curve-hero"):
    panel("r1", M, R1_Y, CW, R1_H, "Yield Curve",
          "latest Trading Date, Yield (%) by Tenor ordered by maturity")

    p_l = M + 84
    p_r = M + CW - 24
    p_t = R1_Y + 64
    p_b = R1_Y + R1_H - 44
    ymin, ymax = 3.5, 5.5

    def y1(v):
        return p_b - (v - ymin) / (ymax - ymin) * (p_b - p_t)

    # Y gridlines + tick labels + unit.
    for gv in [3.5, 4.0, 4.5, 5.0, 5.5]:
        gy = y1(gv)
        s.line(p_l, gy, p_r, gy, t.border, 1)
        mono(p_l - 12, gy + 4, f"{gv:.1f}", FS[0], t.dim, 400, "end")
    vtext(M + 30, (p_t + p_b) / 2, "Yield (%)", FS[0], t.dim)

    tenors = ["1M", "3M", "6M", "1Y", "2Y", "3Y",
              "5Y", "7Y", "10Y", "20Y", "30Y"]
    latest = [4.85, 4.70, 4.55, 4.30, 4.05, 3.95,
              3.90, 3.95, 4.05, None, 4.35]   # 20Y omitted (honest gap)
    hist = [5.30, 5.25, 5.15, 4.95, 4.70, 4.55,
            4.45, 4.48, 4.55, 4.80, 4.75]

    def cx(i):
        return p_l + i / (len(tenors) - 1) * (p_r - p_l)

    # X tenor ticks + labels.
    for i, ten in enumerate(tenors):
        x = cx(i)
        s.line(x, p_b, x, p_b + 5, t.border, 1)
        emph = ten in ("2Y", "10Y")
        s.text(x, p_b + 22, ten, FS[0],
               t.text if emph else t.dim, 600 if emph else 400, "middle")
    s.text((p_l + p_r) / 2, p_b + 40, "Tenor", FS[0], t.dim, 500, "middle")

    # Historical overlay (1Y ago): dashed + hollow squares — distinct w/o color.
    hpts = [(cx(i), y1(v)) for i, v in enumerate(hist)]
    polyline(hpts, t.text, sw=2, dash="7 5", opacity=0.75)
    for x, y in hpts:
        square(x, y, 3.5, t.surface, stroke=t.text, sw=1.6)

    # Latest curve: solid accent + filled circles; 20Y omitted -> line breaks.
    seg = [(cx(i), y1(v)) for i, v in enumerate(latest) if v is not None and i <= 8]
    polyline(seg, t.accent, sw=3)
    for i, v in enumerate(latest):
        if v is None:
            continue
        dot(cx(i), y1(v), 4.5, t.accent)
    # (30Y is plotted once by the loop above; it sits alone past the gap,
    #  intentionally not bridged across the missing 20Y — the dotted guide +
    #  Partial note below explain the break.)
    # Mark the omitted Tenor honestly: dotted guide, no plotted point at zero.
    gx = cx(9)
    s.emit(f'<line x1="{gx:.1f}" y1="{p_t}" x2="{gx:.1f}" y2="{p_b}" '
           f'stroke="{t.dim}" stroke-width="1" stroke-dasharray="2 4" opacity="0.6"/>')

    # Legend (top-right, inside panel) — real labels + style keys.
    lx = p_r - 300
    ly = R1_Y + 58
    s.rect(lx, ly, 300, 56, t.elev, rx=6, stroke=t.border, sw=1)
    s.emit(f'<line x1="{lx+16}" y1="{ly+20}" x2="{lx+44}" y2="{ly+20}" '
           f'stroke="{t.accent}" stroke-width="3"/>')
    dot(lx + 30, ly + 20, 4.5, t.accent)
    s.text(lx + 54, ly + 24, "Latest", FS[1], t.text, 600)
    mono(lx + 300 - 16, ly + 24, "2026-06-30", FS[0], t.dim, 400, "end")
    s.emit(f'<line x1="{lx+16}" y1="{ly+42}" x2="{lx+44}" y2="{ly+42}" '
           f'stroke="{t.text}" stroke-width="2" stroke-dasharray="7 5" opacity="0.75"/>')
    square(lx + 30, ly + 42, 3.5, t.surface, stroke=t.text, sw=1.6)
    s.text(lx + 54, ly + 46, "1Y ago", FS[1], t.text, 600)
    mono(lx + 300 - 16, ly + 46, "2025-06-28", FS[0], t.dim, 400, "end")

    # Representative NON-nominal (partial) state — honest, panel-local, legible.
    px = p_l
    py = p_b + 52
    cw = chip(px, py - 14, "Partial", t.danger, t.elev)
    s.text(px + cw + 10, py, "20Y omitted — no FRED print for this Trading Date "
           "(not drawn at zero, line breaks at the gap)", FS[0], t.dim, 400)

# ============================================================ R2 — 2s10s Spread
R2_Y, R2_H = 598, 236
with s.group("R2-2s10s-spread"):
    panel("r2", M, R2_Y, CW, R2_H, "2s10s Spread",
          "10Y − 2Y over time (basis points)")

    p_t = R2_Y + 46
    p_b = R2_Y + R2_H - 22
    smin, smax = -70, 20

    def y2(v):
        return p_b - (v - smin) / (smax - smin) * (p_b - p_t)

    z = y2(0)
    for gv in [20, -20, -40, -60]:
        gy = y2(gv)
        s.line(PL, gy, PR, gy, t.border, 1)
        mono(PL - 12, gy + 4, f"{gv:+d}", FS[0], t.dim, 400, "end")
    vtext(M + 24, (p_t + p_b) / 2, "Spread (bp)", FS[0], t.dim)

    # faint shared date gridlines
    for m in TICK_M:
        s.emit(f'<line x1="{tx(m):.1f}" y1="{p_t}" x2="{tx(m):.1f}" y2="{p_b}" '
               f'stroke="{t.border}" stroke-width="1" opacity="0.5"/>')

    # Cue 1 — shaded inverted region (fills only where spread < 0).
    top = [(tx(m), y2(min(spread[m], 0))) for m in range(NMONTHS + 1)]
    bot = [(tx(m), z) for m in range(NMONTHS, -1, -1)]
    polygon(top + bot, t.danger, opacity=0.16)

    # spread line (neutral color; negativity carried by shade+label+position)
    spts = [(tx(m), y2(spread[m])) for m in range(NMONTHS + 1)]
    polyline(spts, t.text, sw=2.4)

    # Cue 2 — emphasized zero line + label.
    s.line(PL, z, PR, z, t.text, 2)
    mono(PR - 4, z - 8, "0 bp", FS[0], t.text, 600, "end")

    # Cue 3 + 4 — "inverted" label sitting *below* the zero axis, in open shade.
    ix = tx(6)
    s.emit(f'<text x="{ix:.1f}" y="{y2(-22):.1f}" font-family="{t.font}" '
           f'font-size="{FS[1]}" font-weight="700" fill="{t.danger}" '
           f'text-anchor="middle">▼ inverted</text>')
    s.text(ix, y2(-22) + 16, "curve inverted (spread < 0)", FS[0], t.dim, 400, "middle")

# ============================================================ R3 — 2Y & 10Y legs
R3_Y, R3_H = 846, 236
with s.group("R3-2y-10y-series"):
    panel("r3", M, R3_Y, CW, R3_H, "2Y & 10Y", "underlying Yields over time (%)")

    p_t = R3_Y + 46
    p_b = R3_Y + R3_H - 40      # extra room for the shared X labels
    lmin, lmax = 3.6, 4.8

    def y3(v):
        return p_b - (v - lmin) / (lmax - lmin) * (p_b - p_t)

    for gv in [3.6, 4.0, 4.4, 4.8]:
        gy = y3(gv)
        s.line(PL, gy, PR, gy, t.border, 1)
        mono(PL - 12, gy + 4, f"{gv:.1f}", FS[0], t.dim, 400, "end")
    vtext(M + 24, (p_t + p_b) / 2, "Yield (%)", FS[0], t.dim)

    for m in TICK_M:
        s.emit(f'<line x1="{tx(m):.1f}" y1="{p_t}" x2="{tx(m):.1f}" y2="{p_b}" '
               f'stroke="{t.border}" stroke-width="1" opacity="0.5"/>')

    # 10Y — dashed + squares (secondary style)
    tp = [(tx(m), y3(ten10[m])) for m in range(NMONTHS + 1)]
    polyline(tp, t.text, sw=2, dash="7 5", opacity=0.8)
    for m in range(0, NMONTHS + 1, 3):
        square(tx(m), y3(ten10[m]), 3.2, t.surface, stroke=t.text, sw=1.5)

    # 2Y — solid accent + circles (primary style)
    wp = [(tx(m), y3(two2[m])) for m in range(NMONTHS + 1)]
    polyline(wp, t.accent, sw=2.6)
    for m in range(0, NMONTHS + 1, 3):
        dot(tx(m), y3(two2[m]), 3.6, t.accent)

    # Shared X-axis date labels (owned by the bottom panel of the stack).
    for m, lab in zip(TICK_M, TICK_LABEL):
        s.line(tx(m), p_b, tx(m), p_b + 5, t.border, 1)
        s.text(tx(m), p_b + 22, lab, FS[0], t.dim, 400, "middle")
    s.text((PL + PR) / 2, p_b + 40, "Trading Date — shared time axis with 2s10s Spread",
           FS[0], t.dim, 500, "middle")

    # Legend — labels + style keys (distinguishable without color).
    lx = PR - 250
    ly = R3_Y + 40
    s.rect(lx, ly, 250, 30, t.elev, rx=6, stroke=t.border, sw=1)
    s.emit(f'<line x1="{lx+14}" y1="{ly+15}" x2="{lx+40}" y2="{ly+15}" '
           f'stroke="{t.accent}" stroke-width="2.6"/>')
    dot(lx + 27, ly + 15, 3.6, t.accent)
    s.text(lx + 50, ly + 19, "2Y (solid)", FS[0], t.text, 600)
    s.emit(f'<line x1="{lx+140}" y1="{ly+15}" x2="{lx+166}" y2="{ly+15}" '
           f'stroke="{t.text}" stroke-width="2" stroke-dasharray="7 5"/>')
    square(lx + 153, ly + 15, 3.2, t.surface, stroke=t.text, sw=1.5)
    s.text(lx + 176, ly + 19, "10Y (dashed)", FS[0], t.text, 600)

# ===================================== linked crosshair + tooltips (R2 <-> R3)
with s.group("linked-crosshair-tooltips"):
    xc = tx(XCROSS_M)
    # one shared vertical crosshair spanning both time-series panels
    s.emit(f'<line x1="{xc:.1f}" y1="{R2_Y+46}" x2="{xc:.1f}" y2="{R3_Y+R3_H-40}" '
           f'stroke="{t.accent_sub}" stroke-width="1.5" stroke-dasharray="4 4"/>')

    # Keyboard affordance: the crosshair is arrow-key movable when a panel is
    # focused. Draw a focusable handle (with focus ring) at the top of the line.
    hw = 148
    hx = xc - hw / 2
    hy = R2_Y + 22
    s.rect(hx, hy, hw, 22, t.elev, rx=6, stroke=t.border, sw=1)
    s.text(xc, hy + 15, "◂ ▸  arrow keys", FS[0], t.accent_sub, 600, "middle")
    s.emit(f'<rect x="{hx-2:.1f}" y="{hy-2}" width="{hw+4}" height="26" rx="8" '
           f'fill="none" stroke="{t.accent_sub}" stroke-width="2" '
           f'stroke-dasharray="3 2"/>')  # visible keyboard focus ring

    # markers where the crosshair meets each series
    sp = -18
    s2 = R2_Y + 46
    s2b = R2_Y + R2_H - 22
    yc2 = s2b - (sp - (-70)) / (20 - (-70)) * (s2b - s2)
    dot(xc, yc2, 4.5, t.text, stroke=t.surface, sw=1.5)

    r3t, r3b = R3_Y + 46, R3_Y + R3_H - 40
    def y3c(v):
        return r3b - (v - 3.6) / (4.8 - 3.6) * (r3b - r3t)
    dot(xc, y3c(4.17), 4.5, t.accent, stroke=t.surface, sw=1.5)
    square(xc, y3c(3.99), 4, t.surface, stroke=t.text, sw=1.6)

    # R2 tooltip (placed left of the crosshair, clear of the "0 bp" axis label)
    tw_, th_ = 190, 54
    txp = xc - 14 - tw_
    typ = R2_Y + 52
    s.rect(txp, typ, tw_, th_, t.elev, rx=6, stroke=t.border, sw=1)
    mono(txp + 12, typ + 20, "2025-11-14", FS[0], t.text, 600)
    chip(txp + tw_ - 72, typ + 8, "inverted", t.danger, t.surface, w=60)
    mono(txp + 12, typ + 40, "spread  −18 bp", FS[0], t.text, 400)

    # R3 tooltip (also left of the crosshair, clear of the legend)
    typ3 = R3_Y + 52
    txp3 = xc - 14 - tw_
    s.rect(txp3, typ3, tw_, th_, t.elev, rx=6, stroke=t.border, sw=1)
    mono(txp3 + 12, typ3 + 20, "2Y 4.17%  10Y 3.99%", FS[0], t.text, 600)
    mono(txp3 + 12, typ3 + 40, "Δ  −18 bp", FS[0], t.text, 400)


# ===================================== NON-NOMINAL STATE VARIANTS (strip) =====
# Compact, clearly-labelled variants so the nominal page above stays legible
# while the full state matrix (loading / error / empty / degraded live) reads.
def state_header(x, y, region, state, state_fg):
    s.text(x + 16, y + 26, region, FS[1], t.text, 700)
    w = chip(x + 16 + len(region) * L.char_w(FS[1]) + 12, y + 12, state, state_fg, t.elev)
    return w


def ghost_axes(x, y, w, h):
    """Loading skeleton: ghosted axes + placeholder blocks, but NO fake data."""
    ax_l, ax_b = x + 40, y + h - 26
    ax_r, ax_t = x + w - 20, y + 44
    s.emit(f'<line x1="{ax_l}" y1="{ax_t}" x2="{ax_l}" y2="{ax_b}" '
           f'stroke="{t.border}" stroke-width="1" opacity="0.7"/>')
    s.emit(f'<line x1="{ax_l}" y1="{ax_b}" x2="{ax_r}" y2="{ax_b}" '
           f'stroke="{t.border}" stroke-width="1" opacity="0.7"/>')
    for i in range(1, 4):
        gy = ax_t + i * (ax_b - ax_t) / 4
        s.line(ax_l, gy, ax_r, gy, t.border, 1)
    # skeleton placeholder bars (elev), clearly not a data line
    for i, bw in enumerate((90, 60, 120)):
        s.rect(ax_l + 6 + i * 0, ax_t + 6 + i * 18, bw, 10, t.elev, rx=4)
    s.text((ax_l + ax_r) / 2, (ax_t + ax_b) / 2 + 20, "Loading…",
           FS[0], t.dim, 500, "middle")


STR_Y = 1110
with s.group("STATES-nonnominal-variants"):
    s.line(M, STR_Y, M + CW, STR_Y, t.border, 1)
    s.text(M, STR_Y + 24, "Non-nominal state variants",
           FS[1], t.text, 700)
    s.text(M + 250, STR_Y + 24,
           "compact previews of the state matrix — the panels above stay nominal",
           FS[0], t.dim, 400)

    row_y = STR_Y + 40
    row_h = 176
    gap = 16
    pw = (CW - 2 * gap) / 3
    x0 = M
    x1 = M + pw + gap
    x2 = M + 2 * (pw + gap)

    # ---- Loading skeleton ----
    s.rect(x0, row_y, pw, row_h, t.surface, rx=t.radius, stroke=t.border, sw=1)
    state_header(x0, row_y, "R2 · 2s10s Spread", "Loading", t.dim)
    ghost_axes(x0, row_y, pw, row_h)

    # ---- Error (panel-local) ----
    s.rect(x1, row_y, pw, row_h, t.surface, rx=t.radius, stroke=t.border, sw=1)
    state_header(x1, row_y, "R2 · 2s10s Spread", "Error", t.danger)
    cx1 = x1 + pw / 2
    s.text(cx1, row_y + 78, "⚠", FS[3], t.danger, 700, "middle")
    s.text(cx1, row_y + 104, "Couldn't load the 2s10s Spread —",
           FS[1], t.text, 600, "middle")
    s.text(cx1, row_y + 124, "query service unreachable.", FS[0], t.dim, 400, "middle")
    bw = L.char_w(FS[1]) * len("↻ Retry") + 36
    s.button(cx1 - bw / 2, row_y + 134, "↻ Retry", "default")

    # ---- Empty (with next action, not a blank zero axis) ----
    s.rect(x2, row_y, pw, row_h, t.surface, rx=t.radius, stroke=t.border, sw=1)
    state_header(x2, row_y, "R2 · 2s10s Spread", "Empty", t.dim)
    cx2 = x2 + pw / 2
    s.text(cx2, row_y + 84, "No 2s10s Spread data for this window.",
           FS[1], t.text, 600, "middle")
    s.text(cx2, row_y + 104, "Widen the Time window, or check ingestion.",
           FS[0], t.dim, 400, "middle")
    bw2 = L.char_w(FS[1]) * len("↻ Retry") + 36
    s.button(cx2 - bw2 / 2, row_y + 122, "↻ Retry", "default")

    # ---- R0 total-failure banner variant ----
    ban_y = row_y + row_h + 20
    ban_h = 52
    s.rect(M, ban_y, CW, ban_h, t.elev, rx=t.radius, stroke=t.danger, sw=1.5)
    s.text(M + 20, ban_y + 24, "R0 banner — serving tier unreachable",
           FS[0], t.dim, 600)
    s.text(M + 20, ban_y + 42, "⚠  Yields query gateway timed out — no panels "
           "could load.", FS[1], t.text, 600)
    # Filled danger button drawn from the theme's onDanger token (the library's
    # danger button hard-codes a ~4.44:1 label; onDanger gives AA-passing ink).
    rlabel = "↻ Retry"
    rfs, rh, rpad = FS[1], 36, 18
    rbw = int(L.char_w(rfs) * len(rlabel) + rpad * 2)
    rbx = M + CW - 20 - rbw
    s.rect(rbx, ban_y + 8, rbw, rh, t.danger, rx=t.radius)
    s.text(rbx + rbw / 2, ban_y + 8 + rh / 2 + rfs * 0.35, rlabel, rfs,
           ON_DANGER, 600, "middle")

    # ---- Live-status degraded variants (icon + word, never color alone) ----
    lv_y = ban_y + ban_h + 22
    s.text(M, lv_y, "Live-status variants", FS[0], t.dim, 700)
    ivy = lv_y + 24
    # Live — filled dot
    dot(M + 8, ivy - 4, 5, t.ok)
    s.text(M + 22, ivy, "Live", FS[1], t.text, 600)
    s.text(M + 22 + 42, ivy, "· SSE connected", FS[0], t.dim, 400)
    # Reconnecting — half-filled ring (distinct glyph)
    rx0 = M + 260
    s.emit(f'<circle cx="{rx0+8}" cy="{ivy-4}" r="5" fill="none" '
           f'stroke="{t.dim}" stroke-width="1.5"/>')
    s.emit(f'<path d="M {rx0+8} {ivy-9} A 5 5 0 0 1 {rx0+8} {ivy+1} Z" '
           f'fill="{t.dim}"/>')
    s.text(rx0 + 22, ivy, "Reconnecting…", FS[1], t.text, 600)
    s.text(rx0 + 22 + 128, ivy, "· retrying stream", FS[0], t.dim, 400)
    # Offline — hollow ring
    ox0 = M + 560
    s.emit(f'<circle cx="{ox0+8}" cy="{ivy-4}" r="5" fill="none" '
           f'stroke="{t.dim}" stroke-width="1.5"/>')
    s.text(ox0 + 22, ivy, "Offline", FS[1], t.text, 600)
    s.text(ox0 + 22 + 56, ivy, "· last update 2026-06-30", FS[0], t.dim, 400)
    # keyboard note
    s.text(M + 900, lv_y, "Keyboard", FS[0], t.dim, 700)
    s.text(M + 900, ivy, "Tab → visible focus ring (shown on 2Y); "
           "◂ ▸ move the crosshair.", FS[0], t.dim, 400)


# --- Write --------------------------------------------------------------------
out = s.render(W, H)
assert t.accent in out, "mockup must render from the theme's primary color"
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "layout.svg")
with open(path, "w") as f:
    f.write(out)
print(f"OK: {len(out)} bytes -> {path}")
print(f"primary={theme['color']['primary']} bg={theme['color']['bg']} "
      f"onPrimary AA={contrast(t.on_accent, t.accent):.2f}")
