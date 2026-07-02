import { useCallback, useRef, useState } from "react";

// Reports the content width of a container (responsive charts) via ResizeObserver.
// Uses a *callback ref* so the observer attaches whenever the node mounts — the
// charted node only appears after the panel's loading skeleton clears, so an
// effect with `[]` deps would observe a null ref and never update.
export function useMeasure<T extends HTMLElement>(): [(node: T | null) => void, number] {
  const [width, setWidth] = useState(0);
  const roRef = useRef<ResizeObserver | null>(null);

  const ref = useCallback((node: T | null) => {
    roRef.current?.disconnect();
    if (node) {
      const ro = new ResizeObserver((entries) => {
        setWidth(entries[0]?.contentRect.width ?? 0);
      });
      ro.observe(node);
      roRef.current = ro;
    }
  }, []);

  return [ref, width];
}
