import { create } from "zustand";

export type RegionInfo = {
  name: string;
  color: string;
  anatomy: [number, number, number];
  activation: number;
};

export type NeuronNode = {
  id: string;
  region: string;
  concept: string;
  color: string;
  activation: number;
  fx?: number; fy?: number; fz?: number;     // anatomical anchor
  group: string;
  fireCount: number;
  lastFiredAt: number;
};

export type SynapseLink = {
  source: string;
  target: string;
  weight: number;
  lastSignalAt: number;
};

export type Thought = {
  id: string;
  content: string;
  intensity: number;
  t: number;
};

export type Observation = {
  id: string;
  t: number;
  kind: string;
  content: string;
  source: string;
  intensity: number;
};

type BrainState = {
  regions: Record<string, RegionInfo>;
  neurons: Record<string, NeuronNode>;
  synapses: Record<string, SynapseLink>;
  thoughts: Thought[];
  observations: Observation[];
  utterances: { text: string; t: number }[];
  applyEvent: (ev: any) => void;
  applySnapshot: (snapshot: any) => void;
  decay: () => void;
};

const synKey = (a: string, b: string) => `${a}->${b}`;

export const useBrain = create<BrainState>((set) => ({
  regions: {},
  neurons: {},
  synapses: {},
  thoughts: [],
  observations: [],
  utterances: [],

  applySnapshot: (snapshot) => {
    set((state) => {
      const regions: Record<string, RegionInfo> = { ...state.regions };
      const neurons: Record<string, NeuronNode> = { ...state.neurons };
      const synapses: Record<string, SynapseLink> = { ...state.synapses };
      for (const r of snapshot.regions || []) {
        regions[r.name] = {
          name: r.name,
          color: r.color,
          anatomy: r.anatomy as [number, number, number],
          activation: r.activation || 0,
        };
        const center = r.anatomy as [number, number, number];
        let i = 0;
        for (const n of r.neurons || []) {
          const pos = scatterAround(center, i++, (r.neurons || []).length);
          neurons[n.id] = {
            id: n.id,
            region: r.name,
            concept: n.concept,
            color: r.color,
            activation: n.activation || 0,
            fx: pos[0], fy: pos[1], fz: pos[2],
            group: r.name,
            fireCount: 0,
            lastFiredAt: 0,
          };
          for (const s of n.synapses || []) {
            const k = synKey(n.id, s.to);
            synapses[k] = { source: n.id, target: s.to, weight: s.w, lastSignalAt: 0 };
          }
        }
      }
      return { regions, neurons, synapses };
    });
  },

  applyEvent: (ev) => {
    const t = (ev.t as number) || Date.now() / 1000;
    set((state) => {
      switch (ev.type) {
        case "neuron.create": {
          const region = state.regions[ev.region];
          const center: [number, number, number] = (ev.anatomy as any) || region?.anatomy || [0, 0, 0];
          const count = Object.values(state.neurons).filter((n) => n.region === ev.region).length;
          const pos = scatterAround(center, count, count + 1);
          return {
            neurons: {
              ...state.neurons,
              [ev.id]: {
                id: ev.id, region: ev.region, concept: ev.concept || "",
                color: ev.color || region?.color || "#888", activation: 0,
                fx: pos[0], fy: pos[1], fz: pos[2], group: ev.region,
                fireCount: 0, lastFiredAt: 0,
              },
            },
          };
        }
        case "neuron.fire": {
          const n = state.neurons[ev.id];
          if (!n) return state;
          return {
            neurons: {
              ...state.neurons,
              [ev.id]: { ...n, activation: ev.intensity, fireCount: n.fireCount + 1, lastFiredAt: t },
            },
          };
        }
        case "synapse.signal": {
          const k = synKey(ev.from, ev.to);
          const existing = state.synapses[k];
          return {
            synapses: {
              ...state.synapses,
              [k]: {
                source: ev.from, target: ev.to,
                weight: ev.weight ?? existing?.weight ?? 0.2,
                lastSignalAt: t,
              },
            },
          };
        }
        case "synapse.strengthen": {
          const k = synKey(ev.from, ev.to);
          const existing = state.synapses[k];
          return {
            synapses: {
              ...state.synapses,
              [k]: {
                source: ev.from, target: ev.to,
                weight: ev.weight ?? existing?.weight ?? 0.2,
                lastSignalAt: existing?.lastSignalAt ?? 0,
              },
            },
          };
        }
        case "region.activate": {
          const r = state.regions[ev.region];
          if (!r) return state;
          return { regions: { ...state.regions, [ev.region]: { ...r, activation: ev.level } } };
        }
        case "thought.surface": {
          const next = [...state.thoughts, { id: ev.id || String(t), content: ev.content, intensity: ev.intensity, t }];
          return { thoughts: next.slice(-12) };
        }
        case "broca.utterance": {
          return { utterances: [...state.utterances, { text: ev.text, t }].slice(-6) };
        }
        case "observation.note": {
          const next = [
            ...state.observations,
            { id: ev.id, t, kind: ev.kind, content: ev.content, source: ev.source, intensity: ev.intensity },
          ];
          return { observations: next.slice(-30) };
        }
        default:
          return state;
      }
    });
  },

  decay: () => {
    set((state) => {
      const now = Date.now() / 1000;
      const neurons: Record<string, NeuronNode> = {};
      for (const [id, n] of Object.entries(state.neurons)) {
        neurons[id] = { ...n, activation: n.activation * 0.9 };
      }
      // age out very old synapses' visual signal but keep them
      const synapses: Record<string, SynapseLink> = {};
      for (const [k, s] of Object.entries(state.synapses)) {
        synapses[k] = { ...s, lastSignalAt: now - s.lastSignalAt > 8 ? 0 : s.lastSignalAt };
      }
      return { neurons, synapses };
    });
  },
}));

function scatterAround(center: [number, number, number], i: number, total: number): [number, number, number] {
  const radius = 60;
  const phi = Math.acos(1 - (2 * (i + 0.5)) / Math.max(total, 1));
  const theta = Math.PI * (1 + Math.sqrt(5)) * (i + 0.5);
  return [
    center[0] * 220 + radius * Math.sin(phi) * Math.cos(theta),
    center[1] * 220 + radius * Math.sin(phi) * Math.sin(theta),
    center[2] * 220 + radius * Math.cos(phi),
  ];
}
