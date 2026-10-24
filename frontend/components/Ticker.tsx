"use client";

import type { FeedItem } from "@/lib/api";

const STATUS_DOT: Record<string, string> = {
  clean: "var(--status-good)",
  allow: "var(--status-good)",
  review: "var(--status-warning)",
  block: "var(--status-critical)",
  investigating: "var(--series-1)",
};

/** Horizontal marquee of the latest pipeline transactions. */
export default function Ticker({ items }: { items: FeedItem[] }) {
  if (items.length === 0) return null;
  const slice = items.slice(0, 14);

  const Entry = ({ t }: { t: FeedItem }) => (
    <span className="mono inline-flex items-center gap-2 text-[11px]" style={{ color: "var(--ink-2)" }}>
      <span
        className="inline-block h-1.5 w-1.5 rounded-full"
        style={{ background: STATUS_DOT[t.status] ?? "var(--muted)" }}
      />
      {t.tx_id}
      <span style={{ color: "var(--muted)" }}>{t.user_id}{t.country ? ` · ${t.country}` : ""}</span>
      <span className="tabular font-semibold" style={{ color: "var(--ink)" }}>
        ${t.amount.toFixed(2)}
      </span>
      <span style={{ color: "var(--muted)" }}>{t.merchant_category}</span>
    </span>
  );

  return (
    <div
      className="ticker border-y py-1.5"
      style={{ borderColor: "var(--grid)", background: "rgba(255,255,255,0.02)" }}
      aria-label="Live transaction ticker"
    >
      <div className="ticker-track">
        {[0, 1].map((dup) => (
          <div key={dup} className="flex shrink-0 items-center gap-10" aria-hidden={dup === 1}>
            {slice.map((t) => (
              <Entry key={`${dup}-${t.tx_id}-${t.created_at}`} t={t} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
