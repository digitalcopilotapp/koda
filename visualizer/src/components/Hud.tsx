import { useEffect, useState } from "react";
import { useBrain } from "../store/brainStore";

type Tab = "regions" | "thoughts" | "observations" | "broca";

function useIsMobile(): boolean {
  const [m, setM] = useState(() => typeof window !== "undefined" && window.innerWidth < 820);
  useEffect(() => {
    const onR = () => setM(window.innerWidth < 820);
    window.addEventListener("resize", onR);
    return () => window.removeEventListener("resize", onR);
  }, []);
  return m;
}

export function Hud() {
  const regions = useBrain((s) => s.regions);
  const thoughts = useBrain((s) => s.thoughts);
  const observations = useBrain((s) => s.observations);
  const utterances = useBrain((s) => s.utterances);
  const isMobile = useIsMobile();
  const [tab, setTab] = useState<Tab>("regions");
  const [open, setOpen] = useState(true);
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

  if (isMobile) {
    return (
      <div style={mobileRoot}>
        <div style={{ ...mobileDrawer, transform: open ? "translateY(0)" : "translateY(calc(100% - 124px))" }}>
          <div style={drawerTabs}>
            {(["regions", "thoughts", "observations", "broca"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => { setTab(t); setOpen(true); }}
                style={{
                  ...tabBtn,
                  color: tab === t ? "#fff" : "#7a8499",
                  borderBottom: tab === t ? "2px solid #fff2c2" : "2px solid transparent",
                }}
              >
                {t}
              </button>
            ))}
            <button onClick={() => setOpen(!open)} style={collapseBtn} aria-label="toggle">
              {open ? "▾" : "▴"}
            </button>
          </div>
          <div style={drawerBody}>
            {tab === "regions" && <RegionsList regions={regions} />}
            {tab === "thoughts" && <ThoughtsList thoughts={thoughts} />}
            {tab === "observations" && <ObservationsList observations={observations} />}
            {tab === "broca" && <BrocaList utterances={utterances} />}
          </div>
          <div style={mobileInputBar}>
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="fala com o cérebro…"
              onKeyDown={(e) => { if (e.key === "Enter") send(); }}
              style={mobileInput}
              disabled={busy}
              autoComplete="off"
              autoCapitalize="off"
              autoCorrect="off"
              enterKeyHint="send"
            />
            <button onClick={send} disabled={busy || !text.trim()} style={mobileBtn}>
              {busy ? "…" : "↑"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={hudStyle}>
      <div style={panelStyle}>
        <h3 style={h3}>regions</h3>
        <RegionsList regions={regions} />
      </div>

      <div style={{ ...panelStyle, top: "auto", bottom: 88, maxHeight: 220, overflowY: "auto" }}>
        <h3 style={h3}>thoughts surfacing</h3>
        <ThoughtsList thoughts={thoughts} />
      </div>

      <div style={{ ...panelStyle, top: 16, left: "auto", right: 16, maxWidth: 360, maxHeight: 280, overflowY: "auto" }}>
        <h3 style={h3}>observations</h3>
        <ObservationsList observations={observations} />
      </div>

      <div style={{ ...panelStyle, top: "auto", bottom: 88, left: "auto", right: 16, maxWidth: 420 }}>
        <h3 style={h3}>broca</h3>
        <BrocaList utterances={utterances} />
      </div>

      <div style={inputBar}>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="fala com o cérebro…"
          onKeyDown={(e) => { if (e.key === "Enter") send(); }}
          style={inputStyle}
          disabled={busy}
          autoComplete="off"
        />
        <button onClick={send} disabled={busy || !text.trim()} style={btnStyle}>
          {busy ? "…" : "enviar"}
        </button>
      </div>
    </div>
  );
}

function RegionsList({ regions }: { regions: any }) {
  return (
    <>
      {Object.values(regions).map((r: any) => (
        <div key={r.name} style={{ display: "flex", alignItems: "center", gap: 8, margin: "6px 0" }}>
          <span style={{ width: 12, height: 12, borderRadius: 6, background: r.color, display: "inline-block" }} />
          <span style={{ flex: 1, fontSize: 13 }}>{r.name}</span>
          <span style={{ width: 96, height: 5, background: "#1a2030", borderRadius: 2, overflow: "hidden" }}>
            <span style={{ display: "block", width: `${Math.min(100, r.activation * 200)}%`, height: 5, background: r.color }} />
          </span>
        </div>
      ))}
    </>
  );
}

function ThoughtsList({ thoughts }: { thoughts: any[] }) {
  if (!thoughts.length) return <div style={muted}>(quiet)</div>;
  return (
    <>
      {thoughts.slice().reverse().map((t) => (
        <div key={t.id + t.t} style={{ fontSize: 13, margin: "5px 0", opacity: 0.5 + 0.5 * t.intensity }}>
          <span style={{ color: "#fff2c2" }}>·</span> {t.content}
        </div>
      ))}
    </>
  );
}

function ObservationsList({ observations }: { observations: any[] }) {
  if (!observations.length) return <div style={muted}>(no observations yet)</div>;
  return (
    <>
      {observations.slice().reverse().map((o) => (
        <div key={o.id + o.t} style={{ fontSize: 13, margin: "6px 0", lineHeight: 1.45 }}>
          <span style={{ color: kindColor(o.kind), fontFamily: "monospace", fontSize: 11 }}>{o.kind}</span>{" "}
          <span style={{ opacity: 0.85 }}>{o.content}</span>
        </div>
      ))}
    </>
  );
}

function BrocaList({ utterances }: { utterances: any[] }) {
  if (!utterances.length) return <div style={muted}>(silent)</div>;
  return (
    <>
      {utterances.slice().reverse().map((u, i) => (
        <div key={i} style={{ fontSize: 14, margin: "8px 0", lineHeight: 1.5 }}>{u.text}</div>
      ))}
    </>
  );
}

// ------------------------------------------------------------ styles (desktop)
const hudStyle: React.CSSProperties = { position: "absolute", inset: 0, pointerEvents: "none" };
const panelStyle: React.CSSProperties = {
  position: "absolute", top: 16, left: 16, background: "rgba(10,14,22,0.78)",
  border: "1px solid #1f2733", borderRadius: 10, padding: 12, minWidth: 220,
  pointerEvents: "auto", backdropFilter: "blur(6px)",
};
const h3: React.CSSProperties = {
  margin: "0 0 8px", fontSize: 11, letterSpacing: 1, textTransform: "uppercase", color: "#7a8499",
};
const muted: React.CSSProperties = { color: "#5a6477", fontSize: 13, fontStyle: "italic" };
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

// ------------------------------------------------------------- styles (mobile)
const mobileRoot: React.CSSProperties = {
  position: "absolute", inset: 0, pointerEvents: "none",
};
const mobileDrawer: React.CSSProperties = {
  position: "absolute", left: 0, right: 0, bottom: 0,
  background: "rgba(8,11,17,0.94)",
  borderTop: "1px solid #1f2733",
  borderTopLeftRadius: 16, borderTopRightRadius: 16,
  pointerEvents: "auto",
  display: "flex", flexDirection: "column",
  maxHeight: "65dvh",
  paddingBottom: "var(--safe-bottom)",
  transition: "transform 220ms ease-out",
  backdropFilter: "blur(10px)",
  boxShadow: "0 -10px 40px rgba(0,0,0,0.5)",
};
const drawerTabs: React.CSSProperties = {
  display: "flex", alignItems: "stretch",
  borderBottom: "1px solid #1a2030",
  paddingLeft: 4, paddingRight: 4,
};
const tabBtn: React.CSSProperties = {
  flex: 1, background: "transparent", border: "none",
  padding: "14px 4px", fontSize: 12, textTransform: "uppercase",
  letterSpacing: 1, cursor: "pointer",
};
const collapseBtn: React.CSSProperties = {
  background: "transparent", border: "none", color: "#7a8499",
  padding: "14px 14px", fontSize: 14, cursor: "pointer",
};
const drawerBody: React.CSSProperties = {
  flex: 1, overflowY: "auto", padding: "12px 16px", minHeight: 0,
};
const mobileInputBar: React.CSSProperties = {
  display: "flex", gap: 8, padding: "10px 12px",
  borderTop: "1px solid #1a2030", background: "rgba(8,11,17,0.96)",
};
const mobileInput: React.CSSProperties = {
  flex: 1, padding: "14px 16px", borderRadius: 12,
  border: "1px solid #1f2733",
  background: "#0f1320", color: "#e8ecf3",
  fontSize: 16, // 16+ prevents iOS zoom on focus
};
const mobileBtn: React.CSSProperties = {
  width: 56, height: 52, borderRadius: 12,
  border: "1px solid #2b3548", background: "#1a2438",
  color: "#e8ecf3", fontSize: 22, cursor: "pointer",
};

function kindColor(kind: string): string {
  switch (kind) {
    case "emotion_shift": return "#e85b6e";
    case "drive_active": return "#3da9fc";
    case "pattern_completion": return "#7a5af5";
    default: return "#7a8499";
  }
}
