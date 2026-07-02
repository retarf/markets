// Tenor order by maturity — the X-axis ordering for the Yield Curve (R1).
export const TENOR_ORDER = [
  "1M",
  "3M",
  "6M",
  "1Y",
  "2Y",
  "3Y",
  "5Y",
  "7Y",
  "10Y",
  "20Y",
  "30Y",
] as const;

export interface Preset {
  label: string;
  value: string;
}

// Time-window control (R2 + R3 shared X range). Default 2Y per the UX brief.
export const WINDOW_PRESETS: Preset[] = [
  { label: "6M", value: "6M" },
  { label: "1Y", value: "1Y" },
  { label: "2Y", value: "2Y" },
  { label: "5Y", value: "5Y" },
  { label: "Max", value: "max" },
];
export const DEFAULT_WINDOW = "2Y";

// Comparison-date control (R1 overlay only). "Latest only" = no overlay.
export const COMPARISON_PRESETS: Preset[] = [
  { label: "Latest only", value: "" },
  { label: "vs 1M", value: "1M" },
  { label: "vs 1Y", value: "1Y" },
];

// The two legs the series panel (R3) tracks.
export const SERIES_TENORS = ["2Y", "10Y"] as const;
