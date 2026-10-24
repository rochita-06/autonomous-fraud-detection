"use client";

import type { GraphData } from "@/lib/api";

const W = 560;
const H = 380;

/** Glowing identity-network visualization with animated edges. */
export default function NetworkGraph({ graph, centerId }: { graph: GraphData | null; centerId: string }) {
  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="card flex h-[380px] items-center justify-center p-4 text-xs" style={{ color: "var(--muted)" }}>
        Run or select an investigation to render the identity graph
      </div>
    );
  }

  const cx = W / 2;
  const cy = H / 2;
  const others = graph.nodes.filter((n) => n.id !== centerId);
  const pos = new Map<string, { x: number; y: number }>();
  pos.set(centerId, { x: cx, y: cy });
  const R = Math.min(W, H) / 2 - 56;
  others.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / Math.max(others.length, 1) - Math.PI / 2;
    pos.set(n.id, { x: cx + R * Math.cos(angle), y: cy + R * Math.sin(angle) });
  });

  const nodeColor = (n: GraphData["nodes"][number]) =>
    n.flagged ? "var(--status-critical)" : n.type === "device" ? "var(--series-2)" : "var(--series-1)";

  return (
    <div className="card card-hover p-5">
      <div className="mb-1 text-sm font-semibold">Identity Graph — {centerId}</div>
      <p className="mb-2 text-[11px]" style={{ color: "var(--muted)" }}>
        Shared devices, transfer partners and flagged connections
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={`Identity graph around ${centerId}`}>
        <defs>
          <filter id="node-glow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {graph.links.map((l, i) => {
          const a = pos.get(l.source);
          const b = pos.get(l.target);
          if (!a || !b) return null;
          const transfer = l.rel === "TRANSFERRED_TO";
          return (
            <line
              key={i}
              x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              className={transfer ? "edge-flow" : undefined}
              stroke={transfer ? "rgba(123,97,255,0.55)" : "rgba(79,140,255,0.4)"}
              strokeWidth="1.5"
            />
          );
        })}

        {graph.nodes.map((n) => {
          const p = pos.get(n.id);
          if (!p) return null;
          const isCenter = n.id === centerId;
          const fill = nodeColor(n);
          return (
            <g key={n.id} filter="url(#node-glow)">
              {n.type === "device" ? (
                <rect
                  x={p.x - 8} y={p.y - 8} width="16" height="16" rx="4"
                  fill={fill} stroke="rgba(5,8,22,0.9)" strokeWidth="2"
                />
              ) : (
                <circle
                  cx={p.x} cy={p.y} r={isCenter ? 13 : 9}
                  fill={fill} stroke="rgba(5,8,22,0.9)" strokeWidth="2"
                />
              )}
              <text
                x={p.x} y={p.y + (isCenter ? 28 : 23)}
                textAnchor="middle" fontSize="10" fill="var(--ink-2)"
              >
                {n.id}{n.flagged ? " ⚑" : ""}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[10px]" style={{ color: "var(--ink-2)" }}>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "var(--series-1)" }} /> user
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-[2px]" style={{ background: "var(--series-2)" }} /> device
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "var(--status-critical)" }} /> flagged ⚑
        </span>
        <span>— shared device · animated = transfer</span>
      </div>
    </div>
  );
}
