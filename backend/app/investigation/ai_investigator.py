import json
import logging
from typing import Dict, Any, List
from backend.app.config.settings import settings
from backend.app.schemas.investigation import AIAssessment

logger = logging.getLogger("risklens.investigator")


class AIInvestigator:
    """
    AI-powered investigation synthesizer.
    Analyzes structured evidence, entity signals, and customer baselines
    to deliver an objective, calibrated narrative for human risk analysts.
    """

    @classmethod
    def investigate(cls, context: Dict[str, Any]) -> AIAssessment:
        """
        Dispatches to Gemini LLM if API key is present; otherwise executes
        the deterministic local rule-grounded fallback.
        """
        api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""

        if api_key:
            try:
                return cls._call_gemini_llm(context, api_key)
            except Exception as e:
                logger.warning(f"Gemini LLM call failed ({str(e)}), falling back to deterministic local investigator.")

        return cls._run_deterministic_investigator(context)

    @classmethod
    def _call_gemini_llm(cls, context: Dict[str, Any], api_key: str) -> AIAssessment:
        """
        Calls Google Gemini using the structured JSON response format.
        Strictly grounds all inferences in the supplied evidence payload.
        """
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        system_instruction = (
            "You are a Senior Risk Analyst assistant at RiskLens AI. "
            "You evaluate payment risk solely based on the structured evidence, behavioural baselines, "
            "and entity graphs provided to you. "
            "STRICT RULES:\n"
            "1. You are NOT the classifier; the quantitative risk score is provided.\n"
            "2. Never invent evidence or extrapolate facts not in the prompt.\n"
            "3. Use calibrated, probabilistic language (e.g. 'strongly indicates', 'consistent with'). Never say 'definitely fraud'.\n"
            "4. Always present both suspicious evidence and counter-evidence.\n"
            "5. Output valid JSON adhering to the required schema."
        )

        prompt = (
            f"{system_instruction}\n\n"
            f"EVIDENCE CONTEXT:\n{json.dumps(context, indent=2)}\n\n"
            "Provide your structured risk assessment as a JSON object with keys: "
            "assessment, risk_level, confidence, primary_evidence, supporting_evidence, "
            "counter_evidence, uncertainties, recommended_action, reasoning_summary."
        )

        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        data = json.loads(response.text)
        return AIAssessment(
            assessment=data.get("assessment", "Investigation completed based on system evidence."),
            risk_level=data.get("risk_level", context.get("risk_level", "MEDIUM")),
            confidence=float(data.get("confidence", 0.85)),
            primary_evidence=data.get("primary_evidence", []),
            supporting_evidence=data.get("supporting_evidence", []),
            counter_evidence=data.get("counter_evidence", []),
            uncertainties=data.get("uncertainties", []),
            recommended_action=data.get("recommended_action", "MANUAL_REVIEW"),
            reasoning_summary=data.get("reasoning_summary", ""),
            is_deterministic_fallback=False,
            provider="gemini-1.5-flash",
        )

    @classmethod
    def _run_deterministic_investigator(cls, context: Dict[str, Any]) -> AIAssessment:
        """
        Deterministic, transparent local investigation engine.
        Synthesizes facts directly from structured evidence without hallucination.
        Explicitly flagged as deterministic fallback.
        """
        tx = context.get("transaction", {})
        risk_score = context.get("risk_score", 0)
        risk_level = context.get("risk_level", "LOW")
        evidence = context.get("evidence", [])
        counter_evidence = context.get("counter_evidence", [])
        behaviour = context.get("customer_behaviour", {})

        amt_comp = behaviour.get("amount_comparison", {})
        ratio = amt_comp.get("amount_ratio", 1.0)
        cur_amt = tx.get("amount", 0.0)
        cust_id = tx.get("customer_id", "Unknown")

        primary_ev = []
        supporting_ev = []
        counter_ev = []
        uncertainties = []

        # Extract primary and supporting evidence from verified items
        for ev in evidence:
            ev_desc = ev.get("description", "")
            ev_sev = ev.get("severity", "MEDIUM")
            if ev_sev in ["CRITICAL", "HIGH"] and len(primary_ev) < 3:
                primary_ev.append(f"[{ev.get('type')}] {ev_desc}")
            else:
                supporting_ev.append(f"[{ev.get('type')}] {ev_desc}")

        # Extract counter-evidence
        for cev in counter_evidence:
            counter_ev.append(f"[{cev.get('type')}] {cev.get('description', '')}")

        # Note any missing information or uncertainties
        if int(tx.get("customer_transaction_count", 0)) < 3:
            uncertainties.append("Limited historical customer baselines (fewer than 3 recorded transactions).")
        if not counter_evidence:
            uncertainties.append("No positive trust markers or prior verified hardware matches available.")

        # Determine calibrated action
        if risk_score >= 85:
            recommended_action = "BLOCK"
            assessment = (
                f"High-confidence compromise detected for customer {cust_id}. "
                f"Severe behavioral divergence ({ratio:.1f}x baseline) combined with multi-factor risk signals."
            )
            confidence = 0.94
        elif risk_score >= 60:
            recommended_action = "HOLD"
            assessment = (
                f"Elevated risk signals on transaction {tx.get('transaction_id')}. "
                f"Discrepancies identified in amount or device context warranting analyst verification."
            )
            confidence = 0.86
        elif risk_score >= 30:
            recommended_action = "MANUAL_REVIEW"
            assessment = (
                f"Moderate risk observed. While primary spend deviates moderately from baseline, "
                f"counter-evidence suggests possible legitimate discretionary activity."
            )
            confidence = 0.76
        else:
            recommended_action = "APPROVE"
            assessment = (
                f"Low-risk transaction. Spend pattern, device identity, and velocity align "
                f"closely with customer historical profile."
            )
            confidence = 0.95

        reasoning = (
            f"The quantitative risk fusion engine evaluated this transaction at a score of {risk_score}/100 ({risk_level}). "
            f"The primary driver is {primary_ev[0] if primary_ev else 'within expected parameters'}. "
            f"We recorded {len(primary_ev) + len(supporting_ev)} risk signals against {len(counter_ev)} counter-evidence trust indicators. "
            f"Recommended policy action is {recommended_action}."
        )

        return AIAssessment(
            assessment=assessment,
            risk_level=risk_level,
            confidence=round(confidence, 2),
            primary_evidence=primary_ev if primary_ev else ["No critical risk deviations detected"],
            supporting_evidence=supporting_ev,
            counter_evidence=counter_ev if counter_ev else ["No counter-evidence indicators found"],
            uncertainties=uncertainties if uncertainties else ["Sufficient historical baseline data present"],
            recommended_action=recommended_action,
            reasoning_summary=reasoning,
            is_deterministic_fallback=True,
            provider="local_deterministic_engine",
        )
