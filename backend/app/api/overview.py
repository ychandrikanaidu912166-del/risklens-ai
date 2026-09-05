"""Overview dashboard KPIs computed from the live/persisted data."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db import models
from backend.app.db.database import get_db

router = APIRouter(prefix="/overview", tags=["overview"])


class OverviewMetrics(BaseModel):
    total_transactions: int
    scored_transactions: int
    live_transactions: int
    low_count: int
    medium_count: int
    high_count: int
    critical_count: int
    review_queue_count: int
    action_distribution: Dict[str, int]
    risk_level_distribution: Dict[str, int]
    model: Dict[str, object]
    recent_investigations: List[Dict[str, object]]


@router.get("", response_model=OverviewMetrics)
def overview(db: Session = Depends(get_db)) -> OverviewMetrics:
    total_tx = int(db.scalar(select(func.count(models.Transaction.tx_id))) or 0)
    live_tx = int(db.scalar(
        select(func.count(models.Transaction.tx_id)).where(models.Transaction.split == "live")
    ) or 0)
    scored = int(db.scalar(select(func.count(models.Investigation.tx_id))) or 0)

    level_rows = db.execute(
        select(models.Investigation.risk_level, func.count(models.Investigation.tx_id))
        .group_by(models.Investigation.risk_level)
    ).all()
    level_dist = {r[0]: int(r[1]) for r in level_rows}
    for k in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        level_dist.setdefault(k, 0)

    action_rows = db.execute(
        select(models.Investigation.recommended_action, func.count(models.Investigation.tx_id))
        .group_by(models.Investigation.recommended_action)
    ).all()
    action_dist = {r[0]: int(r[1]) for r in action_rows}

    review_actions = ("MANUAL_REVIEW", "HOLD", "STEP_UP")
    review_queue = sum(action_dist.get(a, 0) for a in review_actions)

    # Recent investigations for the dashboard's activity feed.
    recent_rows = db.execute(
        select(models.Investigation, models.Transaction)
        .join(models.Transaction, models.Investigation.tx_id == models.Transaction.tx_id)
        .order_by(models.Investigation.created_at.desc())
        .limit(8)
    ).all()
    recent = [
        {
            "tx_id": inv.tx_id,
            "customer_id": tx.customer_id,
            "amount": float(tx.amount),
            "currency": tx.currency,
            "risk_score": int(inv.risk_score),
            "risk_level": inv.risk_level,
            "recommended_action": inv.recommended_action,
            "created_at": inv.created_at.isoformat(),
        }
        for inv, tx in recent_rows
    ]

    metrics_path = Path(get_settings().artifact_dir) / "metrics.json"
    model_info: Dict[str, object] = {"available": False}
    if metrics_path.exists():
        try:
            m = json.loads(metrics_path.read_text())
            p = m.get("primary", {})
            model_info = {
                "available": True,
                "model_version": m.get("model_version"),
                "model_kind": m.get("model_kind"),
                "precision": p.get("precision"),
                "recall": p.get("recall"),
                "f1": p.get("f1"),
                "pr_auc": p.get("pr_auc"),
                "roc_auc": p.get("roc_auc"),
                "fpr": p.get("fpr"),
                "fnr": p.get("fnr"),
                "expected_business_cost": p.get("business_cost", {}).get("expected_business_cost"),
            }
        except (json.JSONDecodeError, KeyError):
            model_info = {"available": False}

    return OverviewMetrics(
        total_transactions=total_tx,
        scored_transactions=scored,
        live_transactions=live_tx,
        low_count=level_dist["LOW"],
        medium_count=level_dist["MEDIUM"],
        high_count=level_dist["HIGH"],
        critical_count=level_dist["CRITICAL"],
        review_queue_count=review_queue,
        action_distribution=action_dist,
        risk_level_distribution=level_dist,
        model=model_info,
        recent_investigations=recent,
    )
