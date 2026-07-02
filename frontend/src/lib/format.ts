// Numeric + date formatting. Every figure is rendered with these so the UI is
// consistent and honest (2-decimal %, integer bp, full Trading Date).

export const pct = (v: number | null | undefined): string =>
  v == null || Number.isNaN(v) ? "—" : `${v.toFixed(2)}%`;

export const bp = (v: number | null | undefined): string =>
  v == null || Number.isNaN(v) ? "—" : `${v >= 0 ? "+" : ""}${Math.round(v)} bp`;

// Full, unambiguous Trading Date (e.g. "Jul 1, 2026").
const DATE_FMT = new Intl.DateTimeFormat("en-US", {
  year: "numeric",
  month: "short",
  day: "numeric",
  timeZone: "UTC",
});

export const tradingDate = (iso: string | null | undefined): string => {
  if (!iso) return "—";
  const d = new Date(`${iso}T00:00:00Z`);
  return Number.isNaN(d.getTime()) ? iso : DATE_FMT.format(d);
};

export const isoToMs = (iso: string): number => new Date(`${iso}T00:00:00Z`).getTime();
