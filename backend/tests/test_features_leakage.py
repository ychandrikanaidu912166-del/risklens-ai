"""Guard against future-info leakage in velocity/behavior features."""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from backend.app.ml import features


def _rows(customer="C1", start="2025-02-01 09:00", n=6, dt_minutes=10, amount=100.0):
    ts0 = pd.to_datetime(start)
    return [
        {
            "tx_id": f"T{i}",
            "ts": ts0 + timedelta(minutes=i * dt_minutes),
            "customer_id": customer,
            "merchant_id": f"M{i%2}",
            "merchant_category": "grocery",
            "risk_tier": 1,
            "amount": amount * (1 + 0.1 * i),
            "currency": "INR",
            "device_id": f"D{i%2}",
            "ip_hash": "iphash",
            "ip_country": "IN",
            "customer_country": "IN",
            "channel": "web",
            "auth_result": "success",
            "hour": (ts0 + timedelta(minutes=i * dt_minutes)).hour,
            "day_of_week": (ts0 + timedelta(minutes=i * dt_minutes)).weekday(),
            "is_fraud_label": 0,
        }
        for i in range(n)
    ]


def test_first_row_has_zero_velocity():
    df = pd.DataFrame(_rows(n=5))
    out = features.build_batch_features(df)
    # First transaction per customer must have zero prior counts.
    first = out.iloc[0]
    assert first["velocity_1h"] == 0
    assert first["velocity_24h"] == 0
    assert first["customer_prior_tx_count"] == 0


def test_velocity_uses_only_past_rows():
    df = pd.DataFrame(_rows(n=5, dt_minutes=10))  # spans 40 minutes
    out = features.build_batch_features(df)
    # Row index 3 was preceded by 3 rows all within the last hour.
    assert out.iloc[3]["velocity_1h"] == 3
    assert out.iloc[3]["velocity_24h"] == 3


def test_no_future_amount_included_in_baseline():
    rows = _rows(n=6)
    rows[-1]["amount"] = 1_000_000.0  # future outlier
    df = pd.DataFrame(rows)
    out = features.build_batch_features(df)
    # Amount z-score for row 2 must not consider the future 1M amount.
    z_row2 = out.iloc[2]["amount_z_vs_customer"]
    assert abs(z_row2) < 5.0
