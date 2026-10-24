"use client";

import { useEffect, useState } from "react";

const RADIUS = 56;
const CIRC = 2 * Math.PI * RADIUS;

const ACTION_COLOR: Record<string, string> = {
  allow: "var(--status-good)",
  review: "var(--status-warning)",
  block: "var(--status-critical)",
};

/** Animated circular fraud-score gauge. */
export default function ScoreRing({ score, action }: { score: number; action: string }) {
  // animate from 0 on mount / score change
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const t = requestAnimationFrame(() => setShown(score));
    return () => cancelAnimationFrame(t);
  }, [score]);

  const color = ACTION_COLOR[action] ?? "var(--series-1)";

  return (
    <div className="relative mx-auto h-[150px] w-[150px]">
      <svg viewBox="0 0 140 140" className="h-full w-full" role="img" aria-label={`Fraud score ${score.toFixed(2)}`}>
        <defs>
          <linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--series-1)" />
            <stop offset="100%" stopColor="var(--series-2)" />
          </linearGradient>
        </defs>
        {/* decorative rotating tick ring */}
        <g className="ring-spin" opacity="0.35">
          {Array.from({ length: 36 }, (_, i) => {
            const a = (i / 36) * 2 * Math.PI;
            return (
              <line
                key={i}
                x1={70 + 66 * Math.cos(a)} y1={70 + 66 * Math.sin(a)}
                x2={70 + 69 * Math.cos(a)} y2={70 + 69 * Math.sin(a)}
                stroke="var(--series-2)" strokeWidth="1"
              />
            );
          })}
        </g>
        <circle cx="70" cy="70" r={RADIUS} fill="none" stroke="var(--grid)" strokeWidth="9" />
        <circle
          cx="70" cy="70" r={RADIUS}
          fill="none"
          stroke={action ? color : "url(#ring-grad)"}
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={CIRC}
          strokeDashoffset={CIRC * (1 - shown)}
          transform="rotate(-90 70 70)"
          style={{
            transition: "stroke-dashoffset 1.2s cubic-bezier(0.2, 0.8, 0.2, 1), stroke 0.4s ease",
            filter: `drop-shadow(0 0 8px ${action ? color : "rgba(79,140,255,0.7)"})`,
          }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="tabular text-4xl font-bold">{score.toFixed(2)}</span>
        <span className="text-[10px] uppercase tracking-widest" style={{ color: "var(--muted)" }}>
          fraud score
        </span>
      </div>
    </div>
  );
}
