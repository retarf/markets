import { tokens } from "../tokens";
import type { LiveStatus as Status } from "../state/useSSE";

// Live indicator distinguishes states by text + icon glyph, not color alone.
const MAP: Record<Status, { glyph: string; text: string; color: string }> = {
  connecting: { glyph: "◌", text: "Connecting", color: tokens.dim },
  live: { glyph: "●", text: "Live", color: tokens.ok },
  reconnecting: { glyph: "◐", text: "Reconnecting", color: tokens.primarySubtle },
  offline: { glyph: "○", text: "Offline", color: tokens.danger },
};

export function LiveStatus({ status }: { status: Status }) {
  const s = MAP[status];
  return (
    <span
      role="status"
      aria-label={`Live status: ${s.text}`}
      style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, color: tokens.dim }}
    >
      <span aria-hidden style={{ color: s.color }}>
        {s.glyph}
      </span>
      {s.text}
    </span>
  );
}
