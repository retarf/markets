import { tokens } from "../tokens";
import { tradingDate } from "../lib/format";
import { WINDOW_PRESETS } from "../lib/constants";
import { SegmentedControl } from "./SegmentedControl";
import { ComparisonControl } from "./ComparisonControl";
import { LiveStatus } from "./LiveStatus";
import type { LiveStatus as Status } from "../state/useSSE";

interface Props {
  latestDate: string | null;
  comparison: string;
  onComparison: (v: string) => void;
  window: string;
  onWindow: (v: string) => void;
  status: Status;
  updatedChip: string | null;
  banner: string | null;
  onBannerRetry?: () => void;
}

export function HeaderBar({
  latestDate,
  comparison,
  onComparison,
  window,
  onWindow,
  status,
  updatedChip,
  banner,
  onBannerRetry,
}: Props) {
  return (
    <header
      style={{
        borderBottom: `1px solid ${tokens.border}`,
        background: tokens.surface,
        padding: `${tokens.space * 1.5}px ${tokens.space * 2}px`,
        display: "flex",
        flexDirection: "column",
        gap: tokens.space,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 20, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>US Treasury Yields</h1>
          <span style={{ color: tokens.dim, fontSize: 13 }}>
            Trading Date{" "}
            <span className="num" style={{ color: tokens.text }}>
              {tradingDate(latestDate)}
            </span>
          </span>
          {updatedChip && (
            <span
              role="status"
              style={{
                fontSize: 12,
                color: tokens.bg,
                background: tokens.ok,
                borderRadius: 10,
                padding: "1px 8px",
              }}
            >
              Updated to {tradingDate(updatedChip)}
            </span>
          )}
        </div>

        <div style={{ flex: 1 }} />

        <ComparisonControl value={comparison} onChange={onComparison} maxDate={latestDate} />
        <SegmentedControl label="Window" options={WINDOW_PRESETS} value={window} onChange={onWindow} />
        <LiveStatus status={status} />
      </div>

      {banner && (
        <div
          role="alert"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            background: "rgba(240,82,75,0.12)",
            border: `1px solid ${tokens.danger}`,
            borderRadius: 6,
            padding: "6px 10px",
            fontSize: 13,
          }}
        >
          <span>⚠ Serving tier unreachable — {banner}</span>
          {onBannerRetry && (
            <button
              onClick={onBannerRetry}
              style={{
                minHeight: 24,
                padding: "2px 10px",
                background: tokens.elev,
                color: tokens.text,
                border: `1px solid ${tokens.border}`,
                borderRadius: 6,
                cursor: "pointer",
              }}
            >
              Retry
            </button>
          )}
        </div>
      )}

      <div style={{ color: tokens.dim, fontSize: 11 }}>
        Descriptive market data, not investment advice.
      </div>
    </header>
  );
}
