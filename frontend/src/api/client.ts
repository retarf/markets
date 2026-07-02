import type { CurveResponse, SeriesResponse, SpreadPoint } from "./types";

// The browser calls the api-gateway directly. Override with VITE_API_BASE.
export const API_BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined) ??
  "http://localhost:8090/api/yields";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function getJson<T>(path: string, params: Record<string, string>): Promise<T> {
  const qs = new URLSearchParams(params).toString();
  const url = `${API_BASE}${path}${qs ? `?${qs}` : ""}`;
  let res: Response;
  try {
    res = await fetch(url, { headers: { accept: "application/json" } });
  } catch (e) {
    // Network / CORS / gateway down.
    throw new ApiError(0, e instanceof Error ? e.message : "network error");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export function fetchCurve(date: string, vs: string | null): Promise<CurveResponse> {
  const params: Record<string, string> = { date };
  if (vs) params.vs = vs;
  return getJson<CurveResponse>("/curve", params);
}

export function fetchSpread(window: string): Promise<SpreadPoint[]> {
  return getJson<SpreadPoint[]>("/spread", { window });
}

export function fetchSeries(tenors: string[], window: string): Promise<SeriesResponse> {
  return getJson<SeriesResponse>("/series", { tenors: tenors.join(","), window });
}

export const streamUrl = (): string => `${API_BASE}/stream`;
