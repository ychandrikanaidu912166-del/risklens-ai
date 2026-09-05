import pytest
import pandas as pd
from ml.features.feature_pipeline import extract_features, extract_single_transaction_features, FEATURE_COLUMNS


def test_feature_extraction_columns():
    tx = {
        "transaction_id": "txn_test",
        "timestamp": "2026-08-10T15:30:00",
        "amount": 5000.0,
        "customer_avg_amount": 1000.0,
        "customer_max_amount": 3000.0,
        "customer_transaction_count": 10,
        "customer_age_days": 180,
        "transactions_last_10m": 1,
        "transactions_last_1h": 2,
        "transactions_last_24h": 4,
        "is_new_device": 0,
        "is_new_country": 0,
        "is_unusual_hour": 0,
        "payment_method": "upi",
    }
    feat_df = extract_single_transaction_features(tx)
    assert isinstance(feat_df, pd.DataFrame)
    assert list(feat_df.columns) == FEATURE_COLUMNS
    assert feat_df.iloc[0]["amount_to_avg_ratio"] == 5.0
    assert feat_df.iloc[0]["is_upi"] == 1
    assert feat_df.iloc[0]["is_credit_card"] == 0
