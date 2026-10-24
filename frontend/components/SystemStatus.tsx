"use client";

import { API } from "@/lib/api";

export default function SystemStatus({
  online,
  latency,
  graphBackend,
  engine,
}: {
  online: boolean;
  latency: number | null;
  graphBackend: string | null;
  engine: string | null;
}) {
  const rows: { label: string; value: string; ok?: boolean }[] = [
    { label: "API endpoint", value: API.replace(/^https?:\/\//, ""), ok: online },
    { label: "Round-trip latency", value: latency == null ? "—" : `${latency} ms`, ok: latency != null && latency < 500 },
    { label: "Graph backend", value: graphBackend ?? "—", ok: graphBackend != null },
    { label: "Decision engine", value: engine ?? "rules", ok: true },
    { label: "RAG index", value: "FAISS · 30 cases", ok: true },
    { label: "Thresholds", value: "review 0.50 · block 0.80" },
  ];

  return (
    <div className="card p-5">
      <div className="kicker mb-0.5">Infrastructure</div>
      <div className="mb-3 text-sm font-semibold">System Status</div>
      <dl className="space-y-2">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center justify-between gap-3 text-[11px]">
            <dt style={{ color: "var(--muted)" }}>{r.label}</dt>
            <dd className="mono flex items-center gap-1.5" style={{ color: "var(--ink-2)" }}>
              {r.ok !== undefined && (
                <span
                  className="inline-block h-1.5 w-1.5 rounded-full"
                  style={{ background: r.ok ? "var(--status-good)" : "var(--status-critical)" }}
                />
              )}
              {r.value}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
