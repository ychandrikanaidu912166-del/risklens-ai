export interface Transaction {
  transaction_id: string;
  customer_id: string;
  merchant_id: string;
  amount: number;
  currency: string;
  timestamp: string;
  device_id: string;
  ip_address: string;
  country: string;
  payment_method: string;
  transaction_status: string;
  customer_age_days: number;
  customer_transaction_count: number;
  customer_avg_amount: number;
  customer_max_amount: number;
  customer_usual_country?: string;
  customer_usual_device?: string;
  transactions_last_10m: number;
  transactions_last_1h: number;
  transactions_last_24h: number;
  is_new_device: number;
  is_new_country: number;
  is_unusual_hour: number;
  is_fraud?: number;
}

export interface InvestigationListItem {
  investigation_id: string;
  transaction_id: string;
  customer_id: string;
  merchant_id: string;
  amount: number;
  currency: string;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'PENDING' | 'IN_REVIEW' | 'RESOLVED';
  priority: string;
  policy_recommendation: string;
  analyst_decision?: string;
  created_at: string;
}

export interface RiskFactor {
  name: string;
  category: string;
  contribution: number;
  evidence_id?: string;
  detail?: string;
}

export interface EvidenceItem {
  evidence_id: string;
  type: string;
  source: string;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  observed_value?: string;
  baseline_value?: string;
  timestamp?: string;
  related_entity_ids?: string[];
}

export interface CounterEvidenceItem {
  id: string;
  type: string;
  title: string;
  description: string;
  confidence_impact: number;
  timestamp?: string;
}

export interface SignalsBreakdown {
  ml_risk: number;
  anomaly_risk: number;
  behavior_risk: number;
  entity_risk: number;
  final_fused_risk: number;
  evidence_strength: string;
  signal_agreement: string;
  agreement_description: string;
}

export interface BusinessImpact {
  transaction_amount: number;
  potential_loss_exposure: number;
  risk_adjusted_exposure: number;
  false_positive_friction_cost: number;
  decision_cost_rationale: string;
}

export interface AIAssessment {
  // 10-point structured assessment
  executive_summary?: string;
  risk_assessment?: string;
  strongest_evidence?: string[];
  counter_evidence: string[];
  behavioral_assessment?: string;
  entity_network_assessment?: string;
  business_impact?: any;
  confidence: number;
  recommended_action: string;
  what_would_change_recommendation?: string[];

  // Backward-compatible fields
  assessment: string;
  risk_level: string;
  primary_evidence: string[];
  supporting_evidence: string[];
  uncertainties: string[];
  reasoning_summary: string;
  is_deterministic_fallback: boolean;
  provider: string;
}

export interface TimelineItem {
  id: number;
  event_type: string;
  title: string;
  description: string;
  severity: string;
  timestamp: string;
}

export interface EntityNode {
  id: string;
  label: string;
  type: 'transaction' | 'customer' | 'device' | 'ip' | 'merchant';
  risk: 'target' | 'suspicious' | 'warning' | 'neutral';
}

export interface EntityEdge {
  source: string;
  target: string;
  label: string;
}

export interface EntityGraph {
  nodes: EntityNode[];
  edges: EntityEdge[];
}

export interface BehaviourComparison {
  amount_comparison: {
    current_amount: number;
    baseline_avg: number;
    baseline_median: number;
    baseline_p95: number;
    amount_ratio: number;
    amount_to_median: number;
    is_anomaly: boolean;
    summary: string;
  };
  device_comparison: {
    current_device: string;
    known_devices: string[];
    is_new_device: boolean;
    summary: string;
  };
  country_comparison: {
    current_country: string;
    known_countries: string[];
    is_new_country: boolean;
    summary: string;
  };
  hour_comparison: {
    current_hour: number;
    active_hours: number[];
    is_unusual_hour: boolean;
    summary: string;
  };
  velocity_comparison: {
    last_10m: number;
    last_1h: number;
    last_24h: number;
    is_anomaly: boolean;
    summary: string;
  };
}

export interface InvestigationContext {
  transaction: Transaction;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence_score?: number;
  evidence_strength?: string;
  signals_breakdown?: SignalsBreakdown;
  business_impact?: BusinessImpact;
  ml_output: {
    fraud_probability: number;
    is_fraud_flag: boolean;
    model_version: string;
  };
  risk_factors: RiskFactor[];
  evidence: EvidenceItem[];
  counter_evidence: CounterEvidenceItem[];
  customer_behaviour: BehaviourComparison;
  entities: EntityGraph;
  timeline: TimelineItem[];
  recommended_action: string;
  model_version: string;
  policy_version: string;
  existing_decision?: {
    decision: string;
    reason: string;
    timestamp: string;
    status: string;
  };
  ai_investigation?: AIAssessment;
}

export interface OverviewMetrics {
  total_transactions: number;
  high_risk_count: number;
  critical_risk_count: number;
  review_queue_count: number;
  precision: number;
  recall: number;
  f1: number;
  pr_auc: number;
  false_positive_rate: number;
  false_negative_rate: number;
  business_cost: number;
  cost_per_tx: number;
  model_version: string;
  risk_distribution: Record<string, number>;
  recent_critical_transactions: Array<{
    transaction_id: string;
    customer_id: string;
    merchant_id: string;
    amount: number;
    currency: string;
    risk_score: number;
    risk_level: string;
    policy_recommendation: string;
    status: string;
    timestamp: string;
  }>;
}

export interface SimulationPreset {
  id: string;
  name: string;
  category: string;
  description: string;
  payload: Partial<Transaction>;
}

export interface PipelineStep {
  step: number;
  title: string;
  status: string;
  detail: string;
}

export interface SimulationResult {
  status: string;
  transaction_id: string;
  pipeline_trace: PipelineStep[];
  result: any;
  context: InvestigationContext;
}
