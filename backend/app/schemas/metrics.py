from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class OverviewMetricsResponse(BaseModel):
    total_transactions: int
    high_risk_count: int
    critical_risk_count: int
    review_queue_count: int
    precision: float
    recall: float
    f1: float
    pr_auc: float
    false_positive_rate: float
    false_negative_rate: float
    business_cost: float
    cost_per_tx: float
    model_version: str
    risk_distribution: Dict[str, int]
    recent_critical_transactions: List[Dict[str, Any]]
