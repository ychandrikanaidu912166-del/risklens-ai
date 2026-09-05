"""Pydantic schemas for transactions."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


Channel = Literal["web", "mobile", "pos", "api"]
AuthResult = Literal["success", "failure", "3ds_pass", "3ds_fail"]


class TransactionIn(BaseModel):
    """Payload used to score a brand-new transaction via the API."""

    tx_id: str = Field(..., min_length=3, max_length=64)
    ts: datetime
    customer_id: str = Field(..., min_length=1, max_length=64)
    merchant_id: str = Field(..., min_length=1, max_length=64)
    merchant_category: str = Field(..., min_length=1, max_length=64)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=8)
    device_id: str = Field(..., min_length=1, max_length=64)
    ip_hash: str = Field(..., min_length=3, max_length=128)
    ip_country: str = Field(..., min_length=2, max_length=2)
    customer_country: str = Field(..., min_length=2, max_length=2)
    channel: Channel = "web"
    auth_result: AuthResult = "success"

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v: str) -> str:
        return v.upper()


class TransactionRecord(TransactionIn):
    """Full record after persistence, includes derived fields."""

    hour: int
    day_of_week: int
    is_fraud_label: Optional[int] = None
    split: str = "live"


class TransactionSummary(BaseModel):
    tx_id: str
    ts: datetime
    customer_id: str
    merchant_id: str
    amount: float
    currency: str
    risk_score: int
    risk_level: str
    recommended_action: str
    status: str
