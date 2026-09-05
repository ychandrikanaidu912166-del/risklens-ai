// TypeScript mirrors of the backend Pydantic schemas.

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type Action = "APPROVE" | "STEP_UP" | "MANUAL_REVIEW" | "HOLD" | "BLOCK";
export type AnalystAction = "APPROVE" | "HOLD" | "BLOCK" | "FALSE_POSITIVE" | "ESCALATE";
export type EvidenceSource = "rule" | "model" | "behavior" | "velocity" | "anomaly" | "entity";

export interface Evidence {
  id: string;
  code: string;
  description: string;
  weight: number;
  source: EvidenceSource;
  detail: Record<string, unknown>;
}

export interface ShapContribution {
  feature: string;
  value: number | string;
  contribution: number;
}

export interface ModelExplanation {
  top_features: ShapContribution[];
  method: "shap" | "fallback";
}

export interface BehaviorSnapshot {
  n_prior_tx: number;
  mean_amount: number | null;
  std_amount: number | null;
  common_hours: number[];
  common_countries: string[];
  known_devices: string[];
  amount_z_score: number | null;
  is_new_device: boolean;
  is_new_country: boolean;
  unusual_hour: boolean;
}

export interface TimelineEvent {
  ts: string;
  event: string;
  detail: string;
}

export interface EntityRef {
  type: "customer" | "device" | "ip" | "merchant";
  id: string;
  relation: string;
  note?: string | null;
}

export interface InvestigationResult {
  transaction_id: string;
  ts: string;
  customer_id: string;
  merchant_id: string;
  amount: number;
  currency: string;
  risk_score: number;
  risk_level: RiskLevel;
  fraud_probability: number;
  anomaly_score: number;
  behavioral_deviation: number;
  risk_factors: string[];
  supporting_evidence: Evidence[];
  counter_evidence: Evidence[];
  recommended_action: Action;
  confidence: "low" | "medium" | "high";
  explanation: string;
  model_explanation: ModelExplanation;
  behavior: BehaviorSnapshot;
  timeline: TimelineEvent[];
  entities: EntityRef[];
  model_version: string;
  created_at: string;
}

export interface TransactionSummary {
  tx_id: string;
  ts: string;
  customer_id: string;
  merchant_id: string;
  amount: number;
  currency: string;
  risk_score: number;
  risk_level: RiskLevel;
  recommended_action: Action;
  status: string;
}

export interface TransactionIn {
  tx_id: string;
  ts: string;
  customer_id: string;
  merchant_id: string;
  merchant_category: string;
  amount: number;
  currency: string;
  device_id: string;
  ip_hash: string;
  ip_country: string;
  customer_country: string;
  channel: "web" | "mobile" | "pos" | "api";
  auth_result: "success" | "failure" | "3ds_pass" | "3ds_fail";
}

export interface ModelMetrics {
  generated_at: string;
  model_version: string;
  model_kind: string;
  dataset_rows: number;
  fraud_rate: number;
  split_sizes: { train: number; val: number; test: number };
  primary: PrimaryMetrics;
  baseline: PrimaryMetrics;
  feature_columns: string[];
  last_eval_at?: string;
}

export interface PrimaryMetrics {
  threshold: number;
  precision: number;
  recall: number;
  f1: number;
  pr_auc: number;
  roc_auc: number;
  fpr: number;
  fnr: number;
  brier: number;
  confusion_matrix: { tp: number; fp: number; tn: number; fn: number };
  business_cost: {
    fp_cost_per_tx: number;
    fn_cost_per_tx: number;
    review_cost_per_tx: number;
    false_positive_cost: number;
    false_negative_cost: number;
    expected_business_cost: number;
  };
  pr_curve: { precision: number; recall: number; threshold: number }[];
}

export interface OverviewMetrics {
  total_transactions: number;
  scored_transactions: number;
  live_transactions: number;
  low_count: number;
  medium_count: number;
  high_count: number;
  critical_count: number;
  review_queue_count: number;
  action_distribution: Record<string, number>;
  risk_level_distribution: Record<string, number>;
  model: {
    available: boolean;
    model_version?: string;
    model_kind?: string;
    precision?: number;
    recall?: number;
    f1?: number;
    pr_auc?: number;
    roc_auc?: number;
    fpr?: number;
    fnr?: number;
    expected_business_cost?: number;
  };
  recent_investigations: Array<{
    tx_id: string;
    customer_id: string;
    amount: number;
    currency: string;
    risk_score: number;
    risk_level: RiskLevel;
    recommended_action: Action;
    created_at: string;
  }>;
}

export interface AIInvestigationReport {
  generated_by: "deterministic" | "llm";
  grounded: boolean;
  assessment: string;
  primary_reasons: string[];
  supporting_evidence_ids: string[];
  counter_evidence_ids: string[];
  entity_notes: string[];
  confidence: string;
  recommended_action: string;
  analyst_summary: string;
  disclaimer: string;
}

export interface Decision {
  id: number;
  tx_id: string;
  action: AnalystAction;
  reason?: string | null;
  analyst_id: string;
  created_at: string;
}

export interface DecisionIn {
  tx_id: string;
  action: AnalystAction;
  reason?: string;
  analyst_id?: string;
}

export interface AuditEvent {
  id: number;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string;
  payload_json: Record<string, unknown> | null;
  created_at: string;
}

export type EntityType = "customer" | "device" | "ip" | "merchant";

export interface SubgraphNode {
  id: string;
  type: EntityType;
  label: string;
  risk_hint: "root" | "high" | "warning" | "neutral";
  meta: Record<string, string>;
}

export interface SubgraphEdge {
  source: string;
  target: string;
  weight: number;
  label: string;
}

export interface Subgraph {
  root: SubgraphNode;
  nodes: SubgraphNode[];
  edges: SubgraphEdge[];
  stats: { n_transactions: number; n_nodes: number; n_edges: number };
}

export interface HealthResponse {
  status: "ok" | "degraded";
  model_ok: boolean;
  model: {
    model_version?: string;
    model_kind?: string;
    n_features?: number;
    error?: string;
  };
}
