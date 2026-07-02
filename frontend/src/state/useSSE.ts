import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { streamUrl } from "../api/client";
import { yieldsKey } from "../api/hooks";
import type { IngestedEvent } from "../api/types";

export type LiveStatus = "connecting" | "live" | "reconnecting" | "offline";

export interface LiveState {
  status: LiveStatus;
  /** Trading Date of the most recent live update, for the transient chip. */
  lastUpdate: string | null;
  /** Monotonic tick so a consumer can trigger the "Updated to" chip each event. */
  updateTick: number;
}

// Subscribes to the gateway SSE stream. On `yields.ingested`, invalidates the
// yields query tree so panels refetch and redraw. EventSource auto-reconnects;
// we surface connecting/live/reconnecting/offline for the header indicator.
export function useSSE(): LiveState {
  const qc = useQueryClient();
  const [state, setState] = useState<LiveState>({
    status: "connecting",
    lastUpdate: null,
    updateTick: 0,
  });
  // Once we've been connected, a later error is a *reconnect*, not a cold start.
  const everConnected = useRef(false);

  useEffect(() => {
    const es = new EventSource(streamUrl());

    es.onopen = () => {
      everConnected.current = true;
      setState((s) => ({ ...s, status: "live" }));
    };

    es.addEventListener("yields.ingested", (ev) => {
      let payload: IngestedEvent | null = null;
      try {
        payload = JSON.parse((ev as MessageEvent).data) as IngestedEvent;
      } catch {
        /* ignore malformed frame */
      }
      qc.invalidateQueries({ queryKey: yieldsKey });
      setState((s) => ({
        status: "live",
        lastUpdate: payload?.trading_date ?? s.lastUpdate,
        updateTick: s.updateTick + 1,
      }));
    });

    es.onerror = () => {
      // EventSource retries on its own; reflect the drop in the indicator.
      setState((s) => ({
        ...s,
        status: everConnected.current ? "reconnecting" : "offline",
      }));
    };

    return () => es.close();
  }, [qc]);

  return state;
}
