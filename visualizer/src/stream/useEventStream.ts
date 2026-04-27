import { useEffect } from "react";
import { useBrain } from "../store/brainStore";

export function useEventStream(url = "/ws") {
  const applyEvent = useBrain((s) => s.applyEvent);
  const applySnapshot = useBrain((s) => s.applySnapshot);
  const decay = useBrain((s) => s.decay);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let alive = true;
    let retry = 0;

    const open = () => {
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      const full = url.startsWith("ws") ? url : `${proto}//${window.location.host}${url}`;
      ws = new WebSocket(full);
      ws.onopen = () => { retry = 0; };
      ws.onmessage = (m) => {
        const ev = JSON.parse(m.data);
        if (ev.type === "snapshot") applySnapshot(ev.payload);
        else applyEvent(ev);
      };
      ws.onclose = () => {
        if (!alive) return;
        retry = Math.min(retry + 1, 6);
        setTimeout(open, 500 * retry);
      };
      ws.onerror = () => ws?.close();
    };
    open();

    const decayInterval = setInterval(decay, 200);
    return () => {
      alive = false;
      clearInterval(decayInterval);
      ws?.close();
    };
  }, [url, applyEvent, applySnapshot, decay]);
}
