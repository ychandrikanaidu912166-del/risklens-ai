"""Feature engineering used identically at train time and inference time.

Design principles:
  1. TRAIN/INFER PARITY. `build_features` accepts a DataFrame of transactions
     plus (optionally) history frames; it produces a feature matrix. The
     inference API constructs the same DataFrame from a single tx + its
     customer's history and reuses this function.
  2. NO LEAKAGE. Velocity / behavioral-baseline features for a row at time T
     use only rows with ts < T. We enforce this in the batch builder with a
     strict past-only rolling scan.
  3. NO TARGET IN FEATURES. `is_fraud_label` is never in `FEATURE_COLUMNS`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Ordered feature list — the serving code depends on this exact order.
NUMERIC_FEATURES: List[str] = [
    "amount",
    "log_amount",
    "hour",
    "day_of_week",
    "risk_tier",
    "amount_z_vs_customer",
    "amount_ratio_vs_customer",
    "velocity_1h",
    "velocity_24h",
    "distinct_merchants_24h",
    "distinct_devices_24h",
    "fail_count_1h",
    "device_new_for_customer",
    "country_mismatch",
    "customer_prior_tx_count",
    "unusual_hour_for_customer",
]

CATEGORICAL_FEATURES: List[str] = [
    "merchant_category",
    "channel",
    "auth_result",
]

# Every value the one-hot encoder should recognize.  Kept fixed to avoid drift
# between train and inference vocabularies.
CATEGORICAL_VOCAB: Dict[str, List[str]] = {
    "merchant_category": [
        "grocery", "electronics", "travel", "gaming", "wallet_topup",
        "utilities", "food_delivery", "streaming", "jewellery", "crypto_gateway",
    ],
    "channel": ["web", "mobile", "pos", "api"],
    "auth_result": ["success", "failure", "3ds_pass", "3ds_fail"],
}


@dataclass
class CustomerBaseline:
    n_prior_tx: int
    mean_amount: Optional[float]
    std_amount: Optional[float]
    common_hours: List[int]
    common_countries: List[str]
    known_devices: List[str]


def build_batch_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build features for a full historical dataset (used during training).

    Rows must be sorted by ts. Velocity/behavior features are computed with a
    strict past-only scan per customer to avoid leakage.
    """
    df = df.sort_values("ts").reset_index(drop=True).copy()
    df["ts"] = pd.to_datetime(df["ts"])
    df["log_amount"] = np.log1p(df["amount"].astype(float))

    # ---- per-customer running state ---------------------------------------
    customer_state: Dict[str, Dict] = {}

    amount_z = np.zeros(len(df))
    amount_ratio = np.zeros(len(df))
    velocity_1h = np.zeros(len(df), dtype=int)
    velocity_24h = np.zeros(len(df), dtype=int)
    distinct_merchants_24h = np.zeros(len(df), dtype=int)
    distinct_devices_24h = np.zeros(len(df), dtype=int)
    fail_count_1h = np.zeros(len(df), dtype=int)
    device_new = np.zeros(len(df), dtype=int)
    prior_count = np.zeros(len(df), dtype=int)
    unusual_hour = np.zeros(len(df), dtype=int)
    country_mismatch = (df["ip_country"] != df["customer_country"]).astype(int).values

    for i, row in enumerate(df.itertuples(index=False)):
        cid = row.customer_id
        state = customer_state.setdefault(cid, {
            "amounts": [],
            "history": [],  # list of (ts, merchant_id, device_id, auth_result, hour)
            "devices": set(),
            "hours": [],
        })

        amounts = state["amounts"]
        history = state["history"]

        # --- baseline stats from strictly prior rows ---
        if len(amounts) >= 3:
            mu = float(np.mean(amounts))
            sd = float(np.std(amounts)) or 1e-6
            amount_z[i] = (row.amount - mu) / sd
            amount_ratio[i] = row.amount / max(mu, 1e-6)
        else:
            amount_z[i] = 0.0
            amount_ratio[i] = 1.0

        prior_count[i] = len(amounts)
        device_new[i] = int(row.device_id not in state["devices"])

        if len(state["hours"]) >= 5:
            hist_hours = state["hours"]
            common = _top_k(hist_hours, k=6)
            unusual_hour[i] = int(row.hour not in common)
        else:
            unusual_hour[i] = 0

        # --- windowed counts ---
        ts_i = row.ts
        one_hr = ts_i - pd.Timedelta(hours=1)
        one_day = ts_i - pd.Timedelta(hours=24)

        # walk history from the end while ts >= cutoff
        v1, v24, fails1 = 0, 0, 0
        merchants_24, devices_24 = set(), set()
        for h_ts, h_merchant, h_device, h_auth, _h_hour in reversed(history):
            if h_ts < one_day:
                break
            v24 += 1
            merchants_24.add(h_merchant)
            devices_24.add(h_device)
            if h_ts >= one_hr:
                v1 += 1
                if h_auth in ("failure", "3ds_fail"):
                    fails1 += 1

        velocity_1h[i] = v1
        velocity_24h[i] = v24
        distinct_merchants_24h[i] = len(merchants_24)
        distinct_devices_24h[i] = len(devices_24)
        fail_count_1h[i] = fails1

        # --- update state AFTER computing features (past-only) ---
        amounts.append(row.amount)
        history.append((ts_i, row.merchant_id, row.device_id, row.auth_result, row.hour))
        state["devices"].add(row.device_id)
        state["hours"].append(row.hour)

    df["amount_z_vs_customer"] = amount_z
    df["amount_ratio_vs_customer"] = amount_ratio
    df["velocity_1h"] = velocity_1h
    df["velocity_24h"] = velocity_24h
    df["distinct_merchants_24h"] = distinct_merchants_24h
    df["distinct_devices_24h"] = distinct_devices_24h
    df["fail_count_1h"] = fail_count_1h
    df["device_new_for_customer"] = device_new
    df["customer_prior_tx_count"] = prior_count
    df["unusual_hour_for_customer"] = unusual_hour
    df["country_mismatch"] = country_mismatch

    return df


def build_online_features(tx: dict, history: pd.DataFrame) -> Tuple[pd.DataFrame, CustomerBaseline]:
    """Build a single-row feature frame for one incoming transaction.

    `history` is the customer's prior transactions (may be empty).
    """
    hist = history.copy()
    if not hist.empty:
        hist["ts"] = pd.to_datetime(hist["ts"])
        hist = hist.sort_values("ts")

    ts = pd.to_datetime(tx["ts"])
    amount = float(tx["amount"])

    amounts = hist["amount"].astype(float).tolist() if not hist.empty else []
    if len(amounts) >= 3:
        mu = float(np.mean(amounts))
        sd = float(np.std(amounts)) or 1e-6
        amount_z = (amount - mu) / sd
        amount_ratio = amount / max(mu, 1e-6)
    else:
        mu, sd = (float(np.mean(amounts)) if amounts else None,
                  float(np.std(amounts)) if len(amounts) >= 2 else None)
        amount_z = 0.0
        amount_ratio = 1.0

    known_devices = set(hist["device_id"].tolist()) if not hist.empty else set()
    hours = hist["hour"].tolist() if not hist.empty else []
    common_hours = _top_k(hours, k=6) if len(hours) >= 5 else []
    country_hist = _top_k(hist["ip_country"].tolist(), k=4) if not hist.empty else []

    if not hist.empty:
        one_hr = ts - pd.Timedelta(hours=1)
        one_day = ts - pd.Timedelta(hours=24)
        past = hist[hist["ts"] < ts]
        past_1h = past[past["ts"] >= one_hr]
        past_24h = past[past["ts"] >= one_day]
        velocity_1h = int(len(past_1h))
        velocity_24h = int(len(past_24h))
        distinct_merchants_24h = int(past_24h["merchant_id"].nunique())
        distinct_devices_24h = int(past_24h["device_id"].nunique())
        fail_count_1h = int(past_1h["auth_result"].isin(["failure", "3ds_fail"]).sum())
    else:
        velocity_1h = velocity_24h = distinct_merchants_24h = distinct_devices_24h = fail_count_1h = 0

    device_new = int(tx["device_id"] not in known_devices)
    unusual_hour = int(bool(common_hours) and tx["hour"] not in common_hours)
    country_mismatch = int(tx["ip_country"] != tx["customer_country"])

    row = {
        "amount": amount,
        "log_amount": float(np.log1p(amount)),
        "hour": int(tx["hour"]),
        "day_of_week": int(tx["day_of_week"]),
        "risk_tier": int(tx.get("risk_tier", 1)),
        "amount_z_vs_customer": float(amount_z),
        "amount_ratio_vs_customer": float(amount_ratio),
        "velocity_1h": velocity_1h,
        "velocity_24h": velocity_24h,
        "distinct_merchants_24h": distinct_merchants_24h,
        "distinct_devices_24h": distinct_devices_24h,
        "fail_count_1h": fail_count_1h,
        "device_new_for_customer": device_new,
        "country_mismatch": country_mismatch,
        "customer_prior_tx_count": len(amounts),
        "unusual_hour_for_customer": unusual_hour,
        "merchant_category": tx["merchant_category"],
        "channel": tx.get("channel", "web"),
        "auth_result": tx.get("auth_result", "success"),
    }

    baseline = CustomerBaseline(
        n_prior_tx=len(amounts),
        mean_amount=mu if amounts else None,
        std_amount=sd if len(amounts) >= 2 else None,
        common_hours=common_hours,
        common_countries=country_hist,
        known_devices=list(known_devices),
    )
    return pd.DataFrame([row]), baseline


def encode_matrix(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """One-hot encode categoricals against the fixed vocab and return a numeric matrix."""
    cols: List[str] = []
    pieces: List[np.ndarray] = []

    for col in NUMERIC_FEATURES:
        pieces.append(df[col].astype(float).values.reshape(-1, 1))
        cols.append(col)

    for cat_col in CATEGORICAL_FEATURES:
        vocab = CATEGORICAL_VOCAB[cat_col]
        values = df[cat_col].astype(str).values
        onehot = np.zeros((len(df), len(vocab)), dtype=float)
        for i, v in enumerate(values):
            if v in vocab:
                onehot[i, vocab.index(v)] = 1.0
            else:
                # Unknown category -> all zeros. Model handles OOV as neutral.
                pass
        pieces.append(onehot)
        cols.extend([f"{cat_col}={v}" for v in vocab])

    X = np.hstack(pieces)
    return X, cols


def _top_k(values, k: int) -> List:
    if not values:
        return []
    s = pd.Series(values)
    counts = s.value_counts()
    return counts.head(k).index.tolist()
