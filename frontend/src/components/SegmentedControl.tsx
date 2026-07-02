import { tokens } from "../tokens";
import type { Preset } from "../lib/constants";

interface Props {
  label: string;
  options: Preset[];
  value: string;
  onChange: (value: string) => void;
}

// Preset segmented control. Active selection is indicated by more than color
// (fill + weight + aria-pressed), targets >= 24px (task 3.10 / UX brief §6).
export function SegmentedControl({ label, options, value, onChange }: Props) {
  return (
    <div role="group" aria-label={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span style={{ color: tokens.dim, fontSize: 12 }}>{label}</span>
      <div
        style={{
          display: "inline-flex",
          border: `1px solid ${tokens.border}`,
          borderRadius: 6,
          overflow: "hidden",
        }}
      >
        {options.map((opt) => {
          const active = opt.value === value;
          return (
            <button
              key={opt.value}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(opt.value)}
              style={{
                minHeight: 26,
                padding: "3px 10px",
                fontSize: 12,
                fontWeight: active ? 700 : 400,
                color: active ? tokens.text : tokens.dim,
                background: active ? tokens.elev : "transparent",
                border: "none",
                borderBottom: active ? `2px solid ${tokens.primary}` : "2px solid transparent",
                cursor: "pointer",
              }}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
