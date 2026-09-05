from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Dict, Any

from backend.app.database.session import get_db
from backend.app.database.models import InvestigationModel, TransactionModel
from backend.app.schemas.decision import AnalystDecisionRequest
from backend.app.schemas.investigation import InvestigationContextResponse
from backend.app.services.investigation_service import InvestigationService
from backend.app.investigation.ai_investigator import AIInvestigator

router = APIRouter()


@router.get("/investigations")
def list_investigations(
    risk_level: Optional[str] = Query(None, description="Filter by risk level: LOW, MEDIUM, HIGH, CRITICAL"),
    status: Optional[str] = Query(None, description="Filter by status: PENDING, IN_REVIEW, RESOLVED"),
    search: Optional[str] = Query(None, description="Search by transaction, customer, or merchant ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Returns filterable, paginated queue of investigations for risk operations.
    """
    query = db.query(InvestigationModel).join(TransactionModel)

    if risk_level:
        query = query.filter(InvestigationModel.risk_level == risk_level.upper())
    if status:
        query = query.filter(InvestigationModel.status == status.upper())
    if search:
        s = f"%{search}%"
        query = query.filter(
            (InvestigationModel.transaction_id.ilike(s)) |
            (TransactionModel.customer_id.ilike(s)) |
            (TransactionModel.merchant_id.ilike(s))
        )

    total = query.count()
    items = query.order_by(desc(InvestigationModel.risk_score), desc(InvestigationModel.created_at)).offset(offset).limit(limit).all()

    results = []
    for inv in items:
        tx = inv.transaction
        results.append({
            "investigation_id": inv.investigation_id,
            "transaction_id": inv.transaction_id,
            "customer_id": tx.customer_id if tx else "N/A",
            "merchant_id": tx.merchant_id if tx else "N/A",
            "amount": tx.amount if tx else 0.0,
            "currency": tx.currency if tx else "INR",
            "risk_score": inv.risk_score,
            "risk_level": inv.risk_level,
            "status": inv.status,
            "priority": inv.priority,
            "policy_recommendation": inv.policy_recommendation,
            "analyst_decision": inv.analyst_decision,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        })

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": results
    }


@router.get("/investigations/{transaction_id}")
def get_investigation_detail(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves full unified investigation context for a specific transaction ID.
    """
    context = InvestigationService.get_investigation_context(transaction_id, db)
    if not context:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found.")
    return context


@router.post("/investigations/{transaction_id}/analyze")
def trigger_ai_analysis(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Forces a fresh AI investigation run (Gemini LLM if key set, else deterministic fallback).
    """
    context = InvestigationService.get_investigation_context(transaction_id, db)
    if not context:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found.")

    assessment = AIInvestigator.investigate(context)

    # Update in DB
    inv = db.query(InvestigationModel).filter(InvestigationModel.transaction_id == transaction_id).first()
    if inv:
        import json
        inv.ai_assessment_json = json.dumps(assessment.model_dump())
        inv.ai_is_fallback = assessment.is_deterministic_fallback
        db.commit()

    return {
        "status": "success",
        "data": assessment.model_dump()
    }


@router.post("/investigations/{transaction_id}/decision")
def submit_analyst_decision(
    transaction_id: str,
    payload: AnalystDecisionRequest,
    db: Session = Depends(get_db)
):
    """
    Records an analyst human-in-the-loop decision, overriding recommendation and persisting audit trail.
    """
    try:
        result = InvestigationService.record_analyst_decision(
            transaction_id=transaction_id,
            decision=payload.decision,
            reason=payload.reason,
            analyst_id=payload.analyst_id or "analyst_ops_1",
            db=db
        )
        return {
            "status": "success",
            "data": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record decision: {str(e)}")


@router.get("/investigations/{transaction_id}/timeline")
def get_transaction_timeline(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    context = InvestigationService.get_investigation_context(transaction_id, db)
    if not context:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found.")
    return {"transaction_id": transaction_id, "timeline": context.get("timeline", [])}


@router.get("/investigations/{transaction_id}/entities")
def get_transaction_entities(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    context = InvestigationService.get_investigation_context(transaction_id, db)
    if not context:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found.")
    return {"transaction_id": transaction_id, "entities": context.get("entities", {})}


@router.get("/investigations/{transaction_id}/evidence")
def get_transaction_evidence(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    context = InvestigationService.get_investigation_context(transaction_id, db)
    if not context:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found.")
    return {
        "transaction_id": transaction_id,
        "evidence": context.get("evidence", []),
        "counter_evidence": context.get("counter_evidence", [])
    }
