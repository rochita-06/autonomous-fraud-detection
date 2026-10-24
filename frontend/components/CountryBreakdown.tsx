"use client";

import type { FeedItem } from "@/lib/api";

/** Transaction origins aggregated from the live feed. */
export default function CountryBreakdown({ items }: { items: FeedItem[] }) {
  const counts = new Map<string, { total: number; flagged: number }>();
  for (const t of items) {
    const key = t.country || "??";
    const entry = counts.get(key) ?? { total: 0, flagged: 0 };
    entry.total += 1;
    if (t.status === "block" || t.status === "review") entry.flagged += 1;
    counts.set(key, entry);
  }
  const rows = [...counts.entries()]
    .sort((a, b) => b[1].total - a[1].total)
    .slice(0, 6);
  const max = Math.max(...rows.map(([, v]) => v.total), 1);

  return (
    <div className="card p-5">
      <div className="kicker mb-0.5">Live feed</div>
      <div className="mb-3 text-sm font-semibold">Transaction Origins</div>
      {rows.length === 0 ? (
        <div className="py-6 text-center text-xs" style={{ color: "var(--muted)" }}>
          Waiting for traffic…
        </div>
      ) : (
        <div className="space-y-2.5">
          {rows.map(([country, v]) => (
            <div key={country}>
              <div className="mb-1 flex items-center justify-between text-[11px]">
                <span className="mono" style={{ color: "var(--ink-2)" }}>{country}</span>
                <span className="mono" style={{ color: "var(--muted)" }}>
                  {v.flagged > 0 && (
                    <span style={{ color: "var(--status-warning)" }}>{v.flagged} flagged · </span>
                  )}
                  {v.total} tx
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full" style={{ background: "var(--grid)" }}>
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${(v.total / max) * 100}%`,
                    background: "linear-gradient(90deg, var(--series-1), var(--series-2))",
                    transition: "width 0.6s ease",
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
