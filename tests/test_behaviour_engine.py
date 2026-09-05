import pytest
from backend.app.risk_engine.behaviour import BehaviourEngine
from backend.app.risk_engine.evidence import EvidenceEngine
from backend.app.risk_engine.counter_evidence import CounterEvidenceEngine


def test_behaviour_baseline_and_comparison():
    history = [
        {"amount": 1000.0, "device_id": "dev_1", "country": "IN", "ip_address": "1.1.1.1", "merchant_id": "m1", "timestamp": "2026-08-01T10:00:00"},
        {"amount": 1200.0, "device_id": "dev_1", "country": "IN", "ip_address": "1.1.1.1", "merchant_id": "m2", "timestamp": "2026-08-02T12:00:00"},
        {"amount": 1100.0, "device_id": "dev_1", "country": "IN", "ip_address": "1.1.1.1", "merchant_id": "m1", "timestamp": "2026-08-03T14:00:00"},
    ]
    baseline = BehaviourEngine.calculate_customer_baseline(history)
    assert baseline["transaction_count"] == 3
    assert baseline["avg_amount"] == 1100.0
    assert "dev_1" in baseline["known_devices"]

    # Compare anomalous transaction
    new_tx = {
        "amount": 8000.0,
        "device_id": "dev_unknown",
        "country": "US",
        "timestamp": "2026-08-04T03:00:00",
        "transactions_last_10m": 4,
        "transactions_last_1h": 8,
    }
    diff = BehaviourEngine.compare_transaction(new_tx, baseline)
    assert diff["amount_comparison"]["is_anomaly"] is True
    assert diff["amount_comparison"]["amount_ratio"] > 7.0
    assert diff["device_comparison"]["is_new_device"] is True
    assert diff["country_comparison"]["is_new_country"] is True
    assert diff["velocity_comparison"]["is_anomaly"] is True


def test_evidence_and_counter_evidence_generation():
    tx = {
        "transaction_id": "txn_ev_01",
        "customer_id": "cust_01",
        "device_id": "dev_new",
        "ip_address": "2.2.2.2",
        "country": "US",
        "amount": 50000.0,
        "customer_age_days": 150,
        "customer_transaction_count": 25,
        "timestamp": "2026-08-10T02:30:00",
        "is_new_device": 1,
        "is_new_country": 1,
        "is_unusual_hour": 1,
        "transactions_last_10m": 5,
        "transactions_last_1h": 10,
    }
    baseline = {
        "avg_amount": 2500.0,
        "median_amount": 2200.0,
        "p95_amount": 5000.0,
        "known_devices": ["dev_old"],
        "known_countries": ["IN"],
        "active_hours": list(range(9, 21)),
        "transaction_count": 25,
    }
    diff = BehaviourEngine.compare_transaction(tx, baseline)
    evidence = EvidenceEngine.generate_evidence(tx, diff, ml_prob=0.95, entity_signals=[])
    
    # Verify evidence items exist
    ev_types = [e["type"] for e in evidence]
    assert "AMOUNT_ANOMALY" in ev_types
    assert "HIGH_VELOCITY" in ev_types
    assert "NEW_DEVICE" in ev_types
    assert "NEW_COUNTRY" in ev_types
    assert "ML_HIGH_RISK" in ev_types

    # Verify counter evidence returns list
    counter_ev = CounterEvidenceEngine.generate_counter_evidence(tx, baseline, diff)
    assert isinstance(counter_ev, list)
