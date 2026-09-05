import uuid
from typing import List, Dict, Any


class CounterEvidenceEngine:
    """
    Identifies legitimate, risk-reducing signals and customer tenure indicators
    that counter-balance risk factors. Prevents false positive over-flagging.
    """

    @staticmethod
    def generate_counter_evidence(
        transaction: Dict[str, Any],
        baseline: Dict[str, Any],
        behaviour_diff: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        counter_evidence = []
        txn_id = transaction.get("transaction_id", "")
        cust_id = transaction.get("customer_id", "")
        dev_id = transaction.get("device_id", "")
        country = transaction.get("country", "IN")
        amount = float(transaction.get("amount", 0.0))
        ts = transaction.get("timestamp", "")

        known_devices = baseline.get("known_devices", [])
        known_countries = baseline.get("known_countries", ["IN"])
        tx_count = baseline.get("transaction_count", 0)
        account_age = int(transaction.get("customer_age_days", 0))

        # 1. Known Device Match
        if dev_id and dev_id in known_devices:
            counter_evidence.append({
                "id": f"cev_dev_{uuid.uuid4().hex[:8]}",
                "type": "KNOWN_DEVICE",
                "title": "Hardware Fingerprint Verified",
                "description": f"Transaction originated from verified customer device '{dev_id}', previously associated with {tx_count} historical transactions.",
                "confidence_impact": -15,
                "timestamp": ts,
            })

        # 2. Known Country / Geographic Consistency
        if country in known_countries:
            counter_evidence.append({
                "id": f"cev_geo_{uuid.uuid4().hex[:8]}",
                "type": "KNOWN_COUNTRY",
                "title": "Domestic / Usual Geolocation",
                "description": f"Payment location '{country}' matches the customer's primary registered country profile.",
                "confidence_impact": -10,
                "timestamp": ts,
            })

        # 3. Normal Amount Profile
        amt_comp = behaviour_diff.get("amount_comparison", {})
        if not amt_comp.get("is_anomaly") and amt_comp.get("amount_ratio", 1.0) < 2.0:
            counter_evidence.append({
                "id": f"cev_amt_{uuid.uuid4().hex[:8]}",
                "type": "NORMAL_AMOUNT",
                "title": "Amount Aligns With Normal Spend Profile",
                "description": f"Transaction amount of INR {amount:,.2f} is within customer's normal interquartile spend baseline.",
                "confidence_impact": -12,
                "timestamp": ts,
            })

        # 4. Established Customer Account Tenure
        if account_age >= 90 and tx_count >= 10:
            counter_evidence.append({
                "id": f"cev_tenure_{uuid.uuid4().hex[:8]}",
                "type": "ESTABLISHED_ACCOUNT",
                "title": "Established Account Relationship",
                "description": f"Customer account has been active for {account_age} days with {tx_count} completed transactions without fraud chargebacks.",
                "confidence_impact": -14,
                "timestamp": ts,
            })

        # 5. Normal Transaction Operating Hour
        hour_comp = behaviour_diff.get("hour_comparison", {})
        if not hour_comp.get("is_unusual_hour"):
            cur_hour = hour_comp.get("current_hour", 12)
            counter_evidence.append({
                "id": f"cev_hour_{uuid.uuid4().hex[:8]}",
                "type": "NORMAL_HOUR",
                "title": "Daytime Operating Hours",
                "description": f"Transaction executed at {cur_hour:02d}:00 hours, consistent with normal daytime commercial activity.",
                "confidence_impact": -5,
                "timestamp": ts,
            })

        # 6. Low Velocity History
        v_10m = int(transaction.get("transactions_last_10m", 0))
        if v_10m <= 1:
            counter_evidence.append({
                "id": f"cev_vel_{uuid.uuid4().hex[:8]}",
                "type": "NORMAL_VELOCITY",
                "title": "Calm Velocity Rhythm",
                "description": "No rapid repeated payment attempts detected on this account or device.",
                "confidence_impact": -5,
                "timestamp": ts,
            })

        return counter_evidence
