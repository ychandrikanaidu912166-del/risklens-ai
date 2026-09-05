"""Investigation output schema — the payload every UI page renders."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from backend.app.schemas.evidence import Evidence

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
Action = Literal["APPROVE", "STEP_UP", "MANUAL_REVIEW", "HOLD", "BLOCK"]


class ShapContribution(BaseModel):
    feature: str
    value: Any
    contribution: float


class ModelExplanation(BaseModel):
    top_features: List[ShapContribution]
    method: Literal["shap", "fallback"]


class BehaviorSnapshot(BaseModel):
    n_prior_tx: int
    mean_amount: Optional[float]
    std_amount: Optional[float]
    common_hours: List[int]
    common_countries: List[str]
    known_devices: List[str]
    amount_z_score: Optional[float]
    is_new_device: bool
    is_new_country: bool
    unusual_hour: bool


class TimelineEvent(BaseModel):
    ts: datetime
    event: str
    detail: str


class EntityRef(BaseModel):
    type: Literal["customer", "device", "ip", "merchant"]
    id: str
    relation: str
    note: Optional[str] = None


class InvestigationResult(BaseModel):
    model_config = {"protected_namespaces": ()}

    transaction_id: str
    ts: datetime
    customer_id: str
    merchant_id: str
    amount: float
    currency: str

    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    fraud_probability: float = Field(..., ge=0.0, le=1.0)
    anomaly_score: float
    behavioral_deviation: float

    risk_factors: List[str]
    supporting_evidence: List[Evidence]
    counter_evidence: List[Evidence]

    recommended_action: Action
    confidence: Literal["low", "medium", "high"]
    explanation: str

    model_explanation: ModelExplanation
    behavior: BehaviorSnapshot
    timeline: List[TimelineEvent]
    entities: List[EntityRef]

    model_version: str
    created_at: datetime
