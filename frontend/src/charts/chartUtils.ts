import { isoToMs } from "../lib/format";
import type { SeriesPoint, SpreadPoint } from "../api/types";

// Shared plot margins so R2 (spread) and R3 (series) align pixel-for-pixel on
// the time axis — a date in one lines up with the same date in the other.
export const TS_MARGIN = { top: 12, right: 16, bottom: 28, left: 52 };

export const CHART_HEIGHT = 220;

export type Ms = number;

// Union time-domain across the two time-series panels for the current window,
// so both charts render the identical X scale.
export function sharedDomain(
  spread: SpreadPoint[] | undefined,
  series: Record<string, SeriesPoint[]> | undefined,
): [Ms, Ms] | null {
  const xs: Ms[] = [];
  spread?.forEach((p) => xs.push(isoToMs(p.trading_date)));
  if (series) {
    for (const pts of Object.values(series)) pts.forEach((p) => xs.push(isoToMs(p.trading_date)));
  }
  if (xs.length === 0) return null;
  const min = Math.min(...xs);
  const max = Math.max(...xs);
  return min === max ? [min - 8.64e7, max + 8.64e7] : [min, max];
}

// Split a date-ordered series into contiguous runs, breaking on gaps larger than
// `maxGapDays`. Gaps (holidays / missing prints) are rendered as breaks in the
// line, never bridged (honest presentation).
export function segmentsByGap<T extends { trading_date: string }>(
  points: T[],
  maxGapDays = 5,
): T[][] {
  if (points.length === 0) return [];
  const maxGap = maxGapDays * 8.64e7;
  const out: T[][] = [];
  let run: T[] = [points[0]];
  for (let i = 1; i < points.length; i++) {
    const dt = isoToMs(points[i].trading_date) - isoToMs(points[i - 1].trading_date);
    if (dt > maxGap) {
      out.push(run);
      run = [];
    }
    run.push(points[i]);
  }
  if (run.length) out.push(run);
  return out;
}

// Nearest point (by date) to a target ms — for hover/keyboard crosshair readout.
export function nearestByDate<T extends { trading_date: string }>(
  points: T[],
  targetMs: Ms,
): T | null {
  let best: T | null = null;
  let bestDist = Infinity;
  for (const p of points) {
    const d = Math.abs(isoToMs(p.trading_date) - targetMs);
    if (d < bestDist) {
      bestDist = d;
      best = p;
    }
  }
  return best;
}
