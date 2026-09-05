import uuid
from typing import List, Dict, Any


class EvidenceEngine:
    """
    Generates deterministic, structured evidence items for every detected risk signal.
    Answers: 'WHY is this transaction risky?'
    """

    @staticmethod
    def generate_evidence(
        transaction: Dict[str, Any],
        behaviour_diff: Dict[str, Any],
        ml_prob: float,
        entity_signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        evidence_list = []
        txn_id = transaction.get("transaction_id", "")
        cust_id = transaction.get("customer_id", "")
        dev_id = transaction.get("device_id", "")
        ip_addr = transaction.get("ip_address", "")
        merch_id = transaction.get("merchant_id", "")
        ts = transaction.get("timestamp", "")

        # 1. Amount Anomaly Evidence
        amt_comp = behaviour_diff.get("amount_comparison", {})
        if amt_comp.get("is_anomaly") or amt_comp.get("amount_ratio", 1.0) >= 2.5:
            ratio = amt_comp.get("amount_ratio", 1.0)
            cur_amt = amt_comp.get("current_amount", 0.0)
            base_avg = amt_comp.get("baseline_avg", 0.0)
            evidence_list.append({
                "evidence_id": f"ev_amt_{uuid.uuid4().hex[:8]}",
                "type": "AMOUNT_ANOMALY",
                "source": "BEHAVIOURAL_ENGINE",
                "description": f"Transaction amount of INR {cur_amt:,.2f} is {ratio:.2f}x higher than customer baseline average of INR {base_avg:,.2f}.",
                "severity": "CRITICAL" if ratio >= 5.0 else ("HIGH" if ratio >= 3.0 else "MEDIUM"),
                "observed_value": f"INR {cur_amt:,.2f} ({ratio:.2f}x)",
                "baseline_value": f"INR {base_avg:,.2f} (median: INR {amt_comp.get('baseline_median', 0.0):,.2f})",
                "timestamp": ts,
                "related_entity_ids": [txn_id, cust_id],
            })

        # 2. Velocity Spike Evidence
        vel_comp = behaviour_diff.get("velocity_comparison", {})
        if vel_comp.get("is_anomaly"):
            v_10m = vel_comp.get("last_10m", 0)
            v_1h = vel_comp.get("last_1h", 0)
            evidence_list.append({
                "evidence_id": f"ev_vel_{uuid.uuid4().hex[:8]}",
                "type": "HIGH_VELOCITY",
                "source": "VELOCITY_ENGINE",
                "description": f"Unusual burst velocity detected: {v_10m} payment attempts in last 10 minutes ({v_1h} in last hour).",
                "severity": "CRITICAL" if v_10m >= 4 else "HIGH",
                "observed_value": f"{v_10m} txns / 10m, {v_1h} txns / 1h",
                "baseline_value": "0 - 1 txns / 10m",
                "timestamp": ts,
                "related_entity_ids": [txn_id, cust_id, dev_id],
            })

        # 3. New Device Evidence
        dev_comp = behaviour_diff.get("device_comparison", {})
        if dev_comp.get("is_new_device") or int(transaction.get("is_new_device", 0)) == 1:
            evidence_list.append({
                "evidence_id": f"ev_dev_{uuid.uuid4().hex[:8]}",
                "type": "NEW_DEVICE",
                "source": "ENTITY_INTELLIGENCE",
                "description": f"Transaction initiated from an unrecognized device hardware identifier ({dev_id}).",
                "severity": "MEDIUM",
                "observed_value": dev_id,
                "baseline_value": str(dev_comp.get("known_devices", ["None registered"])),
                "timestamp": ts,
                "related_entity_ids": [txn_id, cust_id, dev_id],
            })

        # 4. New Country / Impossible Travel
        country_comp = behaviour_diff.get("country_comparison", {})
        if country_comp.get("is_new_country") or int(transaction.get("is_new_country", 0)) == 1:
            cur_country = country_comp.get("current_country", transaction.get("country", "Unknown"))
            evidence_list.append({
                "evidence_id": f"ev_geo_{uuid.uuid4().hex[:8]}",
                "type": "NEW_COUNTRY",
                "source": "GEOLOCATION_ENGINE",
                "description": f"Geographic discrepancy: transaction initiated from {cur_country} while customer history is centered in {country_comp.get('known_countries', ['IN'])}.",
                "severity": "HIGH",
                "observed_value": cur_country,
                "baseline_value": str(country_comp.get("known_countries", ["IN"])),
                "timestamp": ts,
                "related_entity_ids": [txn_id, cust_id, ip_addr],
            })

        # 5. Unusual Off-Peak Hour
        hour_comp = behaviour_diff.get("hour_comparison", {})
        if hour_comp.get("is_unusual_hour") or int(transaction.get("is_unusual_hour", 0)) == 1:
            cur_hour = hour_comp.get("current_hour", 12)
            evidence_list.append({
                "evidence_id": f"ev_time_{uuid.uuid4().hex[:8]}",
                "type": "UNUSUAL_HOUR",
                "source": "TEMPORAL_ENGINE",
                "description": f"Transaction executed at {cur_hour:02d}:00 hours, outside customer's standard active profile window.",
                "severity": "LOW",
                "observed_value": f"{cur_hour:02d}:00 UTC/IST",
                "baseline_value": "08:00 - 23:00",
                "timestamp": ts,
                "related_entity_ids": [txn_id, cust_id],
            })

        # 6. Entity Graph Ring / Shared Infrastructure Evidence
        for sig in entity_signals:
            evidence_list.append({
                "evidence_id": f"ev_ent_{uuid.uuid4().hex[:8]}",
                "type": sig.get("type", "ENTITY_CONNECTION"),
                "source": "ENTITY_GRAPH",
                "description": sig.get("description", "Cross-entity correlation identified."),
                "severity": sig.get("severity", "HIGH"),
                "observed_value": sig.get("observed_value", ""),
                "baseline_value": sig.get("baseline_value", "Single dedicated account per device/IP"),
                "timestamp": ts,
                "related_entity_ids": sig.get("related_entities", [txn_id]),
            })

        # 7. Supervised ML High-Risk Output
        if ml_prob >= 0.70:
            evidence_list.append({
                "evidence_id": f"ev_ml_{uuid.uuid4().hex[:8]}",
                "type": "ML_HIGH_RISK",
                "source": "ML_MODEL",
                "description": f"Supervised XGBoost fraud model estimated high fraud probability of {ml_prob * 100:.1f}%.",
                "severity": "CRITICAL" if ml_prob >= 0.90 else "HIGH",
                "observed_value": f"{ml_prob * 100:.1f}% probability",
                "baseline_value": "< 15.0% normal range",
                "timestamp": ts,
                "related_entity_ids": [txn_id],
            })

        return evidence_list
