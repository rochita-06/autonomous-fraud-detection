"use client";

const STEPS = [
  { label: "Transaction", sub: "webhook in" },
  { label: "Pre-filter", sub: "cheap rules" },
  { label: "AI Agent", sub: "LangGraph" },
  { label: "Risk Evaluation", sub: "score + action" },
  { label: "n8n", sub: "score ≥ 0.8?" },
  { label: "Slack Alert", sub: "analyst ping" },
  { label: "Case Management", sub: "stored + audit" },
];

/** Event-driven automation pipeline (n8n workflow) with flowing connectors. */
export default function AutomationFlow() {
  return (
    <div className="card card-hover p-6">
      <div className="mb-1 text-sm font-semibold">Event-driven Automation</div>
      <p className="mb-5 text-[11px]" style={{ color: "var(--muted)" }}>
        n8n workflow: webhook → pre-filter → agent investigation → threshold alerting
      </p>

      <div className="flex flex-wrap items-center gap-y-4">
        {STEPS.map((s, i) => (
          <div key={s.label} className="flex items-center">
            <div
              className="glow-border rounded-xl px-4 py-3 text-center"
              style={{ animationDelay: `${i * 0.4}s` }}
            >
              <div className="text-xs font-semibold whitespace-nowrap">{s.label}</div>
              <div className="text-[10px]" style={{ color: "var(--muted)" }}>{s.sub}</div>
            </div>
            {i < STEPS.length - 1 && (
              <svg width="42" height="12" className="mx-1 shrink-0" aria-hidden>
                <line x1="0" y1="6" x2="42" y2="6" className="edge-flow" stroke="rgba(79,140,255,0.6)" strokeWidth="2" />
              </svg>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-4 text-[11px] leading-relaxed md:grid-cols-3" style={{ color: "var(--ink-2)" }}>
        <div>
          <div className="mb-1 font-semibold" style={{ color: "var(--ink)" }}>1 · Ingest &amp; pre-filter</div>
          The simulator (or any producer) POSTs to the n8n webhook. A Code node scores cheap
          signals — amount, odd hour, risky category, round amounts. Risk &lt; 0.3 is recorded
          via <code>/transactions</code> without waking the agent.
        </div>
        <div>
          <div className="mb-1 font-semibold" style={{ color: "var(--ink)" }}>2 · Autonomous investigation</div>
          Suspicious traffic hits <code>/investigate</code>. The LangGraph agent plans tool calls
          — history, anomaly checks, graph queries, RAG — and finalizes a scored decision with
          evidence-based reasons.
        </div>
        <div>
          <div className="mb-1 font-semibold" style={{ color: "var(--ink)" }}>3 · Alert &amp; audit</div>
          Scores ≥ 0.8 branch to a formatted Slack alert (set <code>SLACK_WEBHOOK_URL</code> on
          the n8n container). Every step is persisted, so any decision is auditable after the fact.
        </div>
      </div>
    </div>
  );
}
