from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class RiskFactor(BaseModel):
    name: str
    category: str
    contribution: float
    evidence_id: Optional[str] = ""
    detail: Optional[str] = ""


class EvidenceItem(BaseModel):
    evidence_id: str
    type: str
    source: str
    description: str
    severity: str
    observed_value: Optional[str] = ""
    baseline_value: Optional[str] = ""
    timestamp: Optional[str] = ""
    related_entity_ids: Optional[List[str]] = []


class CounterEvidenceItem(BaseModel):
    id: str
    type: str
    title: str
    description: str
    confidence_impact: int
    timestamp: Optional[str] = ""


class AIAssessment(BaseModel):
    # 10-point structured investigation
    executive_summary: str = ""
    risk_assessment: str = ""
    strongest_evidence: List[str] = []
    counter_evidence: List[str] = []
    behavioral_assessment: str = ""
    entity_network_assessment: str = ""
    business_impact: Dict[str, Any] = {}
    confidence: float = 0.85
    recommended_action: str = "MANUAL_REVIEW"
    what_would_change_recommendation: List[str] = []

    # Backward-compatible fields
    assessment: str = ""
    risk_level: str = "LOW"
    primary_evidence: List[str] = []
    supporting_evidence: List[str] = []
    uncertainties: List[str] = []
    reasoning_summary: str = ""
    is_deterministic_fallback: bool = True
    provider: str = "local_deterministic_engine"


class InvestigationContextResponse(BaseModel):
    transaction: Dict[str, Any]
    risk_score: int
    risk_level: str
    ml_output: Dict[str, Any]
    risk_factors: List[RiskFactor]
    signals_breakdown: Optional[Dict[str, Any]] = None
    business_impact: Optional[Dict[str, Any]] = None
    evidence: List[EvidenceItem]
    counter_evidence: List[CounterEvidenceItem]
    customer_behaviour: Dict[str, Any]
    entities: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    recommended_action: str
    model_version: str
    policy_version: str
    existing_decision: Optional[Dict[str, Any]] = None
    ai_investigation: Optional[AIAssessment] = None
