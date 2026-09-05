"""AI investigation endpoint — wraps the deterministic investigator."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.ai.investigator import AIInvestigationReport, build_report
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.investigation import InvestigationResult

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.get("/{tx_id}/ai-report", response_model=AIInvestigationReport)
def ai_report(tx_id: str, db: Session = Depends(get_db)) -> AIInvestigationReport:
    inv = db.get(models.Investigation, tx_id)
    if inv is None:
        raise HTTPException(status_code=404, detail=f"Investigation for {tx_id} not found")
    result = InvestigationResult(**inv.payload_json)
    return build_report(result)
