import type { InvestigationSummary } from "@/lib/api";
import Badge from "./Badge";

export default function AlertsPanel({
  items,
  selectedId,
  onSelect,
}: {
  items: InvestigationSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <div className="card p-4">
      <div className="mb-2 text-sm font-medium">Investigations &amp; alerts</div>
      <div className="max-h-[300px] space-y-1.5 overflow-y-auto pr-1">
        {items.length === 0 && (
          <div className="py-6 text-center text-xs" style={{ color: "var(--muted)" }}>
            No investigations yet
          </div>
        )}
        {items.map((inv) => (
          <button
            key={inv.id}
            onClick={() => onSelect(inv.id)}
            className="w-full rounded-lg px-3 py-2 text-left text-xs transition-colors"
            style={{
              background: selectedId === inv.id ? "rgba(57,135,229,0.12)" : "transparent",
              border: `1px solid ${selectedId === inv.id ? "var(--series-1)" : "var(--grid)"}`,
            }}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="mono" style={{ color: "var(--ink-2)" }}>{inv.tx_id} · {inv.user_id}</span>
              <Badge status={inv.action} />
            </div>
            <div className="mt-1.5 flex items-center gap-2">
              <div className="h-1.5 flex-1 overflow-hidden rounded-full" style={{ background: "var(--grid)" }}>
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${Math.round(inv.fraud_score * 100)}%`,
                    background:
                      inv.action === "block"
                        ? "var(--status-critical)"
                        : inv.action === "review"
                          ? "var(--status-warning)"
                          : "var(--status-good)",
                  }}
                />
              </div>
              <span className="tabular" style={{ color: "var(--ink)" }}>{inv.fraud_score.toFixed(2)}</span>
              <span className="tabular" style={{ color: "var(--muted)" }}>${inv.amount}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
