import uuid
import json
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database.models import (
    TransactionModel,
    InvestigationModel,
    EvidenceItemModel,
    CounterEvidenceItemModel,
    TimelineEventModel,
)
from backend.app.audit.service import AuditService
from ml.models.predictor import predictor
from backend.app.risk_engine.behaviour import BehaviourEngine
from backend.app.risk_engine.evidence import EvidenceEngine
from backend.app.risk_engine.counter_evidence import CounterEvidenceEngine
from backend.app.risk_engine.entity_graph import entity_graph
from backend.app.risk_engine.fusion import RiskFusionEngine
from backend.app.investigation.ai_investigator import AIInvestigator
from backend.app.decision_engine.policy import DecisionPolicyEngine


class InvestigationService:

    @classmethod
    def score_and_process_transaction(
        cls,
        tx_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        End-to-end transaction intelligence processing:
        Validation -> ML Inference -> Behaviour Baseline -> Evidence -> Fusion -> AI -> Policy -> DB.
        """
        txn_id = tx_data.get("transaction_id", f"txn_{uuid.uuid4().hex[:8]}")
        cust_id = tx_data.get("customer_id", "cust_unknown")
        
        # 1. Register in entity graph
        entity_graph.register_transaction(tx_data)
        entity_signals = entity_graph.analyze_entity_correlations(tx_data)

        # 2. Query customer history from DB for dynamic baseline
        prior_txs_models = db.query(TransactionModel).filter(
            TransactionModel.customer_id == cust_id,
            TransactionModel.transaction_id != txn_id
        ).order_by(desc(TransactionModel.timestamp)).limit(50).all()

        prior_txs = [
            {
                "amount": t.amount,
                "device_id": t.device_id,
                "country": t.country,
                "ip_address": t.ip_address,
                "merchant_id": t.merchant_id,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
            }
            for t in prior_txs_models
        ]

        if prior_txs:
            baseline = BehaviourEngine.calculate_customer_baseline(prior_txs)
        else:
            # Fall back to payload-provided historical indicators
            base_avg = float(tx_data.get("customer_avg_amount", 1000.0))
            baseline = {
                "transaction_count": int(tx_data.get("customer_transaction_count", 0)),
                "avg_amount": base_avg,
                "median_amount": base_avg * 0.9,
                "min_amount": base_avg * 0.2,
                "max_amount": float(tx_data.get("customer_max_amount", base_avg * 2.0)),
                "p95_amount": base_avg * 2.5,
                "known_devices": [tx_data.get("customer_usual_device")] if tx_data.get("customer_usual_device") else [],
                "known_ips": [tx_data.get("ip_address")] if tx_data.get("ip_address") else [],
                "known_countries": [tx_data.get("customer_usual_country", "IN")],
                "active_hours": list(range(8, 23)),
                "known_merchants": [],
            }

        # 3. Supervised ML Scoring
        try:
            ml_prob, is_fraud_flag, feat_dict = predictor.predict_probability(tx_data)
        except Exception as e:
            ml_prob = 0.15
            is_fraud_flag = False
            feat_dict = {}

        # 4. Behavioural Deviations
        behaviour_diff = BehaviourEngine.compare_transaction(tx_data, baseline)

        # 5. Evidence & Counter-Evidence
        evidence = EvidenceEngine.generate_evidence(tx_data, behaviour_diff, ml_prob, entity_signals)
        counter_evidence = CounterEvidenceEngine.generate_counter_evidence(tx_data, baseline, behaviour_diff)

        # 6. Risk Fusion
        fusion_result = RiskFusionEngine.fuse_signals(
            ml_prob=ml_prob,
            behaviour_diff=behaviour_diff,
            evidence_list=evidence,
            counter_evidence_list=counter_evidence,
            entity_signals=entity_signals
        )
        risk_score = fusion_result["risk_score"]
        risk_level = fusion_result["risk_level"]

        # 7. AI Investigator
        ai_input_context = {
            "transaction": tx_data,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "ml_output": {"fraud_probability": round(ml_prob, 4), "flag": is_fraud_flag},
            "risk_factors": fusion_result["factors"],
            "evidence": evidence,
            "counter_evidence": counter_evidence,
            "customer_behaviour": behaviour_diff,
            "entities": entity_graph.get_entity_graph_for_transaction(tx_data),
        }
        ai_assessment = AIInvestigator.investigate(ai_input_context)

        # 8. Decision Policy Engine
        policy_result = DecisionPolicyEngine.evaluate_decision({
            "risk_score": risk_score,
            "risk_level": risk_level,
            "ai_investigation": ai_assessment.model_dump(),
            "evidence": evidence,
            "counter_evidence": counter_evidence,
            "transaction": tx_data,
        })

        # 9. Persist Transaction & Investigation to Database
        # Check if transaction already exists
        existing_tx = db.query(TransactionModel).filter(TransactionModel.transaction_id == txn_id).first()
        if not existing_tx:
            ts = datetime.datetime.fromisoformat(tx_data["timestamp"]) if tx_data.get("timestamp") else datetime.datetime.utcnow()
            tx_record = TransactionModel(
                transaction_id=txn_id,
                customer_id=cust_id,
                merchant_id=tx_data.get("merchant_id", "merch_001"),
                amount=float(tx_data.get("amount", 0.0)),
                currency=tx_data.get("currency", "INR"),
                timestamp=ts,
                device_id=tx_data.get("device_id", ""),
                ip_address=tx_data.get("ip_address", ""),
                country=tx_data.get("country", "IN"),
                payment_method=tx_data.get("payment_method", "upi"),
                transaction_status=tx_data.get("transaction_status", "success"),
                customer_age_days=int(tx_data.get("customer_age_days", 30)),
                customer_transaction_count=int(tx_data.get("customer_transaction_count", 0)),
                customer_avg_amount=float(tx_data.get("customer_avg_amount", 1000.0)),
                customer_max_amount=float(tx_data.get("customer_max_amount", 1000.0)),
                customer_usual_country=tx_data.get("customer_usual_country", "IN"),
                customer_usual_device=tx_data.get("customer_usual_device", ""),
                transactions_last_10m=int(tx_data.get("transactions_last_10m", 0)),
                transactions_last_1h=int(tx_data.get("transactions_last_1h", 0)),
                transactions_last_24h=int(tx_data.get("transactions_last_24h", 0)),
                is_new_device=int(tx_data.get("is_new_device", 0)),
                is_new_country=int(tx_data.get("is_new_country", 0)),
                is_unusual_hour=int(tx_data.get("is_unusual_hour", 0)),
                is_fraud=int(tx_data.get("is_fraud", 0)),
                risk_score=risk_score,
                risk_level=risk_level,
                ml_probability=round(ml_prob, 4),
            )
            db.add(tx_record)
            db.commit()

        # Create or update Investigation
        inv_id = f"inv_{txn_id}"
        inv_record = db.query(InvestigationModel).filter(InvestigationModel.transaction_id == txn_id).first()
        if not inv_record:
            inv_record = InvestigationModel(
                investigation_id=inv_id,
                transaction_id=txn_id,
                risk_score=risk_score,
                risk_level=risk_level,
                status="PENDING" if risk_score >= 30 else "RESOLVED",
                priority="URGENT" if risk_score >= 85 else ("HIGH" if risk_score >= 60 else "MEDIUM"),
                policy_recommendation=policy_result["decision"],
                automation_allowed=policy_result["automation_allowed"],
                evidence_quality=policy_result["evidence_quality"],
                ai_assessment_json=json.dumps(ai_assessment.model_dump()),
                ai_is_fallback=ai_assessment.is_deterministic_fallback,
                model_version=predictor.model_version,
                policy_version=policy_result["policy_version"],
            )
            db.add(inv_record)
            db.commit()

            # Add Evidence Items
            for ev in evidence:
                db.add(EvidenceItemModel(
                    investigation_id=inv_id,
                    evidence_id=ev["evidence_id"],
                    type=ev["type"],
                    source=ev["source"],
                    description=ev["description"],
                    severity=ev["severity"],
                    observed_value=ev.get("observed_value"),
                    baseline_value=ev.get("baseline_value"),
                    timestamp=ev.get("timestamp"),
                ))

            # Add Counter Evidence Items
            for cev in counter_evidence:
                db.add(CounterEvidenceItemModel(
                    investigation_id=inv_id,
                    item_id=cev["id"],
                    type=cev["type"],
                    title=cev["title"],
                    description=cev["description"],
                    confidence_impact=cev.get("confidence_impact", 0),
                    timestamp=cev.get("timestamp"),
                ))

            # Add Timeline Events
            base_time = tx_data.get("timestamp", datetime.datetime.utcnow().isoformat())
            dt_base = datetime.datetime.fromisoformat(base_time) if isinstance(base_time, str) and "T" in base_time else datetime.datetime.utcnow()

            db.add(TimelineEventModel(
                transaction_id=txn_id,
                event_type="SESSION_START",
                title="Customer Session Authenticated",
                description=f"Device {tx_data.get('device_id')} connected from IP {tx_data.get('ip_address')}.",
                severity="INFO",
                timestamp=dt_base - datetime.timedelta(minutes=4),
            ))
            db.add(TimelineEventModel(
                transaction_id=txn_id,
                event_type="PAYMENT_ATTEMPT",
                title="Payment Initiated",
                description=f"Initiated {tx_data.get('currency', 'INR')} {tx_data.get('amount')} via {tx_data.get('payment_method')} to merchant {tx_data.get('merchant_id')}.",
                severity="INFO",
                timestamp=dt_base,
            ))
            db.add(TimelineEventModel(
                transaction_id=txn_id,
                event_type="RISK_SCORING",
                title=f"Risk Fusion Evaluated ({risk_level} - {risk_score}/100)",
                description=f"Risk score {risk_score} calculated across {len(fusion_result['factors'])} factors. Supervised ML prob: {ml_prob * 100:.1f}%.",
                severity="WARNING" if risk_score >= 60 else "INFO",
                timestamp=dt_base + datetime.timedelta(seconds=2),
            ))
            db.add(TimelineEventModel(
                transaction_id=txn_id,
                event_type="POLICY_RECOMMENDATION",
                title=f"Policy Recommendation: {policy_result['decision']}",
                description=policy_result["reason"],
                severity="CRITICAL" if policy_result["decision"] in ["BLOCK", "HOLD"] else "INFO",
                timestamp=dt_base + datetime.timedelta(seconds=4),
            ))

            db.commit()

            # Record Audit Trail
            AuditService.record_event(
                db=db,
                event_type="TRANSACTION_SCORED",
                action="SCORE",
                entity_type="transaction",
                entity_id=txn_id,
                actor="risk_engine",
                details={
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "decision": policy_result["decision"],
                    "ml_prob": round(ml_prob, 4),
                },
            )

        return {
            "transaction_id": txn_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "ml_probability": round(ml_prob, 4),
            "recommendation": policy_result["decision"],
            "factors": fusion_result["factors"],
            "evidence_count": len(evidence),
            "counter_evidence_count": len(counter_evidence),
        }

    @classmethod
    def get_investigation_context(cls, transaction_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Retrieves complete, unified investigation context for analyst workbench.
        """
        tx = db.query(TransactionModel).filter(TransactionModel.transaction_id == transaction_id).first()
        if not tx:
            return None

        inv = db.query(InvestigationModel).filter(InvestigationModel.transaction_id == transaction_id).first()

        # If investigation not yet generated, score and generate it
        if not inv:
            cls.score_and_process_transaction({
                "transaction_id": tx.transaction_id,
                "customer_id": tx.customer_id,
                "merchant_id": tx.merchant_id,
                "amount": tx.amount,
                "currency": tx.currency,
                "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                "device_id": tx.device_id,
                "ip_address": tx.ip_address,
                "country": tx.country,
                "payment_method": tx.payment_method,
                "transaction_status": tx.transaction_status,
                "customer_age_days": tx.customer_age_days,
                "customer_transaction_count": tx.customer_transaction_count,
                "customer_avg_amount": tx.customer_avg_amount,
                "customer_max_amount": tx.customer_max_amount,
                "customer_usual_country": tx.customer_usual_country,
                "customer_usual_device": tx.customer_usual_device,
                "transactions_last_10m": tx.transactions_last_10m,
                "transactions_last_1h": tx.transactions_last_1h,
                "transactions_last_24h": tx.transactions_last_24h,
                "is_new_device": tx.is_new_device,
                "is_new_country": tx.is_new_country,
                "is_unusual_hour": tx.is_unusual_hour,
                "is_fraud": tx.is_fraud,
            }, db)
            inv = db.query(InvestigationModel).filter(InvestigationModel.transaction_id == transaction_id).first()

        # Fetch evidence and counter evidence
        ev_records = db.query(EvidenceItemModel).filter(EvidenceItemModel.investigation_id == inv.investigation_id).all()
        cev_records = db.query(CounterEvidenceItemModel).filter(CounterEvidenceItemModel.investigation_id == inv.investigation_id).all()
        timeline_records = db.query(TimelineEventModel).filter(TimelineEventModel.transaction_id == transaction_id).order_by(TimelineEventModel.timestamp).all()

        # Build baseline comparison
        baseline = {
            "avg_amount": tx.customer_avg_amount,
            "median_amount": round(tx.customer_avg_amount * 0.95, 2),
            "p95_amount": round(tx.customer_avg_amount * 2.2, 2),
            "known_devices": [tx.customer_usual_device] if tx.customer_usual_device else [],
            "known_countries": [tx.customer_usual_country] if tx.customer_usual_country else ["IN"],
            "active_hours": list(range(8, 23)),
        }
        tx_dict = {
            "transaction_id": tx.transaction_id,
            "customer_id": tx.customer_id,
            "merchant_id": tx.merchant_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
            "device_id": tx.device_id,
            "ip_address": tx.ip_address,
            "country": tx.country,
            "payment_method": tx.payment_method,
            "transaction_status": tx.transaction_status,
            "customer_age_days": tx.customer_age_days,
            "customer_transaction_count": tx.customer_transaction_count,
            "customer_avg_amount": tx.customer_avg_amount,
            "customer_max_amount": tx.customer_max_amount,
            "transactions_last_10m": tx.transactions_last_10m,
            "transactions_last_1h": tx.transactions_last_1h,
            "transactions_last_24h": tx.transactions_last_24h,
            "is_new_device": tx.is_new_device,
            "is_new_country": tx.is_new_country,
            "is_unusual_hour": tx.is_unusual_hour,
            "is_fraud": tx.is_fraud,
        }
        behaviour_diff = BehaviourEngine.compare_transaction(tx_dict, baseline)

        # Entity graph
        graph = entity_graph.get_entity_graph_for_transaction(tx_dict)

        # AI assessment parsing
        ai_assessment = None
        if inv.ai_assessment_json:
            try:
                ai_assessment = json.loads(inv.ai_assessment_json)
            except Exception:
                pass

        # Factors reconstruct
        fusion_calc = RiskFusionEngine.fuse_signals(
            ml_prob=tx.ml_probability,
            behaviour_diff=behaviour_diff,
            evidence_list=[{"evidence_id": e.evidence_id, "type": e.type, "severity": e.severity, "description": e.description} for e in ev_records],
            counter_evidence_list=[{"id": c.item_id, "type": c.type, "description": c.description} for c in cev_records],
            entity_signals=[]
        )

        existing_decision = None
        if inv.analyst_decision:
            existing_decision = {
                "decision": inv.analyst_decision,
                "reason": inv.analyst_reason,
                "timestamp": inv.decision_timestamp.isoformat() if inv.decision_timestamp else None,
                "status": inv.status,
            }

        return {
            "transaction": tx_dict,
            "risk_score": inv.risk_score,
            "risk_level": inv.risk_level,
            "ml_output": {
                "fraud_probability": tx.ml_probability,
                "is_fraud_flag": bool(tx.ml_probability >= 0.70),
                "model_version": inv.model_version,
            },
            "risk_factors": fusion_calc["factors"],
            "evidence": [
                {
                    "evidence_id": e.evidence_id,
                    "type": e.type,
                    "source": e.source,
                    "description": e.description,
                    "severity": e.severity,
                    "observed_value": e.observed_value,
                    "baseline_value": e.baseline_value,
                    "timestamp": e.timestamp,
                    "related_entity_ids": [tx.transaction_id, tx.customer_id],
                }
                for e in ev_records
            ],
            "counter_evidence": [
                {
                    "id": c.item_id,
                    "type": c.type,
                    "title": c.title,
                    "description": c.description,
                    "confidence_impact": c.confidence_impact,
                    "timestamp": c.timestamp,
                }
                for c in cev_records
            ],
            "customer_behaviour": behaviour_diff,
            "entities": graph,
            "timeline": [
                {
                    "id": t.id,
                    "event_type": t.event_type,
                    "title": t.title,
                    "description": t.description,
                    "severity": t.severity,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                }
                for t in timeline_records
            ],
            "recommended_action": inv.policy_recommendation,
            "model_version": inv.model_version,
            "policy_version": inv.policy_version,
            "existing_decision": existing_decision,
            "ai_investigation": ai_assessment,
        }

    @classmethod
    def record_analyst_decision(
        cls,
        transaction_id: str,
        decision: str,
        reason: str,
        analyst_id: str,
        db: Session
    ) -> Dict[str, Any]:
        inv = db.query(InvestigationModel).filter(InvestigationModel.transaction_id == transaction_id).first()
        if not inv:
            raise ValueError(f"Investigation for transaction {transaction_id} not found.")

        valid_decisions = ["APPROVE", "HOLD", "BLOCK", "FALSE_POSITIVE", "ESCALATE"]
        if decision.upper() not in valid_decisions:
            raise ValueError(f"Invalid decision '{decision}'. Must be one of {valid_decisions}")

        now = datetime.datetime.utcnow()
        inv.analyst_decision = decision.upper()
        inv.analyst_reason = reason
        inv.decision_timestamp = now
        inv.status = "RESOLVED"
        db.commit()

        # Add Timeline Event
        db.add(TimelineEventModel(
            transaction_id=transaction_id,
            event_type="ANALYST_DECISION",
            title=f"Analyst Decision: {decision.upper()}",
            description=f"Action submitted by {analyst_id}: '{reason}'",
            severity="INFO" if decision.upper() == "APPROVE" else "WARNING",
            timestamp=now,
        ))
        db.commit()

        # Audit log
        AuditService.record_event(
            db=db,
            event_type="ANALYST_DECISION_RECORDED",
            action=decision.upper(),
            entity_type="investigation",
            entity_id=inv.investigation_id,
            actor=analyst_id,
            details={
                "transaction_id": transaction_id,
                "decision": decision.upper(),
                "reason": reason,
                "risk_score": inv.risk_score,
                "model_version": inv.model_version,
                "policy_version": inv.policy_version,
            },
        )

        return {
            "transaction_id": transaction_id,
            "investigation_id": inv.investigation_id,
            "decision": inv.analyst_decision,
            "reason": inv.analyst_reason,
            "timestamp": now.isoformat(),
            "risk_score": inv.risk_score,
            "model_version": inv.model_version,
            "policy_version": inv.policy_version,
            "status": "RESOLVED",
        }
