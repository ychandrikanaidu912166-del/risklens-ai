from typing import List, Dict, Any, Tuple
import math


class RiskFusionEngine:
    """
    Fuses supervised ML signals, customer behavioural deviations, velocity spikes,
    and entity correlations into an explainable 0-100 composite risk score.
    Exposes independent component risk signals for model agreement intelligence.
    """

    @staticmethod
    def fuse_signals(
        ml_prob: float,
        behaviour_diff: Dict[str, Any],
        evidence_list: List[Dict[str, Any]],
        counter_evidence_list: List[Dict[str, Any]],
        entity_signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        factors = []
        raw_score = 0.0

        # Helper to find evidence_id by type
        def get_ev_id(ev_type: str) -> str:
            for ev in evidence_list:
                if ev.get("type") == ev_type:
                    return ev.get("evidence_id", "")
            return ""

        # 1. Supervised ML Fraud Probability (Max 35 points)
        ml_contrib = round(ml_prob * 35.0, 1)
        if ml_contrib > 0:
            factors.append({
                "name": "Machine Learning Model Probability",
                "category": "ML_CLASSIFIER",
                "contribution": ml_contrib,
                "evidence_id": get_ev_id("ML_HIGH_RISK"),
                "detail": f"Supervised XGBoost fraud model estimated probability: {ml_prob * 100:.1f}%",
            })
            raw_score += ml_contrib

        # 2. Amount Anomaly (Max 25 points)
        amt_comp = behaviour_diff.get("amount_comparison", {})
        ratio = amt_comp.get("amount_ratio", 1.0)
        amt_contrib = 0.0
        if ratio >= 5.0:
            amt_contrib = 25.0
        elif ratio >= 3.0:
            amt_contrib = 18.0
        elif ratio >= 2.0:
            amt_contrib = 10.0
        elif ratio >= 1.5:
            amt_contrib = 5.0

        if amt_contrib > 0:
            factors.append({
                "name": "Spend Amount Anomaly",
                "category": "BEHAVIOURAL",
                "contribution": amt_contrib,
                "evidence_id": get_ev_id("AMOUNT_ANOMALY"),
                "detail": f"Amount is {ratio:.2f}x above customer historical average",
            })
            raw_score += amt_contrib

        # 3. Velocity Spike (Max 15 points)
        vel_comp = behaviour_diff.get("velocity_comparison", {})
        v_10m = vel_comp.get("last_10m", 0)
        v_1h = vel_comp.get("last_1h", 0)
        vel_contrib = 0.0
        if v_10m >= 4:
            vel_contrib = 15.0
        elif v_10m >= 2 or v_1h >= 6:
            vel_contrib = 10.0
        elif v_1h >= 3:
            vel_contrib = 5.0

        if vel_contrib > 0:
            factors.append({
                "name": "Velocity Burst Pattern",
                "category": "VELOCITY",
                "contribution": vel_contrib,
                "evidence_id": get_ev_id("HIGH_VELOCITY"),
                "detail": f"{v_10m} payment attempts in last 10m ({v_1h} in last hour)",
            })
            raw_score += vel_contrib

        # 4. Device Novelty (Max 10 points)
        dev_comp = behaviour_diff.get("device_comparison", {})
        if dev_comp.get("is_new_device"):
            factors.append({
                "name": "Unrecognized Device Hardware",
                "category": "DEVICE",
                "contribution": 10.0,
                "evidence_id": get_ev_id("NEW_DEVICE"),
                "detail": "Transaction initiated from hardware not previously seen on this account",
            })
            raw_score += 10.0

        # 5. Geolocation / Country Discrepancy (Max 15 points)
        country_comp = behaviour_diff.get("country_comparison", {})
        if country_comp.get("is_new_country"):
            factors.append({
                "name": "Geographic Discrepancy (New Country)",
                "category": "GEOGRAPHIC",
                "contribution": 15.0,
                "evidence_id": get_ev_id("NEW_COUNTRY"),
                "detail": f"Transaction from foreign jurisdiction {country_comp.get('current_country')}",
            })
            raw_score += 15.0

        # 6. Unusual Operating Hour (Max 5 points)
        hour_comp = behaviour_diff.get("hour_comparison", {})
        if hour_comp.get("is_unusual_hour"):
            factors.append({
                "name": "Off-Peak Hour Execution",
                "category": "TEMPORAL",
                "contribution": 5.0,
                "evidence_id": get_ev_id("UNUSUAL_HOUR"),
                "detail": f"Transaction executed at unusual off-peak hour {hour_comp.get('current_hour', 0):02d}:00",
            })
            raw_score += 5.0

        # 7. Entity Graph Correlation (Max 15 points)
        for sig in entity_signals:
            ent_contrib = 15.0 if sig.get("severity") == "CRITICAL" else 10.0
            factors.append({
                "name": "Entity Syndicate Connection",
                "category": "ENTITY_GRAPH",
                "contribution": ent_contrib,
                "evidence_id": get_ev_id(sig.get("type", "ENTITY_CONNECTION")),
                "detail": sig.get("description", "Cross-entity multi-account link"),
            })
            raw_score += ent_contrib

        # 8. Counter-Evidence Mitigation (Discount up to -20 points)
        mitigation = 0.0
        if len(counter_evidence_list) >= 3 and raw_score < 70:
            mitigation = min(20.0, len(counter_evidence_list) * 5.0)
            if mitigation > 0:
                factors.append({
                    "name": "Counter-Evidence Trust Discount",
                    "category": "MITIGATION",
                    "contribution": -mitigation,
                    "evidence_id": "",
                    "detail": f"Reduced risk due to {len(counter_evidence_list)} legitimate trust markers (verified device, tenure)",
                })
                raw_score = max(0.0, raw_score - mitigation)

        final_score = int(round(min(100.0, max(0.0, raw_score))))

        # Calibrate Risk Level
        if final_score >= 85:
            risk_level = "CRITICAL"
        elif final_score >= 60:
            risk_level = "HIGH"
        elif final_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # 9. Compute Independent Component Signals for Model Agreement Intelligence
        ml_signal = int(round(min(100.0, ml_prob * 100.0)))

        # Anomaly risk: based on amount divergence and velocity
        raw_anomaly = min(100.0, (ratio / 4.0) * 70.0 + (v_10m * 10.0))
        anomaly_signal = int(round(max(5.0, raw_anomaly)))

        # Behavioral risk: based on device, country, and hour deviations
        beh_pts = 0
        if dev_comp.get("is_new_device"): beh_pts += 45
        if country_comp.get("is_new_country"): beh_pts += 45
        if hour_comp.get("is_unusual_hour"): beh_pts += 20
        behavior_signal = int(min(100, max(8, beh_pts)))

        # Entity risk: based on shared infrastructure
        if any(s.get("severity") == "CRITICAL" for s in entity_signals):
            entity_signal = 92
        elif len(entity_signals) > 0:
            entity_signal = 75
        else:
            entity_signal = 12

        # Evidence Strength
        crit_ev = sum(1 for e in evidence_list if e.get("severity") in ["CRITICAL", "HIGH"])
        if crit_ev >= 2 or len(evidence_list) >= 4:
            ev_strength = "CRITICAL" if crit_ev >= 3 else "STRONG"
        elif len(evidence_list) >= 1:
            ev_strength = "MODERATE"
        else:
            ev_strength = "LOW"

        # Signal Agreement Assessment
        signals = [ml_signal, anomaly_signal, behavior_signal, entity_signal]
        spread = max(signals) - min(signals)
        if spread <= 25 and final_score >= 60:
            signal_agreement = "CONVERGENT_HIGH"
            agreement_desc = "Strong consensus across ML, anomaly, and behavioral detectors."
        elif spread <= 25 and final_score < 40:
            signal_agreement = "CONVERGENT_LOW"
            agreement_desc = "All engines agree transaction matches established baseline."
        else:
            signal_agreement = "DIVERGENT"
            agreement_desc = "Signals diverge across models; review contributing factors."

        signals_breakdown = {
            "ml_risk": ml_signal,
            "anomaly_risk": anomaly_signal,
            "behavior_risk": behavior_signal,
            "entity_risk": entity_signal,
            "final_fused_risk": final_score,
            "evidence_strength": ev_strength,
            "signal_agreement": signal_agreement,
            "agreement_description": agreement_desc,
        }

        return {
            "risk_score": final_score,
            "risk_level": risk_level,
            "raw_score": round(raw_score, 1),
            "factors": factors,
            "signals_breakdown": signals_breakdown,
            "summary": f"Calculated {risk_level} risk score of {final_score}/100 across {len(factors)} explainable signals.",
        }
