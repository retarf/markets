import type { ReactNode } from "react";

import { tokens } from "../tokens";
import { ApiError } from "../api/client";

interface Props {
  title: string;
  subtitle?: string;
  legend?: ReactNode;
  hero?: boolean;
  isLoading: boolean;
  isError: boolean;
  error?: unknown;
  isEmpty?: boolean;
  emptyMessage?: string;
  /** Partial-data note, e.g. omitted Tenors — rendered under the title. */
  note?: ReactNode;
  onRetry?: () => void;
  children: ReactNode;
}

export function Panel({
  title,
  subtitle,
  legend,
  hero,
  isLoading,
  isError,
  error,
  isEmpty,
  emptyMessage,
  note,
  onRetry,
  children,
}: Props) {
  return (
    <section
      aria-label={title}
      style={{
        background: tokens.surface,
        border: `1px solid ${tokens.border}`,
        borderRadius: tokens.radius,
        padding: tokens.space * 2,
        display: "flex",
        flexDirection: "column",
        gap: tokens.space,
        minWidth: 0,
      }}
    >
      <header style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: hero ? 20 : 16, fontWeight: 600 }}>{title}</h2>
          {subtitle && <div style={{ color: tokens.dim, fontSize: 12 }}>{subtitle}</div>}
        </div>
        {legend && <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>{legend}</div>}
      </header>
      {note && <div style={{ color: tokens.dim, fontSize: 12 }}>{note}</div>}

      <div style={{ position: "relative", minHeight: hero ? 300 : 220 }}>
        {isLoading ? (
          <Skeleton hero={hero} />
        ) : isError ? (
          <StateBox
            title="Couldn’t load this panel"
            body={error instanceof ApiError ? error.message : "Unexpected error"}
            actionLabel="Retry"
            onAction={onRetry}
          />
        ) : isEmpty ? (
          <StateBox
            title={emptyMessage ?? "No data"}
            body="Nothing to show for the current selection."
            actionLabel="Retry"
            onAction={onRetry}
          />
        ) : (
          children
        )}
      </div>
    </section>
  );
}

// Loading skeleton: ghosted axes only — never a placeholder data line that could
// be mistaken for real Yields.
function Skeleton({ hero }: { hero?: boolean }) {
  return (
    <div
      aria-hidden
      style={{
        height: hero ? 300 : 220,
        borderLeft: `1px solid ${tokens.border}`,
        borderBottom: `1px solid ${tokens.border}`,
        margin: "8px 0 8px 44px",
        opacity: 0.5,
        background:
          "repeating-linear-gradient(0deg, transparent, transparent 38px, rgba(138,147,166,0.08) 39px)",
      }}
    />
  );
}

function StateBox({
  title,
  body,
  actionLabel,
  onAction,
}: {
  title: string;
  body: string;
  actionLabel: string;
  onAction?: () => void;
}) {
  return (
    <div
      role="alert"
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        textAlign: "center",
        padding: 16,
      }}
    >
      <div style={{ fontWeight: 600 }}>{title}</div>
      <div className="num" style={{ color: tokens.dim, fontSize: 12, maxWidth: 360 }}>
        {body}
      </div>
      {onAction && (
        <button
          onClick={onAction}
          style={{
            marginTop: 4,
            minHeight: 28,
            padding: "4px 14px",
            background: tokens.elev,
            color: tokens.text,
            border: `1px solid ${tokens.border}`,
            borderRadius: 6,
            cursor: "pointer",
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

// Reusable legend swatch that encodes the line style, not just color.
export function LegendItem({
  label,
  color,
  dash,
  marker,
}: {
  label: string;
  color: string;
  dash?: boolean;
  marker: "line" | "dashed" | "square";
}) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12 }}>
      <svg width={22} height={12} aria-hidden>
        {marker === "square" ? (
          <rect x={7} y={2} width={8} height={8} fill="none" stroke={color} strokeWidth={1.5} />
        ) : (
          <line
            x1={0}
            y1={6}
            x2={22}
            y2={6}
            stroke={color}
            strokeWidth={2}
            strokeDasharray={dash ? "5 4" : undefined}
          />
        )}
      </svg>
      <span style={{ color: tokens.dim }}>{label}</span>
    </span>
  );
}
