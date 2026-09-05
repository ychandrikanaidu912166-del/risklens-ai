import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any


FEATURE_COLUMNS = [
    "amount",
    "amount_to_avg_ratio",
    "amount_to_max_ratio",
    "amount_deviation",
    "transactions_last_10m",
    "transactions_last_1h",
    "transactions_last_24h",
    "customer_transaction_count",
    "customer_age_days",
    "is_new_device",
    "is_new_country",
    "is_unusual_hour",
    "hour_sin",
    "hour_cos",
    "is_credit_card",
    "is_upi",
    "is_net_banking",
]


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts time-aware features from transaction records.
    Works on both batch DataFrames and single-transaction DataFrames/dictionaries.
    """
    df = df.copy()

    # Fill default values for required columns if missing
    defaults = {
        "amount": 0.0,
        "customer_avg_amount": 1000.0,
        "customer_max_amount": 1000.0,
        "payment_method": "credit_card",
        "transactions_last_10m": 0,
        "transactions_last_1h": 0,
        "transactions_last_24h": 0,
        "customer_transaction_count": 1,
        "customer_age_days": 30,
        "is_new_device": 0,
        "is_new_country": 0,
        "is_unusual_hour": 0,
    }
    for col, def_val in defaults.items():
        if col not in df.columns:
            df[col] = def_val
        else:
            df[col] = df[col].fillna(def_val)

    # Ensure timestamp is present and datetime
    if "timestamp" not in df.columns or df["timestamp"].isna().all():
        df["timestamp"] = pd.Timestamp.now()
    elif not np.issubdtype(df["timestamp"].dtype, np.datetime64):
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Temporal cyclic features
    hour = df["timestamp"].dt.hour
    df["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)

    # Behavioural baseline ratios
    safe_avg = df["customer_avg_amount"].replace(0, 1.0)
    safe_max = df["customer_max_amount"].replace(0, 1.0)

    df["amount_to_avg_ratio"] = df["amount"] / safe_avg
    df["amount_to_max_ratio"] = df["amount"] / safe_max
    df["amount_deviation"] = np.abs(df["amount"] - df["customer_avg_amount"])

    # Payment method indicators
    df["is_credit_card"] = (df["payment_method"] == "credit_card").astype(int)
    df["is_upi"] = (df["payment_method"] == "upi").astype(int)
    df["is_net_banking"] = (df["payment_method"] == "net_banking").astype(int)

    # Binary flags
    df["is_new_device"] = df["is_new_device"].astype(int)
    df["is_new_country"] = df["is_new_country"].astype(int)
    df["is_unusual_hour"] = df["is_unusual_hour"].astype(int)

    return df[FEATURE_COLUMNS]


def extract_single_transaction_features(txn: Dict[str, Any]) -> pd.DataFrame:
    """
    Extracts features for a single transaction dictionary.
    """
    df = pd.DataFrame([txn])
    return extract_features(df)
