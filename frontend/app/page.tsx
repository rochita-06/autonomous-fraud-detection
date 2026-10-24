"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchFeed,
  fetchGraph,
  fetchHealth,
  fetchInvestigation,
  fetchInvestigations,
  fetchStats,
  type FeedItem,
  type GraphData,
  type InvestigateResult,
  type InvestigationDetail,
  type InvestigationSummary,
  type Stats,
} from "@/lib/api";
import AlertsPanel from "@/components/AlertsPanel";
import AutomationFlow from "@/components/AutomationFlow";
import CountryBreakdown from "@/components/CountryBreakdown";
import HoloGlobe from "@/components/HoloGlobe";
import Tilt from "@/components/Tilt";
import InvestigateForm from "@/components/InvestigateForm";
import KnowledgeBase from "@/components/KnowledgeBase";
import LiveFeed from "@/components/LiveFeed";
import NetworkGraph from "@/components/NetworkGraph";
import Particles from "@/components/Particles";
import ReasoningLog from "@/components/ReasoningLog";
import ResultCard from "@/components/ResultCard";
import RiskDistribution from "@/components/RiskDistribution";
import ScoreChart from "@/components/ScoreChart";
import StatTiles from "@/components/StatTiles";
import SystemStatus from "@/components/SystemStatus";
import Ticker from "@/components/Ticker";
import Timeline, { type TimelinePhase } from "@/components/Timeline";

const POLL_MS = 3000;
const BUILD = "fe35445";
const TABS = ["Dashboard", "Investigations", "Graph Intelligence", "Knowledge Base", "Automation", "Settings"] as const;
type Tab = (typeof TABS)[number];

function Clock() {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    setNow(new Date());
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  if (!now) return <span className="mono">--:--:--</span>;
  return (
    <span className="mono">
      {now.toISOString().slice(11, 19)} <span style={{ color: "var(--muted)" }}>UTC</span>
    </span>
  );
}

function threatLevel(investigations: InvestigationSummary[]) {
  const recent = investigations.slice(0, 5);
  if (recent.length === 0) return { label: "STANDBY", color: "var(--muted)" };
  const avg = recent.reduce((s, i) => s + i.fraud_score, 0) / recent.length;
  if (avg >= 0.8) return { label: "SEVERE", color: "var(--status-critical)" };
  if (avg >= 0.5) return { label: "ELEVATED", color: "var(--status-warning)" };
  if (avg >= 0.3) return { label: "GUARDED", color: "var(--series-1)" };
  return { label: "LOW", color: "var(--status-good)" };
}

export default function Console() {
  const [tab, setTab] = useState<Tab>("Dashboard");

  const [stats, setStats] = useState<Stats | null>(null);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [investigations, setInvestigations] = useState<InvestigationSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<InvestigationDetail | null>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [online, setOnline] = useState(true);
  const [latency, setLatency] = useState<number | null>(null);
  const [graphBackend, setGraphBackend] = useState<string | null>(null);

  const [phase, setPhase] = useState<TimelinePhase>("idle");
  const [result, setResult] = useState<InvestigateResult | null>(null);
  const [investigateError, setInvestigateError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const t0 = performance.now();
      const [s, f, inv, h] = await Promise.all([
        fetchStats(),
        fetchFeed(),
        fetchInvestigations(),
        fetchHealth(),
      ]);
      setLatency(Math.round(performance.now() - t0));
      setStats(s);
      setFeed(f);
      setInvestigations(inv);
      setGraphBackend(h.graph_backend);
      setOnline(true);
    } catch (err) {
      console.error("Failed to refresh dashboard data:", err);
      setOnline(false);
      setLatency(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, POLL_MS);
    return () => clearInterval(t);
  }, [refresh]);

  useEffect(() => {
    if (selectedId == null) return;
    let cancelled = false;
    (async () => {
      try {
        const d = await fetchInvestigation(selectedId);
        if (cancelled) return;
        setDetail(d);
        const g = await fetchGraph(d.user_id);
        if (!cancelled) setGraph(g);
      } catch (err) {
        if (!cancelled) console.error("Failed to load investigation/graph:", err);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  useEffect(() => {
    if (selectedId == null && investigations.length > 0) {
      setSelectedId(investigations[0].id);
    }
  }, [investigations, selectedId]);

  const onInvestigateResult = (r: InvestigateResult) => {
    setResult(r);
    setPhase("done");
    setSelectedId(r.investigation_id);
    refresh();
  };

  const threat = threatLevel(investigations);
  const engine = investigations[0]?.engine ?? null;

  return (
    <>
      <Particles />

      {/* ------------------------------------------- utility strip */}
      <div
        className="hidden items-center justify-between border-b px-4 py-1 text-[10px] sm:flex lg:px-8"
        style={{ borderColor: "var(--grid)", background: "rgba(5,8,22,0.85)", color: "var(--muted)" }}
      >
        <div className="flex items-center gap-4">
          <span className="mono">FIS-CONSOLE v1.2 · build {BUILD}</span>
          <span className="mono hidden md:inline">env: local-sim</span>
          <span className="mono hidden md:inline">graph: {graphBackend ?? "—"}</span>
          <span className="mono hidden lg:inline">engine: {engine ?? "rules"}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="mono">{latency == null ? "rtt —" : `rtt ${latency}ms`}</span>
          <Clock />
        </div>
      </div>

      {/* ------------------------------------------------ nav */}
      <nav
        className="sticky top-0 z-50 border-b px-4 py-2.5 backdrop-blur-xl lg:px-8"
        style={{ background: "rgba(5,8,22,0.72)", borderColor: "var(--border)" }}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden>
              <path
                d="M12 2l8 3.5v5.7c0 5-3.4 9.2-8 10.8-4.6-1.6-8-5.8-8-10.8V5.5L12 2z"
                fill="url(#shield-grad)" opacity="0.9"
              />
              <path d="M8.5 12l2.4 2.4 4.6-4.8" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              <defs>
                <linearGradient id="shield-grad" x1="4" y1="2" x2="20" y2="22">
                  <stop stopColor="#4F8CFF" />
                  <stop offset="1" stopColor="#7B61FF" />
                </linearGradient>
              </defs>
            </svg>
            <span className="hidden text-sm font-semibold tracking-tight md:block">
              Fraud Investigation<span style={{ color: "var(--muted)" }}> · AI SOC</span>
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-1">
            {TABS.map((t) => (
              <button key={t} onClick={() => setTab(t)} className={`nav-link ${tab === t ? "active" : ""}`}>
                {t}
              </button>
            ))}
          </div>

          <span
            className="inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px]"
            style={{ border: "1px solid var(--border)", color: "var(--ink-2)" }}
          >
            <span
              className={`h-2 w-2 rounded-full ${online ? "pulse-glow" : ""}`}
              style={{ background: online ? "var(--status-good)" : "var(--status-critical)" }}
            />
            {online ? "live" : "offline"}
          </span>
        </div>
      </nav>

      <Ticker items={feed} />

      <main className="mx-auto max-w-7xl space-y-5 p-4 lg:p-6">
        {tab === "Dashboard" && (
          <>
            {/* ------------------------------- operational header */}
            <section className="fade-up flex flex-wrap items-end justify-between gap-4 pt-2">
              <div>
                <div className="kicker">Fraud Operations Center</div>
                <h1 className="mt-1 text-2xl font-bold tracking-tight lg:text-3xl">
                  Autonomous Fraud <span className="gradient-text">Investigation</span>
                </h1>
                <p className="mt-1 text-xs" style={{ color: "var(--muted)" }}>
                  Agentic AI · RAG · Graph Intelligence · Event-driven Automation
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="hidden md:block" style={{ marginBottom: "-14px" }}>
                  <HoloGlobe />
                </div>
                <div className="card px-4 py-2.5 text-right">
                  <div className="kicker">Threat level</div>
                  <div
                    className="mono mt-0.5 text-lg font-bold tracking-wider"
                    style={{ color: threat.color, textShadow: `0 0 12px ${threat.color}` }}
                  >
                    {threat.label}
                  </div>
                </div>
                <div className="card hidden px-4 py-2.5 text-right sm:block">
                  <div className="kicker">Session</div>
                  <div className="mono mt-0.5 text-lg font-semibold">
                    <Clock />
                  </div>
                </div>
              </div>
            </section>

            <StatTiles stats={stats} investigations={investigations} />

            {/* ------------------------------- three-panel core */}
            <div className="grid gap-5 lg:grid-cols-[1fr_1fr_1.2fr]">
              <div className="fade-up" style={{ animationDelay: "0.05s" }}>
                <Tilt>
                  <InvestigateForm
                    busy={phase === "running"}
                    onStart={() => {
                      setPhase("running");
                      setResult(null);
                      setInvestigateError(null);
                    }}
                    onResult={onInvestigateResult}
                    onError={(m) => {
                      setInvestigateError(m);
                      setPhase("idle");
                    }}
                  />
                </Tilt>
              </div>
              <div className="fade-up" style={{ animationDelay: "0.12s" }}>
                <Tilt>
                  <Timeline phase={phase} />
                </Tilt>
              </div>
              <div className="fade-up" style={{ animationDelay: "0.2s" }}>
                <Tilt>
                  <ResultCard result={result} error={investigateError} phase={phase} />
                </Tilt>
              </div>
            </div>

            <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
              <ScoreChart items={investigations} />
              <RiskDistribution stats={stats} />
            </div>

            <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
              <AlertsPanel items={investigations} selectedId={selectedId} onSelect={setSelectedId} />
              <div className="space-y-5">
                <CountryBreakdown items={feed} />
                <SystemStatus online={online} latency={latency} graphBackend={graphBackend} engine={engine} />
              </div>
            </div>
          </>
        )}

        {tab === "Investigations" && (
          <div className="fade-up space-y-5">
            <div className="grid gap-5 lg:grid-cols-[1fr_1.4fr]">
              <AlertsPanel items={investigations} selectedId={selectedId} onSelect={setSelectedId} />
              <ReasoningLog detail={detail} />
            </div>
            <LiveFeed items={feed} />
          </div>
        )}

        {tab === "Graph Intelligence" && (
          <div className="fade-up grid gap-5 lg:grid-cols-[1.4fr_1fr]">
            <NetworkGraph graph={graph} centerId={detail?.user_id ?? ""} />
            <AlertsPanel items={investigations} selectedId={selectedId} onSelect={setSelectedId} />
          </div>
        )}

        {tab === "Knowledge Base" && (
          <div className="fade-up">
            <KnowledgeBase detail={detail} />
          </div>
        )}

        {tab === "Automation" && (
          <div className="fade-up">
            <AutomationFlow />
          </div>
        )}

        {tab === "Settings" && (
          <div className="fade-up grid gap-5 lg:grid-cols-2">
            <SystemStatus online={online} latency={latency} graphBackend={graphBackend} engine={engine} />
            <div className="card max-w-xl p-6 text-[11px] leading-relaxed" style={{ color: "var(--muted)" }}>
              <div className="kicker mb-0.5">Configuration</div>
              <div className="mb-3 text-sm font-semibold" style={{ color: "var(--ink)" }}>Runtime</div>
              Thresholds and the Anthropic model live in <code>backend/app/config.py</code> and{" "}
              <code>.env</code>. Set <code>ANTHROPIC_API_KEY</code> to switch from the deterministic
              rule engine to the Claude-powered planner — same tools, same audit trail. Start Neo4j via{" "}
              <code>docker compose up -d</code> and seed with <code>python -m app.graph.seed</code> to
              replace the in-memory graph.
            </div>
          </div>
        )}
      </main>

      <footer
        className="mono flex flex-wrap items-center justify-between gap-2 border-t px-4 pb-6 pt-3 text-[10px] lg:px-8"
        style={{ borderColor: "var(--grid)", color: "var(--muted)" }}
      >
        <span>Autonomous Fraud Investigation System · Agentic RAG · Graph Intelligence · n8n</span>
        <span>build {BUILD} · master · {online ? "operational" : "degraded"}</span>
      </footer>
    </>
  );
}
