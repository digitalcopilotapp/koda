import { useState } from "react";
import { useBrain } from "../store/brainStore";

export function Hud() {
  const regions = useBrain((s) => s.regions);
  const thoughts = useBrain((s) => s.thoughts);
  const utterances = useBrain((s) => s.utterances);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  const send = async () => {
    if (!text.trim() || busy) return;
    setBusy(true);
    try {
      await fetch("/turn", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text }),
      });
      setText("");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={hudStyle}>
      <div style={panelStyle}>
        <h3 style={h3}>regions</h3>
        {Object.values(regions).map((r) => (
          <div key={r.name} style={{ display: "flex", alignItems: "center", gap: 8, margin: "4px 0" }}>
            <span style={{ width: 10, height: 10, borderRadius: 5, background: r.color, display: "inline-block" }} />
            <span style={{ flex: 1, fontSize: 12 }}>{r.name}</span>
            <span style={{ width: 80, height: 4, background: "#1a2030", borderRadius: 2, overflow: "hidden" }}>
              <span style={{ display: "block", width: `${Math.min(100, r.activation * 200)}%`, height: 4, background: r.color }} />
            </span>
          </div>
        ))}
      </div>

      <div style={{ ...panelStyle, top: "auto", bottom: 88, maxHeight: 220, overflowY: "auto" }}>
        <h3 style={h3}>thoughts surfacing</h3>
        {thoughts.length === 0 && <div style={muted}>(quiet)</div>}
        {thoughts.slice().reverse().map((t) => (
          <div key={t.id + t.t} style={{ fontSize: 12, margin: "3px 0", opacity: 0.5 + 0.5 * t.intensity }}>
            <span style={{ color: "#fff2c2" }}>·</span> {t.content}
          </div>
        ))}
      </div>

      <div style={{ ...panelStyle, top: "auto", bottom: 88, left: "auto", right: 16, maxWidth: 420 }}>
        <h3 style={h3}>broca</h3>
        {utterances.length === 0 && <div style={muted}>(silent)</div>}
        {utterances.slice().reverse().map((u, i) => (
          <div key={i} style={{ fontSize: 13, margin: "6px 0", lineHeight: 1.45 }}>{u.text}</div>
        ))}
      </div>

      <div style={inputBar}>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="fala com o cérebro…"
          onKeyDown={(e) => { if (e.key === "Enter") send(); }}
          style={inputStyle}
          disabled={busy}
        />
        <button onClick={send} disabled={busy || !text.trim()} style={btnStyle}>
          {busy ? "…" : "enviar"}
        </button>
      </div>
    </div>
  );
}

const hudStyle: React.CSSProperties = { position: "absolute", inset: 0, pointerEvents: "none" };
const panelStyle: React.CSSProperties = {
  position: "absolute", top: 16, left: 16, background: "rgba(10,14,22,0.78)",
  border: "1px solid #1f2733", borderRadius: 10, padding: 12, minWidth: 220,
  pointerEvents: "auto", backdropFilter: "blur(6px)",
};
const h3: React.CSSProperties = { margin: "0 0 8px", fontSize: 11, letterSpacing: 1, textTransform: "uppercase", color: "#7a8499" };
const muted: React.CSSProperties = { color: "#5a6477", fontSize: 12, fontStyle: "italic" };
const inputBar: React.CSSProperties = {
  position: "absolute", bottom: 16, left: 16, right: 16,
  display: "flex", gap: 8, pointerEvents: "auto",
};
const inputStyle: React.CSSProperties = {
  flex: 1, padding: "12px 14px", borderRadius: 8, border: "1px solid #1f2733",
  background: "rgba(10,14,22,0.85)", color: "#e8ecf3", fontSize: 14,
};
const btnStyle: React.CSSProperties = {
  padding: "0 20px", borderRadius: 8, border: "1px solid #2b3548",
  background: "#1a2438", color: "#e8ecf3", fontSize: 14, cursor: "pointer",
};
