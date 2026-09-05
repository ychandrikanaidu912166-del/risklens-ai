// Centralised API client — one place for URLs, one place for errors.

import type {
  AIInvestigationReport,
  AuditEvent,
  Decision,
  DecisionIn,
  HealthResponse,
  InvestigationResult,
  ModelMetrics,
  OverviewMetrics,
  Subgraph,
  TransactionIn,
  TransactionSummary,
  EntityType,
} from "./types";

const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(`API ${status}: ${detail}`);
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_PREFIX}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      accept: "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* body wasn't JSON */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  health: () => req<HealthResponse>("/health"),
  overview: () => req<OverviewMetrics>("/overview"),

  listTransactions: (params: { risk_level?: string; action?: string; limit?: number } = {}) => {
    const q = new URLSearchParams();
    if (params.risk_level) q.set("risk_level", params.risk_level);
    if (params.action) q.set("action", params.action);
    q.set("limit", String(params.limit ?? 200));
    return req<TransactionSummary[]>(`/transactions?${q.toString()}`);
  },
  scoreTransaction: (tx: TransactionIn) =>
    req<InvestigationResult>("/transactions/score", { method: "POST", body: JSON.stringify(tx) }),

  getInvestigation: (txId: string) =>
    req<InvestigationResult>(`/investigations/${encodeURIComponent(txId)}`),
  getAIReport: (txId: string) =>
    req<AIInvestigationReport>(`/investigations/${encodeURIComponent(txId)}/ai-report`),

  getSubgraph: (type: EntityType, id: string, depth = 1) =>
    req<Subgraph>(`/entities/${type}/${encodeURIComponent(id)}/subgraph?depth=${depth}`),

  metrics: () => req<ModelMetrics>("/metrics/model"),

  postDecision: (payload: DecisionIn) =>
    req<Decision>("/decisions", { method: "POST", body: JSON.stringify(payload) }),
  listDecisions: (txId?: string) =>
    req<Decision[]>(`/decisions${txId ? `?tx_id=${encodeURIComponent(txId)}` : ""}`),

  listAudit: (params: { entity_id?: string; action?: string; limit?: number } = {}) => {
    const q = new URLSearchParams();
    if (params.entity_id) q.set("entity_id", params.entity_id);
    if (params.action) q.set("action", params.action);
    q.set("limit", String(params.limit ?? 100));
    return req<AuditEvent[]>(`/audit?${q.toString()}`);
  },
};
