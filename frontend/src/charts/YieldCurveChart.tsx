import { useMemo, useState } from "react";
import { AxisBottom, AxisLeft } from "@visx/axis";
import { Group } from "@visx/group";
import { scaleLinear, scalePoint } from "@visx/scale";
import { LinePath } from "@visx/shape";

import type { CurvePoint } from "../api/types";
import { pct, tradingDate } from "../lib/format";
import { TENOR_ORDER } from "../lib/constants";
import { tokens } from "../tokens";

const MARGIN = { top: 16, right: 20, bottom: 32, left: 52 };

interface Props {
  width: number;
  height?: number;
  base: CurvePoint[];
  baseDate: string;
  comparison?: CurvePoint[];
  comparisonDate?: string | null;
  comparisonLabel?: string;
}

// Split into runs of consecutive present tenors so a missing Tenor breaks the
// line (omitted, never zero-filled or interpolated).
function runs(points: CurvePoint[]): CurvePoint[][] {
  const byTenor = new Map(points.map((p) => [p.tenor, p]));
  const out: CurvePoint[][] = [];
  let run: CurvePoint[] = [];
  for (const tenor of TENOR_ORDER) {
    const p = byTenor.get(tenor);
    if (p) {
      run.push(p);
    } else if (run.length) {
      out.push(run);
      run = [];
    }
  }
  if (run.length) out.push(run);
  return out;
}

export function YieldCurveChart({
  width,
  height = 300,
  base,
  baseDate,
  comparison,
  comparisonDate,
  comparisonLabel,
}: Props) {
  const [hoverTenor, setHoverTenor] = useState<string | null>(null);
  const innerW = Math.max(0, width - MARGIN.left - MARGIN.right);
  const innerH = height - MARGIN.top - MARGIN.bottom;

  const xScale = useMemo(
    () => scalePoint<string>({ domain: [...TENOR_ORDER], range: [0, innerW], padding: 0.5 }),
    [innerW],
  );

  const yScale = useMemo(() => {
    const vals = [...base, ...(comparison ?? [])].map((p) => p.yield);
    const min = vals.length ? Math.min(...vals) : 0;
    const max = vals.length ? Math.max(...vals) : 5;
    const pad = (max - min || 1) * 0.15;
    return scaleLinear<number>({ domain: [min - pad, max + pad], range: [innerH, 0], nice: true });
  }, [base, comparison, innerH]);

  if (width <= 0) return null;

  const px = (p: CurvePoint) => xScale(p.tenor) ?? 0;
  const py = (p: CurvePoint) => yScale(p.yield);

  const baseByTenor = new Map(base.map((p) => [p.tenor, p]));
  const compByTenor = new Map((comparison ?? []).map((p) => [p.tenor, p]));
  const hoverBase = hoverTenor ? baseByTenor.get(hoverTenor) : undefined;
  const hoverComp = hoverTenor ? compByTenor.get(hoverTenor) : undefined;
  const hoverX = hoverTenor ? (xScale(hoverTenor) ?? null) : null;
  const flip = hoverX != null && hoverX > innerW * 0.6;

  return (
    <div style={{ position: "relative" }}>
      <svg width={width} height={height} role="img" aria-label={`Yield curve for ${tradingDate(baseDate)}`}>
        <Group left={MARGIN.left} top={MARGIN.top}>
          {/* Comparison overlay first (behind): dashed + hollow square markers. */}
          {comparison &&
            comparison.length > 0 &&
            runs(comparison).map((seg, i) => (
              <LinePath<CurvePoint>
                key={`c-${i}`}
                data={seg}
                x={px}
                y={py}
                stroke={tokens.primarySubtle}
                strokeWidth={1.5}
                strokeDasharray="5 4"
              />
            ))}
          {comparison?.map((p) => (
            <rect
              key={`cm-${p.tenor}`}
              x={px(p) - 3}
              y={py(p) - 3}
              width={6}
              height={6}
              fill="none"
              stroke={tokens.primarySubtle}
              strokeWidth={1.5}
            />
          ))}

          {/* Latest curve (hero): solid + filled round markers. */}
          {runs(base).map((seg, i) => (
            <LinePath<CurvePoint>
              key={`b-${i}`}
              data={seg}
              x={px}
              y={py}
              stroke={tokens.primary}
              strokeWidth={2.5}
            />
          ))}
          {base.map((p) => (
            <circle key={`bm-${p.tenor}`} cx={px(p)} cy={py(p)} r={3} fill={tokens.primary} />
          ))}

          {hoverX != null && (
            <line x1={hoverX} x2={hoverX} y1={0} y2={innerH} stroke={tokens.text} strokeWidth={1} opacity={0.4} />
          )}

          <AxisLeft
            scale={yScale}
            numTicks={5}
            tickFormat={(v) => `${(v as number).toFixed(1)}%`}
            stroke={tokens.border}
            tickStroke={tokens.border}
            tickLabelProps={() => ({ fill: tokens.dim, fontSize: 10, dx: -4, dy: 3, textAnchor: "end" })}
            label="Yield (%)"
            labelProps={{ fill: tokens.dim, fontSize: 11, textAnchor: "middle" }}
          />
          <AxisBottom
            top={innerH}
            scale={xScale}
            stroke={tokens.border}
            tickStroke={tokens.border}
            tickLabelProps={() => ({ fill: tokens.dim, fontSize: 10, textAnchor: "middle" })}
          />

          {/* Per-tenor hover columns (>=24px targets where width allows). */}
          {TENOR_ORDER.map((tenor) => {
            const cx = xScale(tenor) ?? 0;
            const step = innerW / TENOR_ORDER.length;
            return (
              <rect
                key={`h-${tenor}`}
                x={cx - step / 2}
                y={0}
                width={step}
                height={innerH}
                fill="transparent"
                onMouseEnter={() => setHoverTenor(tenor)}
                onMouseLeave={() => setHoverTenor(null)}
              />
            );
          })}
        </Group>
      </svg>

      {hoverTenor && (hoverBase || hoverComp) && (
        <div
          role="status"
          style={{
            position: "absolute",
            top: MARGIN.top,
            left: flip ? undefined : MARGIN.left + (hoverX ?? 0) + 10,
            right: flip ? width - MARGIN.left - (hoverX ?? 0) + 10 : undefined,
            background: tokens.elev,
            border: `1px solid ${tokens.border}`,
            borderRadius: 6,
            padding: "6px 8px",
            pointerEvents: "none",
            fontSize: 12,
            minWidth: 130,
          }}
        >
          <div style={{ color: tokens.dim, marginBottom: 2 }}>Tenor {hoverTenor}</div>
          <Row label={tradingDate(baseDate)} value={pct(hoverBase?.yield)} />
          {comparison && (
            <Row
              label={comparisonLabel ?? tradingDate(comparisonDate ?? null)}
              value={pct(hoverComp?.yield)}
              dim
            />
          )}
          {hoverBase && hoverComp && (
            <Row
              label="Δ"
              value={`${(hoverBase.yield - hoverComp.yield >= 0 ? "+" : "")}${(
                (hoverBase.yield - hoverComp.yield) *
                100
              ).toFixed(0)} bp`}
              emphasis
            />
          )}
        </div>
      )}
    </div>
  );
}

function Row({ label, value, dim, emphasis }: { label: string; value: string; dim?: boolean; emphasis?: boolean }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
      <span style={{ color: dim ? tokens.dim : tokens.text }}>{label}</span>
      <span className="num" style={{ fontWeight: emphasis ? 700 : 400 }}>
        {value}
      </span>
    </div>
  );
}
