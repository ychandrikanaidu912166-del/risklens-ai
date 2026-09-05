"""Transparent risk-score fusion.

We combine two sources into a single 0..100 risk score:
  * The calibrated ML probability (mapped 0..70 via a mild non-linearity).
  * The signed evidence weight sum (bounded ±30).

Evidence weights already account for velocity/behavior/rules; adding them
directly to the ML component would double-count. Instead we treat evidence
as a bounded correction. This keeps the score explainable AND grounded in the
model.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.app.schemas.evidence import EvidenceBundle
from backend.app.schemas.investigation import RiskLevel


@dataclass
class FusedScore:
    risk_score: int          # 0..100
    risk_level: RiskLevel
    ml_component: float      # 0..70
    evidence_component: float  # -30..+30
    total_positive_evidence: float
    total_negative_evidence: float


def _ml_component(fraud_probability: float) -> float:
    # Slightly convex mapping so mid-probabilities don't dominate but very high
    # probabilities push toward the cap.
    p = max(0.0, min(1.0, float(fraud_probability)))
    # 0.0 -> 0, 0.5 -> ~26, 0.8 -> ~47, 1.0 -> 70
    return round(70.0 * (p ** 1.35), 2)


def _evidence_component(bundle: EvidenceBundle) -> float:
    pos = min(30.0, bundle.total_positive())
    neg = max(-15.0, bundle.total_negative())  # counter-evidence bounded
    return pos + neg


def _to_level(score: int) -> RiskLevel:
    if score <= 29:
        return "LOW"
    if score <= 59:
        return "MEDIUM"
    if score <= 79:
        return "HIGH"
    return "CRITICAL"


def fuse(fraud_probability: float, evidence: EvidenceBundle) -> FusedScore:
    ml_comp = _ml_component(fraud_probability)
    ev_comp = _evidence_component(evidence)
    raw = ml_comp + ev_comp
    score = int(max(0, min(100, round(raw))))
    return FusedScore(
        risk_score=score,
        risk_level=_to_level(score),
        ml_component=ml_comp,
        evidence_component=ev_comp,
        total_positive_evidence=evidence.total_positive(),
        total_negative_evidence=evidence.total_negative(),
    )
