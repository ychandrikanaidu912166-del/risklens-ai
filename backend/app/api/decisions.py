"""Analyst decision endpoints — persists to the `decisions` table
and writes an audit event. Feedback is stored but NEVER auto-fed into
model training.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.decision import DecisionIn, DecisionOut

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post("", response_model=DecisionOut, status_code=201)
def create_decision(payload: DecisionIn, db: Session = Depends(get_db)) -> DecisionOut:
    if db.get(models.Transaction, payload.tx_id) is None:
        raise HTTPException(status_code=404, detail=f"Transaction {payload.tx_id} not found")

    row = models.Decision(
        tx_id=payload.tx_id,
        analyst_id=payload.analyst_id,
        action=payload.action,
        reason=payload.reason,
    )
    db.add(row)
    db.flush()

    db.add(models.AuditEvent(
        actor=payload.analyst_id,
        action="ANALYST_DECISION",
        entity_type="transaction",
        entity_id=payload.tx_id,
        payload_json={"action": payload.action, "reason": payload.reason},
    ))
    db.commit()
    db.refresh(row)

    return DecisionOut(
        id=row.id,
        tx_id=row.tx_id,
        action=row.action,  # type: ignore[arg-type]
        reason=row.reason,
        analyst_id=row.analyst_id,
        created_at=row.created_at,
    )


@router.get("", response_model=List[DecisionOut])
def list_decisions(
    db: Session = Depends(get_db),
    tx_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> List[DecisionOut]:
    stmt = select(models.Decision).order_by(desc(models.Decision.created_at)).limit(limit)
    if tx_id:
        stmt = stmt.where(models.Decision.tx_id == tx_id)
    rows = db.scalars(stmt).all()
    return [
        DecisionOut(
            id=r.id, tx_id=r.tx_id, action=r.action,  # type: ignore[arg-type]
            reason=r.reason, analyst_id=r.analyst_id, created_at=r.created_at,
        )
        for r in rows
    ]
