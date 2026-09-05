from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class AnalystDecisionRequest(BaseModel):
    decision: str = Field(..., description="Action: APPROVE, HOLD, BLOCK, FALSE_POSITIVE, ESCALATE")
    reason: str = Field(..., min_length=3, description="Analyst rationale for the decision")
    analyst_id: Optional[str] = Field(default="analyst_ops_1", description="Analyst identity")


class AnalystDecisionResponse(BaseModel):
    transaction_id: str
    investigation_id: str
    decision: str
    reason: str
    timestamp: str
    risk_score: int
    model_version: str
    policy_version: str
    status: str = "RESOLVED"
