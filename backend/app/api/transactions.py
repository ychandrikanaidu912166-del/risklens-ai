"""Transaction endpoints."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.risk import engine
from backend.app.schemas.investigation import InvestigationResult
from backend.app.schemas.transaction import TransactionIn, TransactionSummary

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/score", response_model=InvestigationResult)
def score(tx: TransactionIn, db: Session = Depends(get_db)) -> InvestigationResult:
    try:
        return engine.score_transaction(db, tx, persist=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("", response_model=List[TransactionSummary])
def list_transactions(
    db: Session = Depends(get_db),
    risk_level: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> List[TransactionSummary]:
    stmt = (
        select(models.Transaction, models.Investigation)
        .join(models.Investigation, models.Transaction.tx_id == models.Investigation.tx_id)
        .order_by(desc(models.Transaction.ts))
        .limit(limit)
        .offset(offset)
    )
    if risk_level:
        stmt = stmt.where(models.Investigation.risk_level == risk_level.upper())
    if action:
        stmt = stmt.where(models.Investigation.recommended_action == action.upper())

    rows = db.execute(stmt).all()
    out: List[TransactionSummary] = []
    for tx, inv in rows:
        out.append(TransactionSummary(
            tx_id=tx.tx_id,
            ts=tx.ts,
            customer_id=tx.customer_id,
            merchant_id=tx.merchant_id,
            amount=tx.amount,
            currency=tx.currency,
            risk_score=inv.risk_score,
            risk_level=inv.risk_level,
            recommended_action=inv.recommended_action,
            status="scored",
        ))
    return out


@router.get("/{tx_id}")
def get_transaction(tx_id: str, db: Session = Depends(get_db)) -> dict:
    tx = db.get(models.Transaction, tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail=f"Transaction {tx_id} not found")
    return {
        "tx_id": tx.tx_id,
        "ts": tx.ts.isoformat(),
        "customer_id": tx.customer_id,
        "merchant_id": tx.merchant_id,
        "merchant_category": tx.merchant_category,
        "amount": tx.amount,
        "currency": tx.currency,
        "device_id": tx.device_id,
        "ip_hash": tx.ip_hash,
        "ip_country": tx.ip_country,
        "customer_country": tx.customer_country,
        "channel": tx.channel,
        "auth_result": tx.auth_result,
        "hour": tx.hour,
        "day_of_week": tx.day_of_week,
        "split": tx.split,
    }
