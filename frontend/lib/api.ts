export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = { ...(extra ?? {}) };
  if (API_KEY) headers["X-API-Key"] = API_KEY;
  return headers;
}

export interface Stats {
  total_transactions: number;
  investigated: number;
  blocked: number;
  under_review: number;
  avg_fraud_score: number;
}

export interface FeedItem {
  tx_id: string;
  user_id: string;
  receiver_id: string;
  amount: number;
  country: string;
  merchant_category: string;
  status: string;
  prefilter_risk: number;
  created_at: string;
}

export interface InvestigationSummary {
  id: number;
  tx_id: string;
  user_id: string;
  amount: number;
  fraud_score: number;
  confidence: string;
  action: string;
  reasons: string[];
  explanation: string;
  engine: string;
  created_at: string;
}

export interface ReasoningStep {
  step: number;
  type: "thought" | "tool_call" | "decision";
  content?: unknown;
  tool?: string;
  input?: unknown;
  output?: unknown;
}

export interface InvestigationDetail extends InvestigationSummary {
  reasoning_log: ReasoningStep[];
}

export interface GraphData {
  nodes: { id: string; type: "user" | "device"; flagged: boolean }[];
  links: { source: string; target: string; rel: string }[];
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store", headers: authHeaders() });
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

export interface InvestigatePayload {
  user_id: string;
  receiver_id?: string;
  amount: number;
  country?: string;
  merchant_category?: string;
  timestamp?: string;
}

export interface InvestigateResult extends InvestigationSummary {
  summary: string;
  reasoning_log: ReasoningStep[];
  investigation_id: number;
}

export async function investigate(payload: InvestigatePayload): Promise<InvestigateResult> {
  const res = await fetch(`${API}/investigate`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`/investigate: ${res.status}`);
  const body = await res.json();
  return { ...body, id: body.investigation_id };
}

export interface Health {
  status: string;
  graph_backend: string;
}

export const fetchHealth = () => get<Health>("/health");
export const fetchStats = () => get<Stats>("/stats");
export const fetchFeed = () => get<FeedItem[]>("/transactions/feed?limit=30");
export const fetchInvestigations = () => get<InvestigationSummary[]>("/investigations?limit=25");
export const fetchInvestigation = (id: number) => get<InvestigationDetail>(`/investigations/${id}`);
export const fetchGraph = (userId: string) => get<GraphData>(`/graph/${userId}`);
