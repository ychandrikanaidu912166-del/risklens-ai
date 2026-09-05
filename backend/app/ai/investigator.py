"""AI investigation report.

The LLM is NOT the fraud classifier. This layer only *summarises* what the
deterministic risk engine already computed. Every claim it emits is bound to
a specific evidence id from the input bundle — the caller can verify this.

Currently ships the deterministic template. An Anthropic call can be plugged
in later without changing the response schema.
"""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel

from backend.app.schemas.investigation import InvestigationResult


class AIInvestigationReport(BaseModel):
    generated_by: Literal["deterministic", "llm"] = "deterministic"
    grounded: bool = True
    assessment: str
    primary_reasons: List[str]
    supporting_evidence_ids: List[str]
    counter_evidence_ids: List[str]
    entity_notes: List[str]
    confidence: str
    recommended_action: str
    analyst_summary: str
    disclaimer: str = (
        "This narrative summarises the deterministic risk engine's output. "
        "It does not classify fraud on its own; every claim references evidence "
        "produced by the ML model, rules, or behavioural analytics."
    )


def _entity_notes(inv: InvestigationResult) -> List[str]:
    notes = []
    b = inv.behavior
    if b.is_new_device:
        notes.append(
            f"Device {next((e.id for e in inv.entities if e.type == 'device'), 'unknown')} "
            "was not previously associated with this customer."
        )
    if b.is_new_country:
        notes.append(
            "IP originates from a country outside the customer's usual pattern."
        )
    if b.n_prior_tx >= 30:
        notes.append(
            f"Customer has {b.n_prior_tx} prior transactions on record — "
            "long-standing relationship."
        )
    return notes[:4]


def build_report(inv: InvestigationResult) -> AIInvestigationReport:
    top = sorted(inv.supporting_evidence, key=lambda e: -e.weight)[:5]
    counter = sorted(inv.counter_evidence, key=lambda e: e.weight)[:3]

    if inv.risk_level == "CRITICAL":
        headline = "Strong indicators of fraud."
    elif inv.risk_level == "HIGH":
        headline = "Multiple corroborating risk signals present."
    elif inv.risk_level == "MEDIUM":
        headline = "Elevated risk driven by behavioural deviation."
    else:
        headline = "Signals are within normal range for this customer."

    assessment_bits = [headline]
    if top:
        primary = top[0]
        assessment_bits.append(
            f"The strongest signal is: {primary.description} "
            f"(evidence id {primary.id}, weight {primary.weight:.1f})."
        )
    if counter:
        c = counter[0]
        assessment_bits.append(
            f"Counter-signal: {c.description} (evidence id {c.id})."
        )

    primary_reasons = [
        f"[{e.id}] {e.description}" for e in top
    ]

    analyst_summary_bits = [
        f"Risk score {inv.risk_score}/100 ({inv.risk_level}).",
        f"Calibrated ML fraud probability: {inv.fraud_probability:.1%}.",
        f"Behavioural deviation score: {inv.behavioral_deviation:.1f}.",
        f"Recommended action: {inv.recommended_action} "
        f"(engine confidence: {inv.confidence}).",
    ]
    if top:
        analyst_summary_bits.append(
            "Primary drivers: "
            + "; ".join(e.code.replace("_", " ").lower() for e in top[:3])
            + "."
        )
    if counter:
        analyst_summary_bits.append(
            "Counter-evidence considered: "
            + "; ".join(e.code.replace("_", " ").lower() for e in counter)
            + "."
        )
    if inv.risk_level in ("HIGH", "CRITICAL") and inv.confidence != "high":
        analyst_summary_bits.append(
            "Confidence is not high, so analyst review is recommended before final action."
        )

    return AIInvestigationReport(
        generated_by="deterministic",
        grounded=True,
        assessment=" ".join(assessment_bits),
        primary_reasons=primary_reasons,
        supporting_evidence_ids=[e.id for e in top],
        counter_evidence_ids=[e.id for e in counter],
        entity_notes=_entity_notes(inv),
        confidence=inv.confidence,
        recommended_action=inv.recommended_action,
        analyst_summary=" ".join(analyst_summary_bits),
    )
