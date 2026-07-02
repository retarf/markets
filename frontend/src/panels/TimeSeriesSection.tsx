import { useMemo, useState } from "react";

import { useSeries, useSpread } from "../api/hooks";
import { Panel, LegendItem } from "../components/Panel";
import { TimeSeriesChart, type Band, type Datum } from "../charts/TimeSeriesChart";
import { sharedDomain, nearestByDate, type Ms } from "../charts/chartUtils";
import { useMeasure } from "../charts/useMeasure";
import { SERIES_TENORS } from "../lib/constants";
import { bp, isoToMs, pct } from "../lib/format";
import { tokens } from "../tokens";
import type { SpreadPoint } from "../api/types";

// Runs of consecutive inverted points -> shaded bands (spread < 0).
function invertedBands(spread: SpreadPoint[]): Band[] {
  const bands: Band[] = [];
  let start: number | null = null;
  let prev: number | null = null;
  for (const p of spread) {
    const ms = isoToMs(p.trading_date);
    if (p.is_inverted) {
      if (start === null) start = ms;
      prev = ms;
    } else if (start !== null) {
      bands.push({ startMs: start, endMs: prev ?? ms });
      start = null;
    }
  }
  if (start !== null) bands.push({ startMs: start, endMs: prev ?? start });
  return bands;
}

interface Props {
  window: string;
}

export function TimeSeriesSection({ window }: Props) {
  const spreadQ = useSpread(window);
  const seriesQ = useSeries([...SERIES_TENORS], window);

  const [spreadRef, spreadW] = useMeasure<HTMLDivElement>();
  const [seriesRef, seriesW] = useMeasure<HTMLDivElement>();

  // Linked crosshair shared by both panels.
  const [hoveredMs, setHoveredMs] = useState<Ms | null>(null);

  const spread = spreadQ.data;
  const series = seriesQ.data;

  const domain = useMemo(() => sharedDomain(spread, series), [spread, series]);

  // Keyboard stepping walks the spread panel's date axis.
  const dates = useMemo(
    () => (spread ?? []).map((p) => isoToMs(p.trading_date)).sort((a, b) => a - b),
    [spread],
  );
  const stepCrosshair = (dir: -1 | 1) => {
    if (dates.length === 0) return;
    if (hoveredMs === null) {
      setHoveredMs(dir === 1 ? dates[0] : dates[dates.length - 1]);
      return;
    }
    let idx = 0;
    let best = Infinity;
    dates.forEach((d, i) => {
      const dist = Math.abs(d - hoveredMs);
      if (dist < best) {
        best = dist;
        idx = i;
      }
    });
    const next = Math.min(dates.length - 1, Math.max(0, idx + dir));
    setHoveredMs(dates[next]);
  };

  const spreadEmpty = !spreadQ.isLoading && !spreadQ.isError && (spread?.length ?? 0) === 0;
  const seriesData = series ?? {};
  const legPresent = SERIES_TENORS.filter((t) => (seriesData[t]?.length ?? 0) > 0);
  const seriesEmpty = !seriesQ.isLoading && !seriesQ.isError && legPresent.length === 0;
  const missingLeg = SERIES_TENORS.filter((t) => (seriesData[t]?.length ?? 0) === 0);

  const spreadSpec: Datum[] = (spread ?? []).map((p) => ({
    trading_date: p.trading_date,
    value: p.spread_bps,
  }));
  const bands = spread ? invertedBands(spread) : [];

  const legColors: Record<string, string> = { "2Y": tokens.primary, "10Y": tokens.primarySubtle };
  const legDash: Record<string, string | undefined> = { "2Y": undefined, "10Y": "5 4" };

  return (
    <>
      <Panel
        title="2s10s Spread"
        subtitle="10Y − 2Y, basis points"
        isLoading={spreadQ.isLoading}
        isError={spreadQ.isError}
        error={spreadQ.error}
        isEmpty={spreadEmpty}
        emptyMessage="No 2s10s Spread data for this window"
        onRetry={() => spreadQ.refetch()}
        note={bands.length > 0 ? "Shaded region below the zero line = inverted (10Y < 2Y)." : undefined}
        legend={<LegendItem label="2s10s (bp)" color={tokens.text} marker="line" />}
      >
        <div ref={spreadRef}>
          {domain && (
            <TimeSeriesChart
              width={spreadW}
              domain={domain}
              ariaLabel="2s10s spread over time"
              series={[{ key: "spread", label: "2s10s", points: spreadSpec, color: tokens.text }]}
              yLabel="bp"
              yFormat={(v) => `${Math.round(v)}`}
              zeroLine
              invertedBands={bands}
              hoveredMs={hoveredMs}
              onHoverMs={setHoveredMs}
              onKeyStep={stepCrosshair}
              tooltipRows={(ms) => {
                const n = nearestByDate(spread ?? [], ms);
                if (!n) return [];
                return [
                  { label: "2s10s", value: bp(n.spread_bps), emphasis: true },
                  { label: "state", value: n.is_inverted ? "inverted" : "normal" },
                ];
              }}
            />
          )}
        </div>
      </Panel>

      <Panel
        title="2Y & 10Y"
        subtitle="Yields over time, %"
        isLoading={seriesQ.isLoading}
        isError={seriesQ.isError}
        error={seriesQ.error}
        isEmpty={seriesEmpty}
        emptyMessage="No 2Y / 10Y Yield data for this window"
        onRetry={() => seriesQ.refetch()}
        note={
          missingLeg.length > 0 && legPresent.length > 0
            ? `No data for ${missingLeg.join(", ")} in this window.`
            : undefined
        }
        legend={
          <>
            <LegendItem label="2Y" color={legColors["2Y"]} marker="line" />
            <LegendItem label="10Y" color={legColors["10Y"]} marker="dashed" dash />
          </>
        }
      >
        <div ref={seriesRef}>
          {domain && (
            <TimeSeriesChart
              width={seriesW}
              domain={domain}
              ariaLabel="2Y and 10Y yields over time"
              series={legPresent.map((t) => ({
                key: t,
                label: t,
                points: (seriesData[t] ?? []).map((p) => ({
                  trading_date: p.trading_date,
                  value: p.yield,
                })),
                color: legColors[t],
                dash: legDash[t],
              }))}
              yLabel="%"
              yFormat={(v) => v.toFixed(1)}
              hoveredMs={hoveredMs}
              onHoverMs={setHoveredMs}
              onKeyStep={stepCrosshair}
              tooltipRows={(ms) => {
                const two = nearestByDate(seriesData["2Y"] ?? [], ms);
                const ten = nearestByDate(seriesData["10Y"] ?? [], ms);
                const rows = [];
                if (two) rows.push({ label: "2Y", value: pct(two.yield) });
                if (ten) rows.push({ label: "10Y", value: pct(ten.yield) });
                if (two && ten)
                  rows.push({ label: "10Y−2Y", value: bp((ten.yield - two.yield) * 100), emphasis: true });
                return rows;
              }}
            />
          )}
        </div>
      </Panel>
    </>
  );
}
