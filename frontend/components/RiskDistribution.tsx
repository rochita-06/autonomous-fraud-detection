"use client";

import type { Stats } from "@/lib/api";

const ROWS = [
  { key: "allowed", label: "Allowed", color: "var(--status-good)" },
  { key: "review", label: "Under review", color: "var(--status-warning)" },
  { key: "blocked", label: "Blocked", color: "var(--status-critical)" },
] as const;

/** Horizontal bar breakdown of investigation outcomes. */
export default function RiskDistribution({ stats }: { stats: Stats | null }) {
  const blocked = stats?.blocked ?? 0;
  const review = stats?.under_review ?? 0;
  const allowed = Math.max((stats?.investigated ?? 0) - blocked - review, 0);
  const values: Record<(typeof ROWS)[number]["key"], number> = { allowed, review, blocked };
  const max = Math.max(allowed, review, blocked, 1);

  return (
    <div className="card card-hover p-5">
      <div className="mb-3 text-sm font-semibold">Risk Distribution</div>
      <div className="space-y-3">
        {ROWS.map((r) => (
          <div key={r.key}>
            <div className="mb-1 flex items-center justify-between text-[11px]">
              <span style={{ color: "var(--ink-2)" }}>{r.label}</span>
              <span className="tabular font-semibold">{values[r.key]}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full" style={{ background: "var(--grid)" }}>
              <div
                className="h-full rounded-full"
                style={{
                  width: `${(values[r.key] / max) * 100}%`,
                  background: r.color,
                  boxShadow: `0 0 8px ${r.color}`,
                  transition: "width 0.8s cubic-bezier(0.2, 0.8, 0.2, 1)",
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
