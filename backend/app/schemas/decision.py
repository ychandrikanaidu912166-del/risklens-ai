"""Analyst decision + audit schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

AnalystAction = Literal["APPROVE", "HOLD", "BLOCK", "FALSE_POSITIVE", "ESCALATE"]


class DecisionIn(BaseModel):
    tx_id: str = Field(..., min_length=1)
    action: AnalystAction
    reason: Optional[str] = Field(default=None, max_length=2000)
    analyst_id: str = Field(default="analyst", min_length=1, max_length=64)


class DecisionOut(BaseModel):
    id: int
    tx_id: str
    action: AnalystAction
    reason: Optional[str]
    analyst_id: str
    created_at: datetime


class AuditEventOut(BaseModel):
    id: int
    actor: str
    action: str
    entity_type: str
    entity_id: str
    payload_json: Optional[dict]
    created_at: datetime
