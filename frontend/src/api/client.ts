import {
  OverviewMetrics,
  InvestigationListItem,
  InvestigationContext,
  AIAssessment
} from '../types';

const API_BASE = '/api/v1';

export async function fetchOverviewMetrics(): Promise<OverviewMetrics> {
  const res = await fetch(`${API_BASE}/metrics/overview`);
  if (!res.ok) throw new Error(`Failed to load metrics: ${res.statusText}`);
  return res.json();
}

export async function fetchInvestigations(params?: {
  risk_level?: string;
  status?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<{ total: number; offset: number; limit: number; items: InvestigationListItem[] }> {
  const q = new URLSearchParams();
  if (params?.risk_level && params.risk_level !== 'ALL') q.set('risk_level', params.risk_level);
  if (params?.status && params.status !== 'ALL') q.set('status', params.status);
  if (params?.search) q.set('search', params.search);
  if (params?.limit) q.set('limit', params.limit.toString());
  if (params?.offset) q.set('offset', params.offset.toString());

  const res = await fetch(`${API_BASE}/investigations?${q.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch investigations: ${res.statusText}`);
  return res.json();
}

export async function fetchInvestigationDetail(transactionId: string): Promise<InvestigationContext> {
  const res = await fetch(`${API_BASE}/investigations/${encodeURIComponent(transactionId)}`);
  if (!res.ok) throw new Error(`Transaction ${transactionId} not found (${res.statusText})`);
  return res.json();
}

export async function triggerAIAnalysis(transactionId: string): Promise<AIAssessment> {
  const res = await fetch(`${API_BASE}/investigations/${encodeURIComponent(transactionId)}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error(`Analysis failed: ${res.statusText}`);
  const json = await res.json();
  return json.data;
}

export async function submitAnalystDecision(
  transactionId: string,
  payload: { decision: string; reason: string; analyst_id?: string }
): Promise<any> {
  const res = await fetch(`${API_BASE}/investigations/${encodeURIComponent(transactionId)}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to submit decision');
  }
  return res.json();
}

export async function fetchModelMetrics(): Promise<any> {
  const res = await fetch(`${API_BASE}/metrics/model`);
  if (!res.ok) throw new Error(`Failed to fetch model metrics: ${res.statusText}`);
  return res.json();
}
