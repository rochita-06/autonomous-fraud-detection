import type { InvestigationSummary, Stats } from "@/lib/api";

function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return null;
  const W = 96;
  const H = 26;
  const pts = values
    .map((v, i) => `${((i / (values.length - 1)) * W).toFixed(1)},${(H - 3 - v * (H - 6)).toFixed(1)}`)
    .join(" ");
  return (
    <svg width={W} height={H} className="mt-1" aria-hidden>
      <polyline
        points={pts}
        fill="none"
        stroke="var(--series-1)"
        strokeWidth="1.5"
        strokeLinejoin="round"
        style={{ filter: "drop-shadow(0 0 3px rgba(79,140,255,0.6))" }}
      />
      <circle
        cx={W}
        cy={H - 3 - values[values.length - 1] * (H - 6)}
        r="2.5"
        fill="var(--series-2)"
      />
    </svg>
  );
}

const TILES: {
  key: keyof Stats;
  label: string;
  caption: string;
  accent?: string;
  fmt?: (v: number) => string;
}[] = [
  { key: "total_transactions", label: "Transactions processed", caption: "all time · pipeline" },
  { key: "investigated", label: "Agent investigations", caption: "autonomous runs" },
  { key: "blocked", label: "Blocked", caption: "score ≥ 0.80", accent: "var(--status-critical)" },
  { key: "under_review", label: "Under review", caption: "score ≥ 0.50", accent: "var(--status-warning)" },
  { key: "avg_fraud_score", label: "Avg fraud score", caption: "recent trend →", fmt: (v) => v.toFixed(2) },
];

export default function StatTiles({
  stats,
  investigations = [],
}: {
  stats: Stats | null;
  investigations?: InvestigationSummary[];
}) {
  const trend = [...investigations].reverse().slice(-14).map((i) => i.fraud_score);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {TILES.map((t) => (
        <div
          key={t.key}
          className="card card-hover px-4 py-3"
          style={t.accent ? { borderLeft: `2px solid ${t.accent}` } : undefined}
        >
          <div className="text-[11px]" style={{ color: "var(--muted)" }}>
            {t.label}
          </div>
          <div className="mono mt-1 flex items-baseline gap-2 text-2xl font-semibold" style={t.accent ? { color: t.accent } : undefined}>
            {stats == null ? "—" : (t.fmt ?? String)(stats[t.key] as number)}
          </div>
          {t.key === "avg_fraud_score" ? (
            <Sparkline values={trend} />
          ) : (
            <div className="mt-1 text-[10px]" style={{ color: "var(--muted)" }}>
              {t.caption}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
