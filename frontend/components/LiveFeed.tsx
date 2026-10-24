import type { FeedItem } from "@/lib/api";
import Badge from "./Badge";

export default function LiveFeed({ items }: { items: FeedItem[] }) {
  return (
    <div className="card p-4">
      <div className="mb-2 text-sm font-medium">Live transaction feed</div>
      <div className="max-h-[340px] overflow-y-auto">
        <table className="w-full text-xs">
          <thead className="sticky top-0" style={{ background: "var(--surface)" }}>
            <tr style={{ color: "var(--muted)" }}>
              <th className="py-1.5 text-left font-normal">Time</th>
              <th className="py-1.5 text-left font-normal">Tx</th>
              <th className="py-1.5 text-left font-normal">User</th>
              <th className="py-1.5 text-right font-normal">Amount</th>
              <th className="py-1.5 text-left font-normal pl-3">Category</th>
              <th className="py-1.5 text-left font-normal">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={6} className="py-6 text-center" style={{ color: "var(--muted)" }}>
                  Waiting for transactions…
                </td>
              </tr>
            )}
            {items.map((t) => (
              <tr key={t.tx_id + t.created_at} className="row-hover" style={{ borderTop: "1px solid var(--grid)" }}>
                <td className="mono py-1.5" style={{ color: "var(--ink-2)" }}>
                  {new Date(t.created_at).toLocaleTimeString()}
                </td>
                <td className="mono py-1.5 pr-2" style={{ color: "var(--ink-2)" }}>{t.tx_id}</td>
                <td className="py-1.5">{t.user_id}</td>
                <td className="py-1.5 text-right tabular">${t.amount.toFixed(2)}</td>
                <td className="py-1.5 pl-3" style={{ color: "var(--ink-2)" }}>{t.merchant_category}</td>
                <td className="py-1.5"><Badge status={t.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
