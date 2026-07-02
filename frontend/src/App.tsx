import { useEffect, useState } from "react";

import { HeaderBar } from "./components/HeaderBar";
import { CurvePanel } from "./panels/CurvePanel";
import { TimeSeriesSection } from "./panels/TimeSeriesSection";
import { useCurve } from "./api/hooks";
import { useSSE } from "./state/useSSE";
import { ApiError } from "./api/client";
import { DEFAULT_WINDOW } from "./lib/constants";
import { tokens } from "./tokens";

export function App() {
  const [comparison, setComparison] = useState("");
  const [window, setWindow] = useState(DEFAULT_WINDOW);
  const live = useSSE();

  // Shared cache key with CurvePanel (dedup): drives the header date + banner.
  const curve = useCurve("latest", comparison || null);
  const latestDate = curve.data?.base.trading_date ?? live.lastUpdate;

  // Total serving-tier failure = gateway/network unreachable (status 0).
  const banner =
    curve.error instanceof ApiError && curve.error.status === 0 ? curve.error.message : null;

  // Transient "Updated to <date>" chip after each live event.
  const [chip, setChip] = useState<string | null>(null);
  useEffect(() => {
    if (live.updateTick === 0) return;
    setChip(live.lastUpdate);
    const t = setTimeout(() => setChip(null), 4000);
    return () => clearTimeout(t);
  }, [live.updateTick, live.lastUpdate]);

  return (
    <div style={{ minHeight: "100%", display: "flex", flexDirection: "column" }}>
      <HeaderBar
        latestDate={latestDate}
        comparison={comparison}
        onComparison={setComparison}
        window={window}
        onWindow={setWindow}
        status={live.status}
        updatedChip={chip}
        banner={banner}
        onBannerRetry={() => curve.refetch()}
      />

      <main
        style={{
          flex: 1,
          padding: tokens.space * 2,
          display: "grid",
          gap: tokens.space * 2,
          gridTemplateColumns: "1fr",
          maxWidth: 1400,
          width: "100%",
          margin: "0 auto",
        }}
      >
        <CurvePanel comparison={comparison} />
        <div
          style={{
            display: "grid",
            gap: tokens.space * 2,
            gridTemplateColumns: "1fr",
          }}
        >
          <TimeSeriesSection window={window} />
        </div>
      </main>
    </div>
  );
}
