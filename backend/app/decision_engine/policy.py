from typing import Dict, Any


class DecisionPolicyEngine:
    """
    Policy enforcement engine. AI recommendations are subject to policy rules;
    AI never bypasses policy.
    """

    POLICY_VERSION = "v2.4-enterprise"

    @classmethod
    def evaluate_decision(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        risk_score = int(context.get("risk_score", 0))
        risk_level = context.get("risk_level", "LOW")
        ai_investigation = context.get("ai_investigation") or {}
        confidence = float(ai_investigation.get("confidence", 0.85))
        evidence = context.get("evidence", [])
        counter_evidence = context.get("counter_evidence", [])
        tx = context.get("transaction", {})
        amount = float(tx.get("amount", 0.0))

        # Assess Evidence Quality
        evidence_quality = "HIGH"
        if len(evidence) == 0 and risk_score >= 30:
            evidence_quality = "INSUFFICIENT"
        elif int(tx.get("customer_transaction_count", 0)) < 2:
            evidence_quality = "MODERATE"

        # Policy Rules
        if evidence_quality == "INSUFFICIENT" or confidence < 0.65:
            decision = "MANUAL_REVIEW"
            reason = "Policy Rule P-01: Insufficient evidence quality or low AI confidence requires human review."
            automation_allowed = False

        elif risk_score >= 85 or risk_level == "CRITICAL":
            # For extremely high value critical transactions, hard block
            if amount >= 50000.0 or any(e.get("type") == "SHARED_DEVICE_SYNDICATE" for e in evidence):
                decision = "BLOCK"
                reason = "Policy Rule P-CRIT-01: Critical risk score (>=85) with multi-account syndicate or high value."
            else:
                decision = "HOLD"
                reason = "Policy Rule P-CRIT-02: Critical risk score (>=85); hold transaction and notify customer."
            automation_allowed = True

        elif risk_score >= 60 or risk_level == "HIGH":
            decision = "MANUAL_REVIEW"
            reason = "Policy Rule P-HIGH-01: High risk threshold (60-84) routed to Senior Analyst review queue."
            automation_allowed = False

        elif risk_score >= 30 or risk_level == "MEDIUM":
            if len(counter_evidence) >= 2:
                decision = "VERIFY"
                reason = "Policy Rule P-MED-02: Moderate risk mitigated by counter-evidence; step-up 2FA/OTP verification."
                automation_allowed = True
            else:
                decision = "MANUAL_REVIEW"
                reason = "Policy Rule P-MED-01: Moderate risk with minimal counter-evidence; queued for analyst check."
                automation_allowed = False

        else: # LOW
            decision = "APPROVE"
            reason = "Policy Rule P-LOW-01: Low risk score (<30); instant automated clearing permitted."
            automation_allowed = True

        return {
            "decision": decision,
            "reason": reason,
            "policy_version": cls.POLICY_VERSION,
            "risk_score": risk_score,
            "confidence": confidence,
            "evidence_quality": evidence_quality,
            "automation_allowed": automation_allowed,
        }
