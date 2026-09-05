import json
import logging
from typing import Dict, Any, List
from backend.app.config.settings import settings
from backend.app.schemas.investigation import AIAssessment

logger = logging.getLogger("risklens.investigator")


class AIInvestigator:
    """
    AI-powered investigation synthesizer.
    Produces a 10-point structured investigation narrative strictly grounded
    in empirical system evidence, behavioral profiles, and entity correlations.
    """

    @classmethod
    def investigate(cls, context: Dict[str, Any]) -> AIAssessment:
        api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""

        if api_key:
            try:
                return cls._call_gemini_llm(context, api_key)
            except Exception as e:
                logger.warning(f"Gemini LLM call failed ({str(e)}), falling back to deterministic local investigator.")

        return cls._run_deterministic_investigator(context)

    @classmethod
    def _call_gemini_llm(cls, context: Dict[str, Any], api_key: str) -> AIAssessment:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        system_instruction = (
            "You are a Senior Risk Analyst assistant at RiskLens AI. "
            "You evaluate payment risk solely based on the structured evidence, behavioural baselines, "
            "and entity graphs provided to you. "
            "STRICT RULES:\n"
            "1. You are NOT the classifier; the quantitative risk score is provided.\n"
            "2. Never invent evidence, historical metrics, or extrapolate facts not in the prompt.\n"
            "3. Use calibrated, probabilistic language. Never say 'definitely fraud'.\n"
            "4. Always present both suspicious evidence and counter-evidence.\n"
            "5. Output valid JSON adhering to the 10-point schema."
        )

        prompt = (
            f"{system_instruction}\n\n"
            f"EVIDENCE CONTEXT:\n{json.dumps(context, indent=2)}\n\n"
            "Provide your structured risk assessment as a JSON object with keys: "
            "executive_summary, risk_assessment, strongest_evidence, counter_evidence, "
            "behavioral_assessment, entity_network_assessment, business_impact, confidence, "
            "recommended_action, what_would_change_recommendation."
        )

        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        data = json.loads(response.text)
        risk_level = context.get("risk_level", "LOW")

        return AIAssessment(
            executive_summary=data.get("executive_summary", "Case analysis synthesized from system evidence."),
            risk_assessment=data.get("risk_assessment", f"Risk assessed at {risk_level}."),
            strongest_evidence=data.get("strongest_evidence", []),
            counter_evidence=data.get("counter_evidence", []),
            behavioral_assessment=data.get("behavioral_assessment", "Behavioral deviations noted."),
            entity_network_assessment=data.get("entity_network_assessment", "Infrastructure examined."),
            business_impact=data.get("business_impact", {}),
            confidence=float(data.get("confidence", 0.85)),
            recommended_action=data.get("recommended_action", "MANUAL_REVIEW"),
            what_would_change_recommendation=data.get("what_would_change_recommendation", []),
            # Backward-compatible fields
            assessment=data.get("executive_summary", "Case analysis completed."),
            risk_level=risk_level,
            primary_evidence=data.get("strongest_evidence", []),
            supporting_evidence=data.get("strongest_evidence", [])[2:],
            uncertainties=[],
            reasoning_summary=data.get("risk_assessment", ""),
            is_deterministic_fallback=False,
            provider="gemini-1.5-flash",
        )

    @classmethod
    def _run_deterministic_investigator(cls, context: Dict[str, Any]) -> AIAssessment:
        """
        Deterministic local investigation engine.
        Synthesizes the exact 10-point case narrative from structured system facts.
        """
        tx = context.get("transaction", {})
        risk_score = context.get("risk_score", 0)
        risk_level = context.get("risk_level", "LOW")
        evidence = context.get("evidence", [])
        counter_evidence = context.get("counter_evidence", [])
        behaviour = context.get("customer_behaviour", {})
        entities = context.get("entities", {})
        amount = float(tx.get("amount", 0.0))
        cust_id = tx.get("customer_id", "Unknown")
        dev_id = tx.get("device_id", "Unknown")

        amt_comp = behaviour.get("amount_comparison", {})
        ratio = amt_comp.get("amount_ratio", 1.0)
        base_avg = amt_comp.get("baseline_avg", 0.0)

        # 1. Strongest Evidence
        strongest_ev = []
        for ev in evidence:
            ev_desc = ev.get("description", "")
            strongest_ev.append(f"[{ev.get('type')}] {ev_desc}")

        # 2. Counter-Evidence
        counter_ev = []
        for cev in counter_evidence:
            counter_ev.append(f"[{cev.get('type')}] {cev.get('description', '')}")

        # 3. Behavioral Assessment
        if amt_comp.get("is_anomaly") or ratio >= 2.5:
            beh_narrative = (
                f"Severe spend divergence: Requested transaction of INR {amount:,.2f} is {ratio:.2f}x "
                f"above customer {cust_id}'s established average of INR {base_avg:,.2f}. "
                f"Velocity in past 10 minutes is {tx.get('transactions_last_10m', 0)} attempts."
            )
        else:
            beh_narrative = (
                f"Transaction spend of INR {amount:,.2f} aligns closely with customer baseline "
                f"(average INR {base_avg:,.2f}, ratio {ratio:.2f}x)."
            )

        # 4. Entity / Network Assessment
        syndicate_nodes = [n for n in entities.get("nodes", []) if n.get("risk") == "suspicious"]
        if syndicate_nodes:
            entity_narrative = (
                f"High-risk infrastructure sharing identified: Device {dev_id} is correlated with "
                f"{len(syndicate_nodes)} additional suspicious customer accounts in the entity graph."
            )
        else:
            entity_narrative = (
                f"No multi-accounting hardware syndicates detected for device {dev_id}. "
                f"Device appears isolated to customer {cust_id}."
            )

        # 5. Business Impact
        risk_adjusted = round(amount * (risk_score / 100.0), 2)
        bus_impact = {
            "gross_transaction_amount": amount,
            "potential_chargeback_loss": amount,
            "risk_adjusted_exposure": risk_adjusted,
            "friction_cost_estimate": 250.0,
            "loss_containment_status": "CRITICAL" if risk_score >= 85 else ("ELEVATED" if risk_score >= 60 else "NORMAL"),
        }

        # 6. Confidence & Recommendations
        change_triggers = []
        if risk_score >= 85:
            rec_action = "BLOCK"
            confidence = 0.94
            exec_summary = (
                f"High-probability compromised transaction ({risk_score}/100) on customer account {cust_id}. "
                f"Critical spend divergence ({ratio:.1f}x) combined with multi-factor risk signals."
            )
            risk_assessment = (
                f"Severe risk of fraudulent chargeback. The combination of hardware/geo anomalies and "
                f"elevated ML probability ({context.get('ml_output', {}).get('fraud_probability', 0)*100:.1f}%) "
                f"warrants immediate merchant loss containment."
            )
            change_triggers.append("Direct cardholder confirmation via registered phone OTP would downgrade action to HOLD.")
            change_triggers.append("Verified hardware match upon re-authentication would reduce severity.")

        elif risk_score >= 60:
            rec_action = "HOLD"
            confidence = 0.86
            exec_summary = (
                f"Elevated risk transaction ({risk_score}/100). Significant deviations detected from customer baseline "
                f"requiring human analyst verification."
            )
            risk_assessment = (
                f"High risk score reflects anomalous velocity or geographic discrepancy. Financial exposure is INR {amount:,.2f}."
            )
            change_triggers.append("Successful step-up 3DS challenge would permit automated APPROVE.")
            change_triggers.append("Discovery of prior transactions on this hardware would lower risk score by 15 points.")

        elif risk_score >= 30:
            rec_action = "MANUAL_REVIEW"
            confidence = 0.76
            exec_summary = (
                f"Moderate risk transaction ({risk_score}/100). Spend deviates moderately, but "
                f"{len(counter_evidence)} legitimate trust markers suggest possible benign discretionary spend."
            )
            risk_assessment = (
                "Borderline risk profile. Neither strong malicious syndicates nor perfect baseline alignment detected."
            )
            change_triggers.append("Additional failed payment attempts within 1 hour would trigger escalation to HOLD.")
            change_triggers.append("Customer confirmation of travel booking would allow immediate APPROVE.")

        else:
            rec_action = "APPROVE"
            confidence = 0.95
            exec_summary = (
                f"Low-risk routine payment ({risk_score}/100). Parameters align with customer historical baseline."
            )
            risk_assessment = "Minimal financial risk. Instant zero-friction clearing recommended."
            change_triggers.append("Subsequent velocity burst (>3 attempts in 10 mins) would reopen investigation.")

        return AIAssessment(
            executive_summary=exec_summary,
            risk_assessment=risk_assessment,
            strongest_evidence=strongest_ev if strongest_ev else ["No critical risk deviations detected"],
            counter_evidence=counter_ev if counter_ev else ["No positive counter-evidence trust markers found"],
            behavioral_assessment=beh_narrative,
            entity_network_assessment=entity_narrative,
            business_impact=bus_impact,
            confidence=confidence,
            recommended_action=rec_action,
            what_would_change_recommendation=change_triggers,
            # Backward-compatible fields
            assessment=exec_summary,
            risk_level=risk_level,
            primary_evidence=strongest_ev if strongest_ev else ["No critical risk deviations detected"],
            supporting_evidence=strongest_ev[2:] if len(strongest_ev) > 2 else [],
            uncertainties=["Limited historical customer profile" if int(tx.get("customer_transaction_count", 0)) < 3 else "Empirical baseline verified"],
            reasoning_summary=f"{risk_assessment} Recommended action is {rec_action}.",
            is_deterministic_fallback=True,
            provider="local_deterministic_engine",
        )
