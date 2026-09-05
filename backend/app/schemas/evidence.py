"""Evidence & counter-evidence schemas.

Each piece of evidence must:
  - have a stable `id` so downstream reports (including the AI investigator)
    can reference it by id;
  - carry a numeric `weight` (points contributed to the risk score);
  - be sourced from a real feature/rule/model output — never fabricated.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

EvidenceSource = Literal["rule", "model", "behavior", "velocity", "anomaly", "entity"]


class Evidence(BaseModel):
    id: str = Field(..., description="Stable id, e.g. 'E-AMT-HIGH' or 'C-DEVICE-KNOWN'.")
    code: str = Field(..., description="Machine-readable code.")
    description: str = Field(..., description="Human-readable one-line explanation.")
    weight: float = Field(..., description="Signed contribution to risk score (points).")
    source: EvidenceSource
    detail: Dict[str, Any] = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    supporting: List[Evidence] = Field(default_factory=list)
    counter: List[Evidence] = Field(default_factory=list)

    def total_positive(self) -> float:
        return sum(max(e.weight, 0.0) for e in self.supporting)

    def total_negative(self) -> float:
        return sum(min(e.weight, 0.0) for e in self.counter)
