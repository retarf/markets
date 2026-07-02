import { describe, expect, it } from "vitest";

import { nearestByDate, segmentsByGap, sharedDomain } from "./chartUtils";
import { isoToMs } from "../lib/format";

const d = (s: string, value = 0) => ({ trading_date: s, value });

describe("segmentsByGap", () => {
  it("breaks the line on a gap larger than the threshold", () => {
    const pts = [d("2026-01-05"), d("2026-01-06"), d("2026-02-01"), d("2026-02-02")];
    const segs = segmentsByGap(pts);
    expect(segs).toHaveLength(2);
    expect(segs[0]).toHaveLength(2);
    expect(segs[1]).toHaveLength(2);
  });

  it("keeps consecutive dates in one run", () => {
    const pts = [d("2026-01-05"), d("2026-01-06"), d("2026-01-07")];
    expect(segmentsByGap(pts)).toHaveLength(1);
  });
});

describe("nearestByDate", () => {
  it("returns the closest point to a target", () => {
    const pts = [d("2026-01-01"), d("2026-06-01"), d("2026-12-01")];
    const near = nearestByDate(pts, isoToMs("2026-05-20"));
    expect(near?.trading_date).toBe("2026-06-01");
  });
});

describe("sharedDomain", () => {
  it("spans the union of spread and series dates", () => {
    const spread = [
      { trading_date: "2025-01-02", spread_bps: 30, is_inverted: false },
      { trading_date: "2026-07-01", spread_bps: 31, is_inverted: false },
    ];
    const dom = sharedDomain(spread, { "2Y": [{ trading_date: "2024-06-01", yield: 4 }] });
    expect(dom).not.toBeNull();
    expect(dom![0]).toBe(isoToMs("2024-06-01"));
    expect(dom![1]).toBe(isoToMs("2026-07-01"));
  });

  it("returns null with no data", () => {
    expect(sharedDomain([], {})).toBeNull();
  });
});
