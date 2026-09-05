"""Audit trail endpoint — read-only, append-only append-elsewhere."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.decision import AuditEventOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=List[AuditEventOut])
def list_audit(
    db: Session = Depends(get_db),
    entity_id: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> List[AuditEventOut]:
    stmt = select(models.AuditEvent).order_by(desc(models.AuditEvent.created_at)).limit(limit)
    if entity_id:
        stmt = stmt.where(models.AuditEvent.entity_id == entity_id)
    if action:
        stmt = stmt.where(models.AuditEvent.action == action)
    rows = db.scalars(stmt).all()
    return [
        AuditEventOut(
            id=r.id, actor=r.actor, action=r.action, entity_type=r.entity_type,
            entity_id=r.entity_id, payload_json=r.payload_json, created_at=r.created_at,
        )
        for r in rows
    ]
