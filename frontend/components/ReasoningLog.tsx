import type { InvestigationDetail, ReasoningStep } from "@/lib/api";

function StepView({ step }: { step: ReasoningStep }) {
  if (step.type === "thought") {
    return (
      <div className="rounded-lg px-3 py-2" style={{ background: "rgba(57,135,229,0.08)", border: "1px solid var(--grid)" }}>
        <div className="text-[10px] uppercase tracking-wide" style={{ color: "var(--series-1)" }}>
          Step {step.step} · Thought
        </div>
        <div className="mt-0.5 text-xs" style={{ color: "var(--ink-2)" }}>{String(step.content)}</div>
      </div>
    );
  }
  if (step.type === "tool_call") {
    return (
      <div className="rounded-lg px-3 py-2" style={{ border: "1px solid var(--grid)" }}>
        <div className="text-[10px] uppercase tracking-wide" style={{ color: "var(--series-2)" }}>
          Step {step.step} · Tool — {step.tool}
        </div>
        <details className="mt-1">
          <summary className="cursor-pointer text-[11px]" style={{ color: "var(--muted)" }}>
            input / output
          </summary>
          <pre className="mt-1 max-h-40 overflow-auto rounded p-2 text-[10px] leading-relaxed" style={{ background: "#0d0d0d", color: "var(--ink-2)" }}>
            {JSON.stringify({ input: step.input, output: step.output }, null, 2)}
          </pre>
        </details>
      </div>
    );
  }
  return (
    <div className="rounded-lg px-3 py-2" style={{ border: "1px solid var(--status-warning)" }}>
      <div className="text-[10px] uppercase tracking-wide" style={{ color: "var(--status-warning)" }}>
        Step {step.step} · Final decision
      </div>
      <pre className="mt-1 max-h-40 overflow-auto rounded p-2 text-[10px] leading-relaxed" style={{ background: "#0d0d0d", color: "var(--ink-2)" }}>
        {JSON.stringify(step.content, null, 2)}
      </pre>
    </div>
  );
}

export default function ReasoningLog({ detail }: { detail: InvestigationDetail | null }) {
  if (!detail) {
    return (
      <div className="card flex h-[280px] items-center justify-center p-4 text-xs" style={{ color: "var(--muted)" }}>
        Select an investigation to inspect the agent&apos;s reasoning
      </div>
    );
  }
  return (
    <div className="card p-4">
      <div className="mb-1 flex items-baseline justify-between">
        <div className="text-sm font-medium">Agent reasoning — {detail.tx_id}</div>
        <div className="text-[10px]" style={{ color: "var(--muted)" }}>
          engine: {detail.engine}
        </div>
      </div>
      <pre className="mb-3 whitespace-pre-wrap rounded-lg p-3 text-xs leading-relaxed" style={{ background: "#0d0d0d", color: "var(--ink-2)" }}>
        {detail.explanation}
      </pre>
      <div className="max-h-[320px] space-y-1.5 overflow-y-auto pr-1">
        {detail.reasoning_log.map((s) => (
          <StepView key={s.step} step={s} />
        ))}
      </div>
    </div>
  );
}
