"use client";

import { useState } from "react";
import type { InvestigationSummary } from "@/lib/api";

const W = 640;
const H = 220;
const PAD = { top: 14, right: 16, bottom: 26, left: 36 };

const ACTION_COLOR: Record<string, string> = {
  allow: "var(--status-good)",
  review: "var(--status-warning)",
  block: "var(--status-critical)",
};

export default function ScoreChart({ items }: { items: InvestigationSummary[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const data = [...items].reverse(); // oldest -> newest

  const iw = W - PAD.left - PAD.right;
  const ih = H - PAD.top - PAD.bottom;
  const x = (i: number) => PAD.left + (data.length <= 1 ? iw / 2 : (i / (data.length - 1)) * iw);
  const y = (score: number) => PAD.top + (1 - score) * ih;

  const path = data.map((d, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(d.fraud_score).toFixed(1)}`).join(" ");

  return (
    <div className="card p-4">
      <div className="mb-1 text-sm font-medium">Fraud score — recent investigations</div>
      {data.length === 0 ? (
        <div className="flex h-[220px] items-center justify-center text-sm" style={{ color: "var(--muted)" }}>
          No investigations yet — start the simulator
        </div>
      ) : (
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Fraud scores of recent investigations over time">
          {/* gridlines */}
          {[0, 0.25, 0.5, 0.75, 1].map((v) => (
            <g key={v}>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)} stroke="var(--grid)" strokeWidth="1" />
              <text x={PAD.left - 6} y={y(v) + 3.5} textAnchor="end" fontSize="10" fill="var(--muted)" className="tabular">
                {v.toFixed(2)}
              </text>
            </g>
          ))}
          {/* thresholds */}
          {[
            { v: 0.5, label: "review ≥ 0.5", color: "var(--status-warning)" },
            { v: 0.8, label: "block ≥ 0.8", color: "var(--status-critical)" },
          ].map((t) => (
            <g key={t.v}>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(t.v)} y2={y(t.v)} stroke={t.color} strokeWidth="1" strokeDasharray="4 4" opacity="0.7" />
              <text x={W - PAD.right} y={y(t.v) - 4} textAnchor="end" fontSize="9" fill="var(--ink-2)">
                {t.label}
              </text>
            </g>
          ))}
          {/* series line */}
          {data.length > 1 && <path d={path} fill="none" stroke="var(--series-1)" strokeWidth="2" opacity="0.55" />}
          {/* points, colored by decided action */}
          {data.map((d, i) => (
            <circle
              key={d.id}
              cx={x(i)}
              cy={y(d.fraud_score)}
              r={hover === i ? 6 : 4}
              fill={ACTION_COLOR[d.action] ?? "var(--series-1)"}
              stroke="var(--surface)"
              strokeWidth="2"
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
            />
          ))}
          {/* hover tooltip */}
          {hover !== null && data[hover] && (
            <g pointerEvents="none">
              {(() => {
                const d = data[hover];
                const tx = Math.min(Math.max(x(hover) - 70, PAD.left), W - PAD.right - 140);
                const ty = y(d.fraud_score) > 90 ? y(d.fraud_score) - 58 : y(d.fraud_score) + 12;
                return (
                  <g transform={`translate(${tx},${ty})`}>
                    <rect width="150" height="46" rx="6" fill="#0d0d0d" stroke="var(--border)" />
                    <text x="8" y="16" fontSize="10" fill="var(--ink)">
                      {d.tx_id} · {d.user_id}
                    </text>
                    <text x="8" y="30" fontSize="10" fill="var(--ink-2)" className="tabular">
                      score {d.fraud_score.toFixed(2)} · ${d.amount}
                    </text>
                    <text x="8" y="42" fontSize="10" fill={ACTION_COLOR[d.action] ?? "var(--ink-2)"}>
                      {d.action.toUpperCase()} ({d.confidence})
                    </text>
                  </g>
                );
              })()}
            </g>
          )}
        </svg>
      )}
      {/* status legend — labels, never color alone */}
      <div className="mt-2 flex gap-4 text-xs" style={{ color: "var(--ink-2)" }}>
        {Object.entries(ACTION_COLOR).map(([k, c]) => (
          <span key={k} className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: c }} /> {k}
          </span>
        ))}
      </div>
    </div>
  );
}
