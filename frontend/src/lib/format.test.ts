import { describe, expect, it } from "vitest";

import { bp, pct, tradingDate } from "./format";

describe("format", () => {
  it("pct renders 2 decimals with %", () => {
    expect(pct(4.174)).toBe("4.17%");
    expect(pct(null)).toBe("—");
  });

  it("bp rounds and signs basis points", () => {
    expect(bp(31)).toBe("+31 bp");
    expect(bp(-12.4)).toBe("-12 bp");
    expect(bp(undefined)).toBe("—");
  });

  it("tradingDate formats a full UTC date", () => {
    expect(tradingDate("2026-07-01")).toBe("Jul 1, 2026");
    expect(tradingDate(null)).toBe("—");
  });
});
