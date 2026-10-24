"use client";

import type { GraphData } from "@/lib/api";

const W = 420;
const H = 300;

export default function GraphView({ graph, centerId }: { graph: GraphData | null; centerId: string }) {
  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="card flex h-[300px] items-center justify-center p-4 text-xs" style={{ color: "var(--muted)" }}>
        Select an investigation to see the identity graph
      </div>
    );
  }

  const cx = W / 2;
  const cy = H / 2;
  const others = graph.nodes.filter((n) => n.id !== centerId);
  const pos = new Map<string, { x: number; y: number }>();
  pos.set(centerId, { x: cx, y: cy });
  const R = Math.min(W, H) / 2 - 46;
  others.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / Math.max(others.length, 1) - Math.PI / 2;
    pos.set(n.id, { x: cx + R * Math.cos(angle), y: cy + R * Math.sin(angle) });
  });

  return (
    <div className="card p-4">
      <div className="mb-1 text-sm font-medium">Identity graph — {centerId}</div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={`Identity graph around ${centerId}`}>
        {graph.links.map((l, i) => {
          const a = pos.get(l.source);
          const b = pos.get(l.target);
          if (!a || !b) return null;
          return (
            <line
              key={i}
              x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              stroke="var(--baseline)"
              strokeWidth="1.5"
              strokeDasharray={l.rel === "TRANSFERRED_TO" ? "5 4" : undefined}
            />
          );
        })}
        {graph.nodes.map((n) => {
          const p = pos.get(n.id);
          if (!p) return null;
          const isCenter = n.id === centerId;
          const fill = n.flagged
            ? "var(--status-critical)"
            : n.type === "device"
              ? "var(--series-2)"
              : "var(--series-1)";
          return (
            <g key={n.id}>
              {n.type === "device" ? (
                <rect x={p.x - 7} y={p.y - 7} width="14" height="14" rx="3" fill={fill} stroke="var(--surface)" strokeWidth="2" />
              ) : (
                <circle cx={p.x} cy={p.y} r={isCenter ? 11 : 8} fill={fill} stroke="var(--surface)" strokeWidth="2" />
              )}
              <text x={p.x} y={p.y + (isCenter ? 24 : 20)} textAnchor="middle" fontSize="9" fill="var(--ink-2)">
                {n.id}{n.flagged ? " ⚑" : ""}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-[10px]" style={{ color: "var(--ink-2)" }}>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "var(--series-1)" }} /> user
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-[2px]" style={{ background: "var(--series-2)" }} /> device
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "var(--status-critical)" }} /> flagged ⚑
        </span>
        <span>— shared device &nbsp;· &nbsp;- - transfer</span>
      </div>
    </div>
  );
}
