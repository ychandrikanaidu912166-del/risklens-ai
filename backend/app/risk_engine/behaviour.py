from typing import Dict, Any, List, Optional
import numpy as np


class BehaviourEngine:
    """
    Computes customer-specific historical baselines and compares new transactions
    against the customer's own mathematical profile.
    """

    @staticmethod
    def calculate_customer_baseline(customer_transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Derives empirical baseline distributions from customer transaction history.
        """
        if not customer_transactions:
            return {
                "transaction_count": 0,
                "avg_amount": 0.0,
                "median_amount": 0.0,
                "min_amount": 0.0,
                "max_amount": 0.0,
                "p95_amount": 0.0,
                "std_amount": 0.0,
                "known_devices": [],
                "known_ips": [],
                "known_countries": ["IN"],
                "active_hours": list(range(8, 23)),
                "known_merchants": [],
            }

        amounts = [float(tx["amount"]) for tx in customer_transactions]
        devices = list({tx["device_id"] for tx in customer_transactions if tx.get("device_id")})
        ips = list({tx["ip_address"] for tx in customer_transactions if tx.get("ip_address")})
        countries = list({tx["country"] for tx in customer_transactions if tx.get("country")})
        merchants = list({tx["merchant_id"] for tx in customer_transactions if tx.get("merchant_id")})

        hours = []
        for tx in customer_transactions:
            ts = tx.get("timestamp")
            if ts:
                try:
                    # Parse hour from iso string
                    if "T" in str(ts):
                        hours.append(int(str(ts).split("T")[1].split(":")[0]))
                except Exception:
                    pass

        return {
            "transaction_count": len(amounts),
            "avg_amount": round(float(np.mean(amounts)), 2),
            "median_amount": round(float(np.median(amounts)), 2),
            "min_amount": round(float(np.min(amounts)), 2),
            "max_amount": round(float(np.max(amounts)), 2),
            "p95_amount": round(float(np.percentile(amounts, 95)), 2) if len(amounts) >= 5 else round(float(np.max(amounts)), 2),
            "std_amount": round(float(np.std(amounts)), 2) if len(amounts) > 1 else 0.0,
            "known_devices": devices,
            "known_ips": ips,
            "known_countries": countries if countries else ["IN"],
            "active_hours": sorted(list(set(hours))) if hours else list(range(8, 23)),
            "known_merchants": merchants,
        }

    @staticmethod
    def compare_transaction(
        transaction: Dict[str, Any],
        baseline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compares current transaction against customer baseline.
        Generates mathematically grounded anomaly signals.
        """
        amount = float(transaction.get("amount", 0.0))
        device_id = transaction.get("device_id", "")
        country = transaction.get("country", "IN")
        ip_address = transaction.get("ip_address", "")
        
        # Parse hour
        hour = 12
        ts = transaction.get("timestamp", "")
        if "T" in str(ts):
            try:
                hour = int(str(ts).split("T")[1].split(":")[0])
            except Exception:
                hour = 12

        avg_amount = baseline.get("avg_amount", 0.0)
        median_amount = baseline.get("median_amount", 0.0)
        p95_amount = baseline.get("p95_amount", avg_amount * 2.0)
        known_devices = baseline.get("known_devices", [])
        known_countries = baseline.get("known_countries", ["IN"])
        active_hours = baseline.get("active_hours", list(range(8, 23)))

        # 1. Amount comparison
        amount_ratio = round(amount / max(1.0, avg_amount), 2) if avg_amount > 0 else 1.0
        amount_to_median = round(amount / max(1.0, median_amount), 2) if median_amount > 0 else 1.0
        is_amount_anomaly = amount > (p95_amount * 1.5) or amount_ratio >= 3.0

        # 2. Device comparison
        is_device_anomaly = bool(known_devices and device_id not in known_devices)

        # 3. Country comparison
        is_country_anomaly = bool(known_countries and country not in known_countries)

        # 4. Hour comparison
        is_hour_anomaly = bool(active_hours and hour not in active_hours and (hour < 5 or hour > 23))

        # 5. Velocity comparison
        v_10m = int(transaction.get("transactions_last_10m", 0))
        v_1h = int(transaction.get("transactions_last_1h", 0))
        v_24h = int(transaction.get("transactions_last_24h", 0))
        is_velocity_anomaly = v_10m >= 3 or v_1h >= 6

        return {
            "amount_comparison": {
                "current_amount": amount,
                "baseline_avg": avg_amount,
                "baseline_median": median_amount,
                "baseline_p95": p95_amount,
                "amount_ratio": amount_ratio,
                "amount_to_median": amount_to_median,
                "is_anomaly": is_amount_anomaly,
                "summary": f"Current amount INR {amount:,.2f} is {amount_ratio:.2f}x customer average of INR {avg_amount:,.2f}"
            },
            "device_comparison": {
                "current_device": device_id,
                "known_devices": known_devices,
                "is_new_device": is_device_anomaly,
                "summary": "New unrecognized device" if is_device_anomaly else f"Known customer device ({device_id})"
            },
            "country_comparison": {
                "current_country": country,
                "known_countries": known_countries,
                "is_new_country": is_country_anomaly,
                "summary": f"Foreign location {country} not in customer history" if is_country_anomaly else f"Usual country ({country})"
            },
            "hour_comparison": {
                "current_hour": hour,
                "active_hours": active_hours,
                "is_unusual_hour": is_hour_anomaly,
                "summary": f"Unusual off-peak transaction hour ({hour:02d}:00)" if is_hour_anomaly else f"Normal active hour ({hour:02d}:00)"
            },
            "velocity_comparison": {
                "last_10m": v_10m,
                "last_1h": v_1h,
                "last_24h": v_24h,
                "is_anomaly": is_velocity_anomaly,
                "summary": f"High velocity burst ({v_10m} txns in last 10 mins, {v_1h} in 1h)" if is_velocity_anomaly else "Normal velocity"
            }
        }
