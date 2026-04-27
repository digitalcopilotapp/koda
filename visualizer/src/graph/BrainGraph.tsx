import { useEffect, useMemo, useRef } from "react";
import ForceGraph3D, { ForceGraphMethods } from "react-force-graph-3d";
import * as THREE from "three";
import { useBrain } from "../store/brainStore";

export function BrainGraph() {
  const neurons = useBrain((s) => s.neurons);
  const synapses = useBrain((s) => s.synapses);
  const fgRef = useRef<ForceGraphMethods>();

  const data = useMemo(() => {
    const nodes = Object.values(neurons).map((n) => ({
      id: n.id,
      name: `${n.region} · ${n.concept || n.id}`,
      activation: n.activation,
      color: n.color,
      fx: n.fx, fy: n.fy, fz: n.fz,
      lastFiredAt: n.lastFiredAt,
      region: n.region,
    }));
    const links = Object.values(synapses).map((s) => ({
      source: s.source,
      target: s.target,
      weight: s.weight,
      lastSignalAt: s.lastSignalAt,
    }));
    return { nodes, links };
  }, [neurons, synapses]);

  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;
    fg.d3Force("charge")?.strength(-12);
  }, []);

  return (
    <ForceGraph3D
      ref={fgRef as any}
      graphData={data}
      backgroundColor="#06080d"
      nodeRelSize={3}
      nodeOpacity={0.95}
      nodeThreeObject={(node: any) => {
        const intensity = Math.min(1, node.activation || 0);
        const radius = 1.6 + intensity * 4;
        const geometry = new THREE.SphereGeometry(radius, 12, 12);
        const color = new THREE.Color(node.color);
        if (intensity > 0.05) {
          // shift toward warm white when firing
          color.lerp(new THREE.Color("#fff2c2"), Math.min(0.9, intensity));
        }
        const material = new THREE.MeshStandardMaterial({
          color,
          emissive: color,
          emissiveIntensity: 0.4 + intensity * 1.6,
        });
        return new THREE.Mesh(geometry, material);
      }}
      linkOpacity={0.4}
      linkWidth={(l: any) => 0.2 + (l.weight || 0.2) * 1.6}
      linkColor={(l: any) => {
        const since = Date.now() / 1000 - (l.lastSignalAt || 0);
        if (since < 0.6) return "#fff2c2";
        if (since < 2) return "#7aa9ff";
        return "#3a4256";
      }}
      linkDirectionalParticles={(l: any) => {
        const since = Date.now() / 1000 - (l.lastSignalAt || 0);
        return since < 1 ? 2 : 0;
      }}
      linkDirectionalParticleWidth={2}
      linkDirectionalParticleSpeed={0.02}
      enableNodeDrag={false}
      cooldownTicks={0}
      warmupTicks={0}
    />
  );
}
