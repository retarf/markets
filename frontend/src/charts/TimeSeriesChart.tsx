import { useMemo } from "react";
import { AxisBottom, AxisLeft } from "@visx/axis";
import { Group } from "@visx/group";
import { scaleLinear, scaleTime } from "@visx/scale";
import { LinePath } from "@visx/shape";

import { isoToMs, tradingDate } from "../lib/format";
import { tokens } from "../tokens";
import {
  CHART_HEIGHT,
  Ms,
  TS_MARGIN,
  nearestByDate,
  segmentsByGap,
} from "./chartUtils";

export interface Datum {
  trading_date: string;
  value: number;
}

export interface SeriesSpec {
  key: string;
  label: string;
  points: Datum[];
  color: string;
  dash?: string; // non-color distinguishability (line style)
  strokeWidth?: number;
}

export interface Band {
  startMs: Ms;
  endMs: Ms;
}

export interface TooltipRow {
  label: string;
  value: string;
  emphasis?: boolean;
}

interface Props {
  width: number;
  height?: number;
  domain: [Ms, Ms];
  series: SeriesSpec[];
  yLabel: string;
  yFormat: (v: number) => string;
  zeroLine?: boolean;
  invertedBands?: Band[];
  hoveredMs: Ms | null;
  onHoverMs: (ms: Ms | null) => void;
  onKeyStep?: (dir: -1 | 1) => void;
  tooltipRows: (ms: Ms) => TooltipRow[];
  ariaLabel: string;
}

export function TimeSeriesChart({
  width,
  height = CHART_HEIGHT,
  domain,
  series,
  yLabel,
  yFormat,
  zeroLine = false,
  invertedBands = [],
  hoveredMs,
  onHoverMs,
  onKeyStep,
  tooltipRows,
  ariaLabel,
}: Props) {
  const innerW = Math.max(0, width - TS_MARGIN.left - TS_MARGIN.right);
  const innerH = height - TS_MARGIN.top - TS_MARGIN.bottom;

  const xScale = useMemo(
    () => scaleTime<number>({ domain: domain.map((d) => new Date(d)), range: [0, innerW] }),
    [domain, innerW],
  );

  const yScale = useMemo(() => {
    const vals = series.flatMap((s) => s.points.map((p) => p.value));
    if (zeroLine) vals.push(0);
    const min = vals.length ? Math.min(...vals) : 0;
    const max = vals.length ? Math.max(...vals) : 1;
    const pad = (max - min || 1) * 0.1;
    return scaleLinear<number>({ domain: [min - pad, max + pad], range: [innerH, 0], nice: true });
  }, [series, zeroLine, innerH]);

  if (width <= 0) return null;

  const px = (p: Datum) => xScale(new Date(isoToMs(p.trading_date)));
  const py = (p: Datum) => yScale(p.value);

  const handleMove = (e: React.MouseEvent<SVGRectElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    onHoverMs(xScale.invert(x).getTime());
  };

  const hoverX = hoveredMs != null ? xScale(new Date(hoveredMs)) : null;
  const rows = hoveredMs != null ? tooltipRows(hoveredMs) : [];
  const tooltipLeft = hoverX != null ? TS_MARGIN.left + hoverX : 0;
  const flip = hoverX != null && hoverX > innerW * 0.6;

  return (
    <div style={{ position: "relative" }}>
      <svg
        width={width}
        height={height}
        role="img"
        aria-label={ariaLabel}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") {
            e.preventDefault();
            onKeyStep?.(-1);
          } else if (e.key === "ArrowRight") {
            e.preventDefault();
            onKeyStep?.(1);
          }
        }}
      >
        <Group left={TS_MARGIN.left} top={TS_MARGIN.top}>
          {/* Inverted-region shading (cue 1) — sits below the zero line (cue 4). */}
          {invertedBands.map((b, i) => {
            const x0 = Math.max(0, xScale(new Date(b.startMs)));
            const x1 = Math.min(innerW, xScale(new Date(b.endMs)));
            const y0 = zeroLine ? yScale(0) : 0;
            return (
              <rect
                key={`band-${i}`}
                x={x0}
                y={y0}
                width={Math.max(1, x1 - x0)}
                height={innerH - y0}
                fill={tokens.danger}
                opacity={0.16}
              />
            );
          })}

          {/* Emphasized, labeled zero line (cues 2 + 3). */}
          {zeroLine && (
            <>
              <line
                x1={0}
                x2={innerW}
                y1={yScale(0)}
                y2={yScale(0)}
                stroke={tokens.dim}
                strokeWidth={1.5}
              />
              <text x={2} y={yScale(0) - 4} fill={tokens.dim} fontSize={11}>
                0 bp
              </text>
              {invertedBands.length > 0 && (
                <text
                  x={4}
                  y={yScale(0) + 14}
                  fill={tokens.danger}
                  fontSize={11}
                  fontWeight={700}
                >
                  inverted
                </text>
              )}
            </>
          )}

          {/* Series — each split into runs so gaps become breaks, not bridges. */}
          {series.map((s) =>
            segmentsByGap(s.points).map((seg, i) => (
              <LinePath<Datum>
                key={`${s.key}-${i}`}
                data={seg}
                x={px}
                y={py}
                stroke={s.color}
                strokeWidth={s.strokeWidth ?? 1.75}
                strokeDasharray={s.dash}
                curve={undefined}
              />
            )),
          )}

          {/* Crosshair + nearest-point markers. */}
          {hoverX != null && hoverX >= 0 && hoverX <= innerW && (
            <>
              <line
                x1={hoverX}
                x2={hoverX}
                y1={0}
                y2={innerH}
                stroke={tokens.text}
                strokeWidth={1}
                opacity={0.5}
              />
              {series.map((s) => {
                const near = nearestByDate(s.points, hoveredMs!);
                if (!near) return null;
                return (
                  <circle
                    key={`m-${s.key}`}
                    cx={px(near)}
                    cy={py(near)}
                    r={3.5}
                    fill={tokens.bg}
                    stroke={s.color}
                    strokeWidth={2}
                  />
                );
              })}
            </>
          )}

          <AxisLeft
            scale={yScale}
            numTicks={4}
            tickFormat={(v) => yFormat(v as number)}
            stroke={tokens.border}
            tickStroke={tokens.border}
            tickLabelProps={() => ({ fill: tokens.dim, fontSize: 10, dx: -4, dy: 3, textAnchor: "end" })}
            label={yLabel}
            labelProps={{ fill: tokens.dim, fontSize: 11, textAnchor: "middle" }}
          />
          <AxisBottom
            top={innerH}
            scale={xScale}
            numTicks={Math.max(2, Math.floor(innerW / 90))}
            stroke={tokens.border}
            tickStroke={tokens.border}
            tickLabelProps={() => ({ fill: tokens.dim, fontSize: 10, textAnchor: "middle" })}
          />

          {/* Full-area hover capture. */}
          <rect
            x={0}
            y={0}
            width={innerW}
            height={innerH}
            fill="transparent"
            onMouseMove={handleMove}
            onMouseLeave={() => onHoverMs(null)}
          />
        </Group>
      </svg>

      {rows.length > 0 && (
        <div
          role="status"
          style={{
            position: "absolute",
            top: TS_MARGIN.top,
            left: flip ? undefined : tooltipLeft + 10,
            right: flip ? width - tooltipLeft + 10 : undefined,
            background: tokens.elev,
            border: `1px solid ${tokens.border}`,
            borderRadius: 6,
            padding: "6px 8px",
            pointerEvents: "none",
            fontSize: 12,
            minWidth: 120,
          }}
        >
          <div style={{ color: tokens.dim, marginBottom: 2 }}>
            {tradingDate(new Date(hoveredMs!).toISOString().slice(0, 10))}
          </div>
          {rows.map((r) => (
            <div
              key={r.label}
              style={{ display: "flex", justifyContent: "space-between", gap: 12 }}
            >
              <span style={{ color: tokens.dim }}>{r.label}</span>
              <span
                className="num"
                style={{ color: r.emphasis ? tokens.text : tokens.text, fontWeight: r.emphasis ? 700 : 400 }}
              >
                {r.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
