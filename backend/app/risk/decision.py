"""Decision engine.

Policy considers: risk score band, model confidence, evidence strength, and
transaction value. Score alone never decides — a HIGH score with weak evidence
routes to MANUAL_REVIEW rather than BLOCK.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from backend.app.config import get_settings
from backend.app.schemas.evidence import EvidenceBundle
from backend.app.schemas.investigation import Action, RiskLevel


@dataclass
class DecisionResult:
    action: Action
    confidence: str          # low | medium | high
    reason: str


def _confidence(fraud_probability: float, evidence: EvidenceBundle, prior_tx: int) -> str:
    pos = evidence.total_positive()
    supporting_count = len(evidence.supporting)

    if prior_tx < 3:
        # We can't be confident about a customer with almost no history.
        return "low" if supporting_count < 3 else "medium"

    if fraud_probability >= 0.75 and pos >= 40 and supporting_count >= 4:
        return "high"
    if fraud_probability >= 0.5 and pos >= 25:
        return "medium"
    if fraud_probability <= 0.15 and supporting_count <= 1:
        return "high"  # confident it's fine
    return "medium" if supporting_count >= 2 else "low"


def decide(
    risk_level: RiskLevel,
    risk_score: int,
    fraud_probability: float,
    evidence: EvidenceBundle,
    amount: float,
    prior_tx: int,
) -> DecisionResult:
    settings = get_settings()
    confidence = _confidence(fraud_probability, evidence, prior_tx)
    pos = evidence.total_positive()
    supporting_count = len(evidence.supporting)

    # Insufficient-evidence guard: high score but nothing concrete to point to.
    if risk_score >= 60 and supporting_count < 2:
        return DecisionResult(
            action="MANUAL_REVIEW",
            confidence="low",
            reason="High score but insufficient concrete evidence. Analyst review recommended.",
        )

    if risk_level == "LOW":
        return DecisionResult(action="APPROVE", confidence=confidence, reason="Low risk score.")

    if risk_level == "MEDIUM":
        # Small-value MEDIUM tx can go through with STEP_UP; larger amounts get manual review.
        if amount >= 25_000:
            return DecisionResult(
                action="MANUAL_REVIEW",
                confidence=confidence,
                reason="Medium risk on a large-value transaction.",
            )
        return DecisionResult(
            action="STEP_UP",
            confidence=confidence,
            reason="Medium risk — require additional verification.",
        )

    if risk_level == "HIGH":
        if confidence == "high" and pos >= 45:
            return DecisionResult(
                action="HOLD",
                confidence=confidence,
                reason="High risk with strong evidence — hold pending review.",
            )
        return DecisionResult(
            action="MANUAL_REVIEW",
            confidence=confidence,
            reason="High risk — route to analyst.",
        )

    # CRITICAL
    if confidence == "high" and pos >= 55:
        return DecisionResult(
            action="BLOCK",
            confidence=confidence,
            reason="Critical risk with strong, corroborating evidence.",
        )
    return DecisionResult(
        action="HOLD",
        confidence=confidence,
        reason="Critical risk but confidence is not high enough to auto-block.",
    )
