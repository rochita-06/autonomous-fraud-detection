"use client";

import type { InvestigateResult } from "@/lib/api";
import ScoreRing from "./ScoreRing";

const ACTION_META: Record<string, { label: string; color: string; risk: string; recommendation: string }> = {
  allow: {
    label: "Allow",
    color: "var(--status-good)",
    risk: "Low Risk",
    recommendation: "Process normally. No manual action required.",
  },
  review: {
    label: "Hold + Review",
    color: "var(--status-warning)",
    risk: "Elevated Risk",
    recommendation: "Hold funds and queue for a manual analyst review.",
  },
  block: {
    label: "Block",
    color: "var(--status-critical)",
    risk: "Critical Risk",
    recommendation: "Block the transaction, freeze the session and escalate to the fraud desk.",
  },
};

export default function ResultCard({
  result,
  error,
  phase,
}: {
  result: InvestigateResult | null;
  error: string | null;
  phase: "idle" | "running" | "done";
}) {
  if (error) {
    return (
      <div className="card h-full p-5">
        <div className="mb-2 text-sm font-semibold">Investigation Result</div>
        <div
          className="rounded-lg px-3 py-2 text-xs"
          style={{ border: "1px solid var(--status-critical)", color: "var(--ink-2)" }}
        >
          ⚠ {error} — is the backend running on port 8000?
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="card flex h-full min-h-[320px] flex-col items-center justify-center gap-2 p-5 text-xs" style={{ color: "var(--muted)" }}>
        {phase === "running" ? (
          <>
            <span className="pulse-glow inline-block h-3 w-3 rounded-full" style={{ background: "var(--series-1)" }} />
            Agent is investigating…
          </>
        ) : (
          "Submit a transaction to see the verdict"
        )}
      </div>
    );
  }

  const meta = ACTION_META[result.action] ?? ACTION_META.review;

  return (
    <div className="glow-border card h-full p-5 fade-up">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm font-semibold">Investigation Result</div>
        <span className="text-[10px]" style={{ color: "var(--muted)" }}>
          {result.tx_id} · engine: {result.engine}
        </span>
      </div>

      <ScoreRing score={result.fraud_score} action={result.action} />

      <div className="mt-4 flex items-center justify-center gap-2">
        <span
          className="rounded-full px-3 py-1 text-xs font-semibold"
          style={{ background: `color-mix(in srgb, ${meta.color} 18%, transparent)`, color: meta.color, border: `1px solid ${meta.color}` }}
        >
          {meta.risk}
        </span>
        <span className="rounded-full px-3 py-1 text-xs font-semibold" style={{ border: "1px solid var(--border)" }}>
          {meta.label}
        </span>
        <span className="rounded-full px-3 py-1 text-[11px]" style={{ border: "1px solid var(--border)", color: "var(--ink-2)" }}>
          confidence: {result.confidence}
        </span>
      </div>

      <div className="mt-4">
        <div className="mb-1.5 text-[11px] uppercase tracking-wide" style={{ color: "var(--muted)" }}>
          Reasons
        </div>
        <ul className="space-y-1.5">
          {result.reasons.map((r, i) => (
            <li key={i} className="flex gap-2 text-xs leading-relaxed" style={{ color: "var(--ink-2)" }}>
              <span style={{ color: "var(--series-1)" }}>▸</span> {r}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-4 rounded-lg px-3 py-2 text-[11px] leading-relaxed" style={{ background: "rgba(79,140,255,0.08)", border: "1px solid rgba(79,140,255,0.25)", color: "var(--ink-2)" }}>
        <span className="font-semibold" style={{ color: "var(--ink)" }}>Recommendation — </span>
        {meta.recommendation}
      </div>
    </div>
  );
}
