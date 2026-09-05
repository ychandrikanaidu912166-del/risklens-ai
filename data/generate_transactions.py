import random
import string
import json
import datetime
from typing import List, Dict, Any
import numpy as np
import pandas as pd


def generate_synthetic_transactions(
    num_customers: int = 200,
    num_merchants: int = 30,
    num_transactions: int = 6000,
    fraud_rate: float = 0.05,
    random_seed: int = 42,
) -> pd.DataFrame:
    """
    Generates a realistic, reproducible dataset of payment transactions with
    behavioural baselines, entity graphs, temporal trends, and subtle fraud patterns.
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    # 1. Establish Merchants
    merchant_categories = {
        "merch_ecom": ("E-Commerce", 500, 15000),
        "merch_elec": ("Electronics & Gadgets", 2000, 120000),
        "merch_food": ("Food & Dining", 150, 2500),
        "merch_trav": ("Travel & Airlines", 3000, 85000),
        "merch_util": ("Utilities & Recharges", 100, 3000),
        "merch_lux": ("Luxury & Jewelry", 10000, 350000),
        "merch_gamb": ("Gaming & Digital Goods", 200, 25000),
    }

    merchants = []
    for i in range(num_merchants):
        cat_key = random.choice(list(merchant_categories.keys()))
        cat_name, min_amt, max_amt = merchant_categories[cat_key]
        merchants.append({
            "merchant_id": f"merch_{i+1:03d}",
            "merchant_name": f"{cat_name} #{i+1}",
            "category": cat_key,
            "min_amt": min_amt,
            "max_amt": max_amt,
            "risk_weight": 1.4 if cat_key in ["merch_lux", "merch_gamb", "merch_elec"] else 0.9,
        })

    # 2. Establish Customer Profiles
    countries = ["IN", "IN", "IN", "IN", "IN", "US", "AE", "SG", "GB"]  # 80%+ India
    payment_methods = ["upi", "upi", "credit_card", "debit_card", "net_banking"]

    customers = []
    for i in range(num_customers):
        cust_id = f"cust_{i+1:04d}"
        usual_country = "IN" if random.random() < 0.88 else random.choice(["US", "AE", "SG", "GB"])
        usual_device = f"dev_{cust_id[-4:]}_primary"
        usual_ip = f"103.21.{random.randint(10, 250)}.{random.randint(2, 254)}"
        
        # Customer spending persona
        persona = random.choices(
            ["budget", "middle", "affluent"],
            weights=[0.45, 0.45, 0.10]
        )[0]
        
        if persona == "budget":
            base_mean = float(np.random.gamma(shape=3.0, scale=400)) + 200  # ~1400 INR
        elif persona == "middle":
            base_mean = float(np.random.gamma(shape=4.0, scale=1200)) + 800  # ~5600 INR
        else:
            base_mean = float(np.random.gamma(shape=5.0, scale=6000)) + 5000 # ~35000 INR

        account_age_days = random.randint(15, 1200)
        
        customers.append({
            "customer_id": cust_id,
            "usual_country": usual_country,
            "usual_device": usual_device,
            "usual_ip": usual_ip,
            "persona": persona,
            "base_mean": base_mean,
            "account_age_days": account_age_days,
            "preferred_method": random.choice(payment_methods),
            "preferred_hours": list(range(8, 23)),  # 8 AM to 11 PM
        })

    # Shared device syndicates for entity graph correlation (fraud rings)
    syndicate_devices = [f"dev_syndicate_{s}" for s in range(3)]
    syndicate_ips = [f"45.154.255.{random.randint(1, 250)}" for _ in range(3)]

    # 3. Generate Transactions across a 60-day window
    start_time = datetime.datetime(2026, 7, 5, 0, 0, 0)
    
    # State tracking per customer to prevent future leakage
    cust_history: Dict[str, List[Dict[str, Any]]] = {c["customer_id"]: [] for c in customers}
    
    records = []
    
    # Generate timestamp order
    time_deltas = np.sort(np.random.uniform(0, 60 * 24 * 3600, num_transactions))
    
    for idx, dt_sec in enumerate(time_deltas):
        txn_id = f"txn_{idx+1:06d}"
        txn_time = start_time + datetime.timedelta(seconds=float(dt_sec))
        
        # Pick customer
        cust = random.choice(customers)
        cust_id = cust["customer_id"]
        history = cust_history[cust_id]
        
        # Historical stats at this point in time
        cust_tx_count = len(history)
        cust_age_at_tx = cust["account_age_days"] + int(dt_sec / 86400)
        
        if cust_tx_count > 0:
            hist_amounts = [h["amount"] for h in history]
            cust_avg_amount = float(np.mean(hist_amounts))
            cust_max_amount = float(np.max(hist_amounts))
        else:
            cust_avg_amount = cust["base_mean"]
            cust_max_amount = cust["base_mean"] * 1.5

        # Velocity tracking in past windows
        ten_mins_ago = txn_time - datetime.timedelta(minutes=10)
        one_hour_ago = txn_time - datetime.timedelta(hours=1)
        one_day_ago = txn_time - datetime.timedelta(days=1)

        tx_last_10m = sum(1 for h in history if h["timestamp"] >= ten_mins_ago)
        tx_last_1h = sum(1 for h in history if h["timestamp"] >= one_hour_ago)
        tx_last_24h = sum(1 for h in history if h["timestamp"] >= one_day_ago)

        # Decide if this transaction is fraudulent
        is_fraud = 1 if (random.random() < fraud_rate and idx > 150) else 0

        # Merchant selection
        if is_fraud:
            # 60% of fraud targets high-risk merchants, 40% targets normal everyday merchants
            if random.random() < 0.60:
                high_risk_merchs = [m for m in merchants if m["risk_weight"] > 1.0]
                merch = random.choice(high_risk_merchs)
            else:
                merch = random.choice(merchants)
        else:
            merch = random.choice(merchants)

        # Device, IP, Country, Hour, Amount logic
        hour = txn_time.hour
        is_unusual_hour = 1 if (hour < 5 or hour > 23) else 0

        if is_fraud:
            fraud_type = random.choices(
                ["stealth_micro_testing", "account_takeover", "velocity_burst", "foreign_syndicate", "mimic_normal"],
                weights=[0.20, 0.30, 0.20, 0.15, 0.15]
            )[0]

            if fraud_type == "stealth_micro_testing":
                # Stealthy micro-deposit / card probing: low amount, looks innocuous!
                amount = float(random.choice([1.0, 2.0, 5.0, 10.0, 50.0, 100.0]))
                device_id = random.choice(syndicate_devices) if random.random() < 0.5 else f"dev_{random.randint(1000, 9999)}"
                ip_address = random.choice(syndicate_ips) if random.random() < 0.5 else f"185.220.101.{random.randint(1, 254)}"
                country = cust["usual_country"] if random.random() < 0.7 else random.choice(["US", "SG", "IN"])
                payment_method = random.choice(["credit_card", "debit_card"])
                is_new_device = 1 if random.random() < 0.65 else 0
                is_new_country = 1 if country != cust["usual_country"] else 0
                is_unusual_hour = 1 if random.random() < 0.4 else 0

            elif fraud_type == "account_takeover":
                # Stolen credentials on new device, higher amount
                amount = cust_avg_amount * random.uniform(2.2, 4.8)
                device_id = f"dev_ato_{random.randint(1000, 9999)}"
                ip_address = f"103.21.{random.randint(10, 250)}.{random.randint(2, 254)}"
                country = cust["usual_country"]
                payment_method = cust["preferred_method"]
                is_new_device = 1 if random.random() < 0.85 else 0
                is_new_country = 0
                is_unusual_hour = 1 if (hour < 6 or hour > 22 or random.random() < 0.4) else 0

            elif fraud_type == "velocity_burst":
                # Rapid bursts of transactions
                amount = cust_avg_amount * random.uniform(1.2, 3.5)
                device_id = random.choice(syndicate_devices)
                ip_address = random.choice(syndicate_ips)
                country = cust["usual_country"]
                payment_method = cust["preferred_method"]
                is_new_device = 1 if random.random() < 0.7 else 0
                is_new_country = 0
                tx_last_10m += random.randint(2, 5)
                tx_last_1h += random.randint(4, 9)
                tx_last_24h += random.randint(6, 14)

            elif fraud_type == "foreign_syndicate":
                # Impossible travel or foreign proxy
                amount = max(cust_avg_amount * random.uniform(2.5, 6.0), merch["min_amt"])
                device_id = f"dev_proxy_{random.randint(1000, 9999)}"
                ip_address = f"198.51.100.{random.randint(1, 254)}"
                country = random.choice(["NG", "RO", "UA", "VN", "RU", "AE"])
                payment_method = "credit_card"
                is_new_device = 1
                is_new_country = 1 if country != cust["usual_country"] else 0
                is_unusual_hour = 1 if random.random() < 0.6 else 0

            else: # mimic_normal: mimics normal user behaviour to create hard classification boundaries (hard FN cases)
                amount = float(np.random.gamma(shape=4.0, scale=cust_avg_amount / 4.0))
                device_id = cust["usual_device"] if random.random() < 0.5 else f"dev_{cust_id[-4:]}_sec"
                ip_address = cust["usual_ip"]
                country = cust["usual_country"]
                payment_method = cust["preferred_method"]
                is_new_device = 0
                is_new_country = 0
                is_unusual_hour = 0
        else:
            # Legitimate transactions
            legit_scenario = random.choices(
                ["routine", "legitimate_high_ticket", "legitimate_travel", "legitimate_new_phone", "legitimate_velocity"],
                weights=[0.80, 0.08, 0.04, 0.05, 0.03]
            )[0]

            if legit_scenario == "legitimate_high_ticket":
                # Buying electronics / appliances / wedding gifts: high amount, but from KNOWN device and country!
                amount = cust_avg_amount * random.uniform(3.0, 7.5)
                device_id = cust["usual_device"]
                ip_address = cust["usual_ip"]
                country = cust["usual_country"]
                payment_method = cust["preferred_method"]
                is_new_device = 0
                is_new_country = 0

            elif legit_scenario == "legitimate_travel":
                # Vacation/business travel: legitimate user in new country/IP
                amount = cust_avg_amount * random.uniform(1.0, 2.5)
                device_id = cust["usual_device"] # same phone!
                ip_address = f"14.139.{random.randint(10, 250)}.{random.randint(2, 254)}"
                country = random.choice(["US", "AE", "GB", "TH", "SG"])
                payment_method = "credit_card"
                is_new_device = 0
                is_new_country = 1 if country != cust["usual_country"] else 0

            elif legit_scenario == "legitimate_new_phone":
                # Upgraded phone: new device, normal amount, normal country
                amount = float(np.random.gamma(shape=4.0, scale=cust_avg_amount / 4.0))
                device_id = f"dev_{cust_id[-4:]}_newphone"
                ip_address = cust["usual_ip"]
                country = cust["usual_country"]
                payment_method = cust["preferred_method"]
                is_new_device = 1
                is_new_country = 0

            elif legit_scenario == "legitimate_velocity":
                # Multiple bills paid on same day, booking group travel
                amount = float(np.random.gamma(shape=3.5, scale=cust_avg_amount / 3.5))
                device_id = cust["usual_device"]
                ip_address = cust["usual_ip"]
                country = cust["usual_country"]
                payment_method = cust["preferred_method"]
                is_new_device = 0
                is_new_country = 0
                tx_last_10m += random.randint(1, 3)
                tx_last_1h += random.randint(2, 5)

            else: # routine
                amount = float(np.random.gamma(shape=4.0, scale=cust_avg_amount / 4.0))
                device_id = cust["usual_device"] if random.random() < 0.94 else f"dev_{cust_id[-4:]}_secondary"
                is_new_device = 1 if device_id != cust["usual_device"] and device_id != f"dev_{cust_id[-4:]}_secondary" else 0
                ip_address = cust["usual_ip"] if random.random() < 0.88 else f"103.21.{random.randint(10, 250)}.{random.randint(2, 254)}"
                country = cust["usual_country"] if random.random() < 0.97 else "US"
                is_new_country = 1 if country != cust["usual_country"] else 0
                payment_method = cust["preferred_method"] if random.random() < 0.8 else random.choice(payment_methods)

        amount = round(float(amount), 2)
        status = "failed" if (is_fraud and random.random() < 0.25) else "success"

        record = {
            "transaction_id": txn_id,
            "customer_id": cust_id,
            "merchant_id": merch["merchant_id"],
            "amount": amount,
            "currency": "INR",
            "timestamp": txn_time.isoformat(),
            "device_id": device_id,
            "ip_address": ip_address,
            "country": country,
            "payment_method": payment_method,
            "transaction_status": status,
            "customer_age_days": cust_age_at_tx,
            "customer_transaction_count": cust_tx_count,
            "customer_avg_amount": round(cust_avg_amount, 2),
            "customer_max_amount": round(cust_max_amount, 2),
            "customer_usual_country": cust["usual_country"],
            "customer_usual_device": cust["usual_device"],
            "transactions_last_10m": tx_last_10m,
            "transactions_last_1h": tx_last_1h,
            "transactions_last_24h": tx_last_24h,
            "is_new_device": int(is_new_device),
            "is_new_country": int(is_new_country),
            "is_unusual_hour": int(is_unusual_hour),
            "is_fraud": int(is_fraud),
        }

        records.append(record)

        # Update customer state for future transactions
        cust_history[cust_id].append({
            "timestamp": txn_time,
            "amount": amount,
            "device_id": device_id,
            "country": country,
        })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    print("Generating synthetic payment transactions dataset...")
    df = generate_synthetic_transactions(
        num_customers=250,
        num_merchants=35,
        num_transactions=6500,
        fraud_rate=0.052,
        random_seed=42,
    )
    output_path = "data/transactions.csv"
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} transactions to {output_path}")
    print(f"Fraud count: {df['is_fraud'].sum()} ({df['is_fraud'].mean():.2%})")
