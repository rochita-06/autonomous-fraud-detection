"use client";

import { useEffect, useState } from "react";

export type TimelinePhase = "idle" | "running" | "done";

const STAGES = [
  "Receiving Transaction",
  "Pre-filter Checks",
  "Agent Reasoning",
  "Tool Calls",
  "Knowledge Retrieval (RAG)",
  "Graph Analysis",
  "Risk Scoring",
  "Decision",
];

/** Vertical investigation pipeline — stages light up as the agent works. */
export default function Timeline({ phase }: { phase: TimelinePhase }) {
  const [active, setActive] = useState(-1);

  useEffect(() => {
    if (phase === "idle") {
      setActive(-1);
      return;
    }
    if (phase === "done") {
      setActive(STAGES.length - 1);
      return;
    }
    // running: walk stages, hold at Risk Scoring until the response lands
    setActive(0);
    const t = setInterval(() => {
      setActive((a) => Math.min(a + 1, STAGES.length - 2));
    }, 650);
    return () => clearInterval(t);
  }, [phase]);

  return (
    <div className="card card-hover h-full p-5">
      <div className="mb-4 text-sm font-semibold">Investigation Pipeline</div>
      <ol className="relative ml-3 space-y-0">
        {STAGES.map((label, i) => {
          const complete = phase === "done" || (phase === "running" && i < active);
          const current = phase === "running" && i === active;
          const dotColor = complete
            ? "var(--status-good)"
            : current
              ? "var(--series-1)"
              : "rgba(255,255,255,0.18)";
          return (
            <li key={label} className="relative flex items-start gap-3 pb-5 last:pb-0">
              {i < STAGES.length - 1 && (
                <span
                  className="absolute left-[7px] top-5 h-full w-[2px]"
                  style={{
                    background: complete
                      ? "linear-gradient(180deg, var(--series-1), var(--series-2))"
                      : "rgba(255,255,255,0.1)",
                    transition: "background 0.4s ease",
                  }}
                />
              )}
              <span
                className={`relative z-10 mt-0.5 inline-block h-4 w-4 shrink-0 rounded-full ${current ? "pulse-glow" : ""}`}
                style={{
                  background: dotColor,
                  boxShadow: complete || current ? `0 0 12px ${dotColor}` : "none",
                  transition: "background 0.4s ease, box-shadow 0.4s ease",
                }}
              />
              <div>
                <div
                  className="text-xs font-medium"
                  style={{ color: complete || current ? "var(--ink)" : "var(--muted)" }}
                >
                  {label}
                </div>
                <div className="text-[10px]" style={{ color: "var(--muted)" }}>
                  {complete ? "complete" : current ? "in progress…" : "pending"}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
