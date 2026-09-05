"""Risk engine — orchestrates feature building, ML scoring, evidence, fusion,
and decision. Produces a full InvestigationResult and persists it.

This module is the single entry point used by both:
  * the API layer (POST /transactions/score)
  * batch scripts that pre-score seeded live transactions
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db import models
from backend.app.ml import explain, features, model as model_mod
from backend.app.risk import behavior as behavior_mod
from backend.app.risk import decision as decision_mod
from backend.app.risk import fusion as fusion_mod
from backend.app.risk import evidence as evidence_mod
from backend.app.schemas.evidence import Evidence
from backend.app.schemas.investigation import (
    EntityRef,
    InvestigationResult,
    ModelExplanation,
    ShapContribution,
    TimelineEvent,
)
from backend.app.schemas.transaction import TransactionIn
from backend.app.utils.logging import get_logger

log = get_logger(__name__)


def _entities_for(tx_in: TransactionIn) -> list[EntityRef]:
    return [
        EntityRef(type="customer", id=tx_in.customer_id, relation="initiator"),
        EntityRef(type="device", id=tx_in.device_id, relation="used_by"),
        EntityRef(type="ip", id=tx_in.ip_hash, relation="originated_from"),
        EntityRef(type="merchant", id=tx_in.merchant_id, relation="paid_to"),
    ]


def _timeline(tx_in: TransactionIn, history: pd.DataFrame, evidence_count: int,
              action: str) -> list[TimelineEvent]:
    events = []
    if not history.empty:
        first = pd.to_datetime(history["ts"].min())
        events.append(TimelineEvent(
            ts=first,
            event="FIRST_SEEN",
            detail=f"Customer first observed with a transaction at {first.isoformat()}.",
        ))
        last = pd.to_datetime(history["ts"].max())
        events.append(TimelineEvent(
            ts=last,
            event="LAST_ACTIVITY",
            detail=f"Most recent prior transaction at {last.isoformat()} ({len(history)} priors).",
        ))
    events.append(TimelineEvent(
        ts=tx_in.ts,
        event="SCORING",
        detail=(
            f"Transaction {tx_in.tx_id} scored: amount {tx_in.amount:.2f} {tx_in.currency}, "
            f"merchant {tx_in.merchant_id} ({tx_in.merchant_category}), device {tx_in.device_id}."
        ),
    ))
    events.append(TimelineEvent(
        ts=datetime.utcnow(),
        event="INVESTIGATION_BUILT",
        detail=f"Investigation produced with {evidence_count} evidence items, recommended {action}.",
    ))
    return events


def _explanation_sentence(risk_score: int, level: str, action: str,
                          evidence_count: int, top_evidence: list[Evidence]) -> str:
    top = ", ".join(e.description for e in top_evidence[:3]) or "no strong signals"
    return (
        f"Risk score {risk_score}/100 ({level}). Recommended: {action}. "
        f"Basis ({evidence_count} evidence items): {top}"
    )


def _merchant_risk_tier(db: Session, merchant_id: str, fallback: int = 1) -> int:
    m = db.get(models.Merchant, merchant_id)
    return int(m.risk_tier) if m else fallback


def score_transaction(db: Session, tx_in: TransactionIn, persist: bool = True) -> InvestigationResult:
    settings = get_settings()
    loaded = model_mod.load_model()

    # Enrich with derived time fields.
    tx = tx_in.model_dump()
    tx["hour"] = tx_in.ts.hour
    tx["day_of_week"] = tx_in.ts.weekday()
    tx["risk_tier"] = _merchant_risk_tier(db, tx_in.merchant_id)

    # History — strictly prior to this tx.
    history = behavior_mod.load_customer_history(db, tx_in.customer_id, before_ts=tx_in.ts)

    # Features.
    single_frame, baseline = features.build_online_features(tx, history)
    X, _cols = features.encode_matrix(single_frame)

    if X.shape[1] != len(loaded.feature_columns):
        raise RuntimeError(
            f"Feature dimension mismatch: got {X.shape[1]}, model expects {len(loaded.feature_columns)}."
        )

    raw_p, cal_p = model_mod.predict_proba(loaded, X)
    fraud_probability = float(cal_p[0])

    # Behavior snapshot for the UI.
    behavior_snapshot = behavior_mod.snapshot_from_history(history, tx)

    # SHAP / fallback contributions.
    shap_top, method = explain.top_k_contributions(loaded, X, k=8)
    shap_contribs = [
        ShapContribution(feature=name, value=val, contribution=contrib)
        for name, val, contrib in shap_top
    ]
    model_explanation = ModelExplanation(top_features=shap_contribs, method=method)

    # Evidence engine.
    evidence_bundle = evidence_mod.build_evidence(
        tx=tx,
        features_row=single_frame.iloc[0].to_dict(),
        behavior=behavior_snapshot,
        fraud_probability=fraud_probability,
        shap_top=shap_top,
    )

    # Fusion + decision.
    fused = fusion_mod.fuse(fraud_probability, evidence_bundle)
    dec = decision_mod.decide(
        risk_level=fused.risk_level,
        risk_score=fused.risk_score,
        fraud_probability=fraud_probability,
        evidence=evidence_bundle,
        amount=float(tx_in.amount),
        prior_tx=behavior_snapshot.n_prior_tx,
    )

    # Behavioral deviation summary (single number for UI).
    z = behavior_snapshot.amount_z_score if behavior_snapshot.amount_z_score is not None else 0.0
    behavioral_deviation = round(
        (abs(z) * 12.0)
        + (10.0 if behavior_snapshot.is_new_device else 0.0)
        + (8.0 if behavior_snapshot.is_new_country else 0.0)
        + (6.0 if behavior_snapshot.unusual_hour else 0.0),
        2,
    )

    # Simple anomaly proxy: how far this row's numeric features are from the training background.
    if loaded.background is not None and loaded.background.size > 0:
        bg_mean = loaded.background.mean(axis=0)
        bg_std = loaded.background.std(axis=0)
        bg_std[bg_std == 0] = 1.0
        z_row = np.abs((X[0] - bg_mean) / bg_std)
        anomaly_score = float(np.mean(np.tanh(z_row / 3.0)))
    else:
        anomaly_score = 0.0

    top_evidence_sorted = sorted(evidence_bundle.supporting, key=lambda e: -e.weight)
    explanation = _explanation_sentence(
        risk_score=fused.risk_score,
        level=fused.risk_level,
        action=dec.action,
        evidence_count=len(evidence_bundle.supporting),
        top_evidence=top_evidence_sorted,
    )
    risk_factors = [e.description for e in top_evidence_sorted[:6]]

    result = InvestigationResult(
        transaction_id=tx_in.tx_id,
        ts=tx_in.ts,
        customer_id=tx_in.customer_id,
        merchant_id=tx_in.merchant_id,
        amount=float(tx_in.amount),
        currency=tx_in.currency,
        risk_score=fused.risk_score,
        risk_level=fused.risk_level,
        fraud_probability=fraud_probability,
        anomaly_score=anomaly_score,
        behavioral_deviation=behavioral_deviation,
        risk_factors=risk_factors,
        supporting_evidence=evidence_bundle.supporting,
        counter_evidence=evidence_bundle.counter,
        recommended_action=dec.action,
        confidence=dec.confidence,
        explanation=explanation,
        model_explanation=model_explanation,
        behavior=behavior_snapshot,
        timeline=_timeline(tx_in, history, len(evidence_bundle.supporting), dec.action),
        entities=_entities_for(tx_in),
        model_version=loaded.model_version,
        created_at=datetime.utcnow(),
    )

    if persist:
        _persist(db, tx_in, tx, result)

    return result


def _persist(db: Session, tx_in: TransactionIn, tx_full: dict, result: InvestigationResult) -> None:
    """Upsert customer/merchant/device rows and the transaction, then the investigation."""
    if db.get(models.Customer, tx_in.customer_id) is None:
        db.add(models.Customer(
            customer_id=tx_in.customer_id,
            country=tx_in.customer_country,
        ))
    if db.get(models.Merchant, tx_in.merchant_id) is None:
        db.add(models.Merchant(
            merchant_id=tx_in.merchant_id,
            category=tx_in.merchant_category,
            risk_tier=tx_full["risk_tier"],
        ))
    if db.get(models.Device, tx_in.device_id) is None:
        db.add(models.Device(device_id=tx_in.device_id))

    if db.get(models.Transaction, tx_in.tx_id) is None:
        db.add(models.Transaction(
            tx_id=tx_in.tx_id,
            ts=tx_in.ts,
            customer_id=tx_in.customer_id,
            merchant_id=tx_in.merchant_id,
            merchant_category=tx_in.merchant_category,
            device_id=tx_in.device_id,
            ip_hash=tx_in.ip_hash,
            ip_country=tx_in.ip_country,
            customer_country=tx_in.customer_country,
            amount=float(tx_in.amount),
            currency=tx_in.currency,
            channel=tx_in.channel,
            auth_result=tx_in.auth_result,
            hour=tx_full["hour"],
            day_of_week=tx_full["day_of_week"],
            split="live",
        ))

    existing_inv = db.get(models.Investigation, tx_in.tx_id)
    payload = result.model_dump(mode="json")
    if existing_inv is None:
        db.add(models.Investigation(
            tx_id=tx_in.tx_id,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            recommended_action=result.recommended_action,
            fraud_probability=result.fraud_probability,
            anomaly_score=result.anomaly_score,
            behavioral_deviation=result.behavioral_deviation,
            confidence=result.confidence,
            payload_json=payload,
            model_version=result.model_version,
        ))
    else:
        existing_inv.risk_score = result.risk_score
        existing_inv.risk_level = result.risk_level
        existing_inv.recommended_action = result.recommended_action
        existing_inv.fraud_probability = result.fraud_probability
        existing_inv.anomaly_score = result.anomaly_score
        existing_inv.behavioral_deviation = result.behavioral_deviation
        existing_inv.confidence = result.confidence
        existing_inv.payload_json = payload
        existing_inv.model_version = result.model_version

    db.add(models.AuditEvent(
        actor="system",
        action="SCORE_TRANSACTION",
        entity_type="transaction",
        entity_id=tx_in.tx_id,
        payload_json={
            "risk_score": result.risk_score,
            "risk_level": result.risk_level,
            "action": result.recommended_action,
            "confidence": result.confidence,
        },
    ))
    db.commit()
