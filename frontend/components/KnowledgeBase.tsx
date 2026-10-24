"use client";

import type { InvestigationDetail, ReasoningStep } from "@/lib/api";
import Tilt from "./Tilt";

interface CaseMatch {
  case_id: string;
  fraud_type: string;
  pattern: string;
  description: string;
  similarity: number;
}

function extractMatches(detail: InvestigationDetail | null): CaseMatch[] {
  if (!detail) return [];
  const step = detail.reasoning_log.find(
    (s: ReasoningStep) => s.type === "tool_call" && s.tool === "search_similar_cases",
  );
  const output = step?.output as { matches?: CaseMatch[] } | undefined;
  return output?.matches ?? [];
}

/** Similar known fraud cases retrieved via FAISS for the selected investigation. */
export default function KnowledgeBase({ detail }: { detail: InvestigationDetail | null }) {
  const matches = extractMatches(detail);

  if (matches.length === 0) {
    return (
      <div className="card flex h-[200px] items-center justify-center p-4 text-xs" style={{ color: "var(--muted)" }}>
        Run an investigation to retrieve similar fraud cases from the knowledge base
      </div>
    );
  }

  return (
    <div>
      <div className="mb-1 text-sm font-semibold">Retrieved Similar Cases</div>
      <p className="mb-3 text-[11px]" style={{ color: "var(--muted)" }}>
        FAISS vector search over the fraud-case knowledge base — for {detail?.tx_id}
      </p>
      <div className="grid gap-4 md:grid-cols-3">
        {matches.map((m, i) => (
          <Tilt key={m.case_id} max={9}>
          <div
            className="card float p-5"
            style={{ animationDelay: `${i * 0.7}s`, height: "100%" }}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold" style={{ color: "var(--series-1)" }}>
                {m.case_id}
              </span>
              <span
                className="tabular rounded-full px-2 py-0.5 text-[10px] font-semibold"
                style={{
                  background: "rgba(123,97,255,0.18)",
                  color: "#c9bcff",
                  border: "1px solid rgba(123,97,255,0.4)",
                }}
              >
                {(m.similarity * 100).toFixed(0)}% match
              </span>
            </div>
            <div className="mt-2 text-sm font-medium">{m.fraud_type.replaceAll("_", " ")}</div>
            <div className="mt-0.5 text-[11px] italic" style={{ color: "var(--series-2)" }}>
              {m.pattern}
            </div>
            <p className="mt-2 text-[11px] leading-relaxed" style={{ color: "var(--ink-2)" }}>
              {m.description}
            </p>
          </div>
          </Tilt>
        ))}
      </div>
    </div>
  );
}
