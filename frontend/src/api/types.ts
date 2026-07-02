// Typed mirror of the yields-query-service response models (served via the
// gateway at /api/yields/*). The rate field is serialized as JSON key "yield".

export interface CurvePoint {
  tenor: string;
  tenor_order: number;
  yield: number;
}

export interface Curve {
  trading_date: string; // ISO date (YYYY-MM-DD)
  points: CurvePoint[];
}

export interface CurveComparison {
  requested: string;
  resolved_trading_date: string | null;
  points: CurvePoint[];
}

export interface CurveResponse {
  base: Curve;
  comparison: CurveComparison | null;
}

export interface SpreadPoint {
  trading_date: string;
  spread_bps: number;
  is_inverted: boolean;
}

export interface SeriesPoint {
  trading_date: string;
  yield: number;
}

// GET /yields/series returns an object keyed by requested tenor label.
export type SeriesResponse = Record<string, SeriesPoint[]>;

// SSE `treasury.yields.ingested` payload.
export interface IngestedEvent {
  trading_date: string;
  tenors: string[];
}
