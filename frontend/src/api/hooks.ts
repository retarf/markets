import { useQuery } from "@tanstack/react-query";

import { fetchCurve, fetchSeries, fetchSpread } from "./client";
import type { CurveResponse, SeriesResponse, SpreadPoint } from "./types";

// Keys are colocated so the SSE hook can invalidate the whole "yields" tree.
export const yieldsKey = ["yields"] as const;

export function useCurve(date: string, vs: string | null) {
  return useQuery<CurveResponse>({
    queryKey: [...yieldsKey, "curve", date, vs ?? ""],
    queryFn: () => fetchCurve(date, vs),
  });
}

export function useSpread(window: string) {
  return useQuery<SpreadPoint[]>({
    queryKey: [...yieldsKey, "spread", window],
    queryFn: () => fetchSpread(window),
  });
}

export function useSeries(tenors: string[], window: string) {
  return useQuery<SeriesResponse>({
    queryKey: [...yieldsKey, "series", tenors.join(","), window],
    queryFn: () => fetchSeries(tenors, window),
  });
}
