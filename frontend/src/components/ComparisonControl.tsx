import { tokens } from "../tokens";
import { COMPARISON_PRESETS } from "../lib/constants";

export const isIsoDate = (v: string): boolean => /^\d{4}-\d{2}-\d{2}$/.test(v);

interface Props {
  value: string; // "" | "1M" | "1Y" | "YYYY-MM-DD"
  onChange: (value: string) => void;
  /** Latest available Trading Date — upper bound for the custom picker. */
  maxDate?: string | null;
}

// Comparison-date control (R1 overlay): presets + a "Custom Trading Date…" input
// (ux-brief §6). A custom date is passed straight through as `vs=YYYY-MM-DD`; the
// API snaps to the nearest prior Trading Date and the panel labels the resolved
// date, so out-of-calendar picks are handled honestly rather than rejected.
export function ComparisonControl({ value, onChange, maxDate }: Props) {
  const custom = isIsoDate(value);

  return (
    <div role="group" aria-label="Compare" style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span style={{ color: tokens.dim, fontSize: 12 }}>Compare</span>
      <div
        style={{
          display: "inline-flex",
          border: `1px solid ${tokens.border}`,
          borderRadius: 6,
          overflow: "hidden",
        }}
      >
        {COMPARISON_PRESETS.map((opt) => {
          const active = !custom && opt.value === value;
          return (
            <button
              key={opt.value}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(opt.value)}
              style={segStyle(active)}
            >
              {opt.label}
            </button>
          );
        })}
        <button
          type="button"
          aria-pressed={custom}
          onClick={() => onChange(maxDate ?? new Date().toISOString().slice(0, 10))}
          style={segStyle(custom)}
        >
          Custom…
        </button>
      </div>
      {custom && (
        <input
          type="date"
          aria-label="Custom comparison Trading Date"
          value={value}
          max={maxDate ?? undefined}
          onChange={(e) => e.target.value && onChange(e.target.value)}
          style={{
            minHeight: 26,
            background: tokens.elev,
            color: tokens.text,
            border: `1px solid ${tokens.border}`,
            borderRadius: 6,
            padding: "2px 6px",
            fontSize: 12,
            colorScheme: "dark",
          }}
        />
      )}
    </div>
  );
}

function segStyle(active: boolean): React.CSSProperties {
  return {
    minHeight: 26,
    padding: "3px 10px",
    fontSize: 12,
    fontWeight: active ? 700 : 400,
    color: active ? tokens.text : tokens.dim,
    background: active ? tokens.elev : "transparent",
    border: "none",
    borderBottom: active ? `2px solid ${tokens.primary}` : "2px solid transparent",
    cursor: "pointer",
  };
}
