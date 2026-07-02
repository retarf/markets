import { useCurve } from "../api/hooks";
import { Panel, LegendItem } from "../components/Panel";
import { isIsoDate } from "../components/ComparisonControl";
import { YieldCurveChart } from "../charts/YieldCurveChart";
import { useMeasure } from "../charts/useMeasure";
import { TENOR_ORDER } from "../lib/constants";
import { tradingDate } from "../lib/format";
import { tokens } from "../tokens";

interface Props {
  comparison: string; // "" = latest only, else 1M/1Y/ISO
}

export function CurvePanel({ comparison }: Props) {
  const [ref, width] = useMeasure<HTMLDivElement>();
  const vs = comparison || null;
  const q = useCurve("latest", vs);

  const base = q.data?.base;
  const comp = q.data?.comparison;
  const isEmpty = !q.isLoading && !q.isError && (!base || base.points.length === 0);

  // Partial: name any tracked Tenors missing from the latest curve.
  const present = new Set(base?.points.map((p) => p.tenor));
  const missing = base ? TENOR_ORDER.filter((t) => !present.has(t)) : [];

  const comparisonMissing =
    vs && comp && (comp.resolved_trading_date === null || comp.points.length === 0);
  // A custom pick is an ISO date ("as of"); presets read "<n> ago".
  const comparisonLabel =
    comp && comp.resolved_trading_date
      ? isIsoDate(vs ?? "")
        ? `as of ${tradingDate(comp.resolved_trading_date)}`
        : `${vs} ago (${tradingDate(comp.resolved_trading_date)})`
      : undefined;

  // Partial: Tenors present in the latest curve but absent from the comparison
  // (e.g. the 20Y before its May-2020 reintroduction) — named, line breaks.
  const compPresent = new Set(comp?.points.map((p) => p.tenor));
  const comparisonOmitted =
    comp && comp.points.length > 0
      ? TENOR_ORDER.filter((t) => present.has(t) && !compPresent.has(t))
      : [];

  return (
    <Panel
      hero
      title="Yield Curve"
      subtitle={base ? tradingDate(base.trading_date) : undefined}
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      isEmpty={isEmpty}
      emptyMessage="No Yield Curve available"
      onRetry={() => q.refetch()}
      note={
        <>
          {missing.length > 0 && <span>Omitted Tenors (no data): {missing.join(", ")}. </span>}
          {comparisonOmitted.length > 0 && (
            <span>Comparison curve omits {comparisonOmitted.join(", ")} (no data at that date). </span>
          )}
          {comparisonMissing && <span>No curve for {isIsoDate(vs ?? "") ? vs : `${vs} ago`} — showing latest only.</span>}
        </>
      }
      legend={
        <>
          <LegendItem label={base ? tradingDate(base.trading_date) : "Latest"} color={tokens.primary} marker="line" />
          {vs && !comparisonMissing && (
            <LegendItem
              label={comparisonLabel ?? (isIsoDate(vs ?? "") ? (vs as string) : `${vs} ago`)}
              color={tokens.primarySubtle}
              marker="dashed"
              dash
            />
          )}
        </>
      }
    >
      <div ref={ref}>
        {base && (
          <YieldCurveChart
            width={width}
            base={base.points}
            baseDate={base.trading_date}
            comparison={vs && !comparisonMissing ? comp?.points : undefined}
            comparisonDate={comp?.resolved_trading_date}
            comparisonLabel={comparisonLabel}
          />
        )}
      </div>
    </Panel>
  );
}
