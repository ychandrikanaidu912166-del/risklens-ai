from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.app.database.session import get_db
from backend.app.schemas.transaction import TransactionCreate
from backend.app.services.investigation_service import InvestigationService

router = APIRouter()


@router.post("/transactions/score")
def score_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Ingests and scores an incoming transaction in real-time.
    Runs ML model, behavioural deviations, evidence generation, risk fusion,
    policy evaluation, and saves transaction and investigation context.
    """
    try:
        tx_dict = payload.model_dump()
        result = InvestigationService.score_and_process_transaction(tx_dict, db)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to score transaction: {str(e)}")
