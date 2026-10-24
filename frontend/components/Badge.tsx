const STYLES: Record<string, { color: string; label: string }> = {
  allow: { color: "var(--status-good)", label: "Allow" },
  clean: { color: "var(--status-good)", label: "Clean" },
  review: { color: "var(--status-warning)", label: "Review" },
  investigating: { color: "var(--series-1)", label: "Investigating" },
  block: { color: "var(--status-critical)", label: "Block" },
};

export default function Badge({ status }: { status: string }) {
  const s = STYLES[status] ?? { color: "var(--muted)", label: status };
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ border: `1px solid ${s.color}`, color: "var(--ink-2)" }}
    >
      <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
      {s.label}
    </span>
  );
}
