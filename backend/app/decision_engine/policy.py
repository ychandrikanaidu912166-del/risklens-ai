from typing import Dict, Any, List


class DecisionPolicyEngine:
    """
    Confidence-aware enterprise policy engine.
    Balances fraud risk, evidence strength, confidence calibration, and business loss impact.
    AI recommendations are subject to policy rules; AI never bypasses policy.
    """

    POLICY_VERSION = "v2.5-enterprise"
    UNIT_FP_FRICTION_COST = 250.0  # INR customer friction/support cost
    UNIT_FN_FRAUD_LOSS_BASE = 3500.0  # INR chargeback liability baseline

    @classmethod
    def evaluate_decision(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        risk_score = int(context.get("risk_score", 0))
        risk_level = context.get("risk_level", "LOW")
        ai_investigation = context.get("ai_investigation") or {}
        raw_ai_confidence = float(ai_investigation.get("confidence", 0.85))
        evidence = context.get("evidence", [])
        counter_evidence = context.get("counter_evidence", [])
        tx = context.get("transaction", {})
        amount = float(tx.get("amount", 0.0))
        cust_tx_count = int(tx.get("customer_transaction_count", 0))

        # 1. Determine Evidence Strength
        crit_ev_count = sum(1 for e in evidence if e.get("severity") in ["CRITICAL", "HIGH"])
        total_ev_count = len(evidence)
        counter_count = len(counter_evidence)

        if crit_ev_count >= 2 or total_ev_count >= 4:
            evidence_strength = "CRITICAL" if crit_ev_count >= 3 else "STRONG"
        elif total_ev_count >= 1:
            evidence_strength = "MODERATE"
        else:
            evidence_strength = "LOW" if risk_score < 30 else "INSUFFICIENT"

        # 2. Calibrate Confidence Score
        # Confidence is higher when evidence is strong or normal baseline is established;
        # Confidence is lower when evidence is sparse on high risk or history is shallow.
        confidence = raw_ai_confidence
        if cust_tx_count < 2 and risk_score >= 50:
            confidence = min(confidence, 0.62)  # Low history drops confidence
        elif evidence_strength == "INSUFFICIENT" and risk_score >= 40:
            confidence = min(confidence, 0.55)
        elif counter_count >= 2 and total_ev_count <= 1:
            confidence = max(confidence, 0.88)  # Strong counter evidence reinforces low risk

        confidence = round(float(min(0.99, max(0.40, confidence))), 2)

        # 3. Calculate Business Loss Exposure
        potential_loss = amount
        risk_adjusted_exposure = round(amount * (risk_score / 100.0), 2)
        friction_cost = cls.UNIT_FP_FRICTION_COST

        decision_factors: List[str] = []

        # 4. Policy Decision Rules
        # Core Principle:
        # HIGH RISK + LOW CONFIDENCE -> HUMAN REVIEW
        # HIGH RISK + HIGH CONFIDENCE + STRONG EVIDENCE -> HOLD / BLOCK
        # MEDIUM RISK -> REVIEW / VERIFY
        # LOW RISK + STRONG NORMAL BEHAVIOR -> APPROVE
        if risk_score >= 60 and confidence < 0.70:
            decision = "MANUAL_REVIEW"
            reason = "High risk, but insufficient confidence. Human review required."
            decision_factors.append(f"Risk score is elevated ({risk_score}/100) but confidence is low ({int(confidence*100)}%).")
            decision_factors.append("Preventing automated block due to potential false-positive business impact.")
            cost_rationale = f"Holding automated block saves potential ₹{friction_cost:.0f} friction cost while safeguarding ₹{potential_loss:,.2f} exposure under human oversight."
            automation_allowed = False

        elif evidence_strength == "INSUFFICIENT" and risk_score >= 30:
            decision = "MANUAL_REVIEW"
            reason = "Policy Rule P-01: Insufficient empirical evidence quality requires human analyst review."
            decision_factors.append("Zero confirmed evidence items despite elevated anomalous score.")
            cost_rationale = f"Routing to analyst queue to prevent ungrounded customer friction."
            automation_allowed = False

        elif risk_score >= 85 or risk_level == "CRITICAL":
            is_syndicate = any(e.get("type") in ["SHARED_DEVICE_SYNDICATE", "HIGH_DENSITY_IP_CLUSTER"] for e in evidence)
            if amount >= 50000.0 or is_syndicate:
                decision = "BLOCK"
                reason = "Policy Rule P-CRIT-01: Critical risk (>=85) with multi-account syndicate or high financial exposure."
                decision_factors.append(f"Critical risk score ({risk_score}/100) with strong evidence ({total_ev_count} items).")
                if is_syndicate:
                    decision_factors.append("Multi-accounting infrastructure / device syndicate detected.")
                cost_rationale = f"Immediate hard block intercepts ₹{potential_loss:,.2f} potential chargeback liability."
            else:
                decision = "HOLD"
                reason = "Policy Rule P-CRIT-02: Critical risk score (>=85); hold settlement and request cardholder re-verification."
                decision_factors.append(f"Score {risk_score}/100 warrants immediate holding of funds pending verification.")
                cost_rationale = f"Holding funds protects ₹{potential_loss:,.2f} while allowing legitimate customer recovery."
            automation_allowed = True

        elif risk_score >= 60 or risk_level == "HIGH":
            decision = "MANUAL_REVIEW"
            reason = "Policy Rule P-HIGH-01: High risk threshold (60-84) routed to Senior Analyst review queue."
            decision_factors.append(f"High risk score ({risk_score}/100) backed by {evidence_strength.lower()} evidence.")
            decision_factors.append(f"Risk-adjusted financial exposure is ₹{risk_adjusted_exposure:,.2f}.")
            cost_rationale = f"Analyst review mitigates ₹{risk_adjusted_exposure:,.2f} risk-adjusted loss without automated decline friction."
            automation_allowed = False

        elif risk_score >= 30 or risk_level == "MEDIUM":
            if counter_count >= 2:
                decision = "VERIFY"
                reason = "Policy Rule P-MED-02: Moderate risk mitigated by counter-evidence; step-up 2FA/OTP verification."
                decision_factors.append(f"Score ({risk_score}/100) has {counter_count} legitimate counter-evidence trust markers.")
                cost_rationale = f"Step-up 2FA incurs minimal verification cost while verifying ₹{potential_loss:,.2f} intent."
                automation_allowed = True
            else:
                decision = "MANUAL_REVIEW"
                reason = "Policy Rule P-MED-01: Moderate risk with minimal counter-evidence; queued for analyst check."
                decision_factors.append(f"Moderate risk ({risk_score}/100) with insufficient positive trust markers.")
                cost_rationale = f"Queued for analyst spot-check."
                automation_allowed = False

        else:  # LOW (<30)
            decision = "APPROVE"
            reason = "Policy Rule P-LOW-01: Low risk score (<30); instant automated clearing permitted."
            decision_factors.append(f"Transaction aligns with normal customer behavioral baseline (Score: {risk_score}/100).")
            if counter_count > 0:
                decision_factors.append(f"Confirmed by {counter_count} legitimate trust markers (verified device/tenure).")
            cost_rationale = f"Instant zero-friction clearance optimizes conversion and merchant revenue."
            automation_allowed = True

        business_impact = {
            "transaction_amount": amount,
            "potential_loss_exposure": potential_loss,
            "risk_adjusted_exposure": risk_adjusted_exposure,
            "false_positive_friction_cost": friction_cost,
            "decision_cost_rationale": cost_rationale,
        }

        return {
            "decision": decision,
            "reason": reason,
            "policy_version": cls.POLICY_VERSION,
            "risk_score": risk_score,
            "confidence_score": confidence,
            "confidence": confidence,  # backward compatibility
            "evidence_quality": evidence_strength,
            "evidence_strength": evidence_strength,
            "business_impact": business_impact,
            "decision_factors": decision_factors,
            "automation_allowed": automation_allowed,
        }
