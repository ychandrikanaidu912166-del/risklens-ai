import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ml_model_version" in data


def test_metrics_endpoints():
    res_overview = client.get("/api/v1/metrics/overview")
    assert res_overview.status_code == 200
    data = res_overview.json()
    assert "total_transactions" in data
    assert "precision" in data
    assert "business_cost" in data

    res_model = client.get("/api/v1/metrics/model")
    assert res_model.status_code == 200
    m_data = res_model.json()
    assert "primary_xgboost" in m_data


def test_score_and_investigate_flow():
    # Ingest a new transaction
    payload = {
        "transaction_id": "txn_unit_test_999",
        "customer_id": "cust_0042",
        "merchant_id": "merch_005",
        "amount": 42000.0,
        "currency": "INR",
        "timestamp": "2026-08-20T23:45:00",
        "device_id": "dev_test_probe",
        "ip_address": "198.51.100.42",
        "country": "RO",
        "payment_method": "credit_card",
        "customer_age_days": 120,
        "customer_transaction_count": 14,
        "customer_avg_amount": 2500.0,
        "customer_max_amount": 6000.0,
        "customer_usual_country": "IN",
        "customer_usual_device": "dev_cust_0042_primary",
        "transactions_last_10m": 3,
        "transactions_last_1h": 7,
        "transactions_last_24h": 10,
        "is_new_device": 1,
        "is_new_country": 1,
        "is_unusual_hour": 1,
    }
    score_res = client.post("/api/v1/transactions/score", json=payload)
    assert score_res.status_code == 200
    score_data = score_res.json()["data"]
    assert score_data["transaction_id"] == "txn_unit_test_999"
    assert score_data["risk_score"] > 50

    # Fetch investigation detail
    detail_res = client.get("/api/v1/investigations/txn_unit_test_999")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["transaction"]["transaction_id"] == "txn_unit_test_999"
    assert len(detail_data["evidence"]) > 0
    assert detail_data["ai_investigation"] is not None

    # Submit analyst decision
    decision_payload = {
        "decision": "HOLD",
        "reason": "Suspicious foreign IP and 16x average spend pattern detected.",
        "analyst_id": "lead_analyst_qa",
    }
    dec_res = client.post("/api/v1/investigations/txn_unit_test_999/decision", json=decision_payload)
    assert dec_res.status_code == 200
    dec_data = dec_res.json()["data"]
    assert dec_data["decision"] == "HOLD"
    assert dec_data["status"] == "RESOLVED"

    # Verify updated detail shows analyst decision
    detail_after = client.get("/api/v1/investigations/txn_unit_test_999").json()
    assert detail_after["existing_decision"]["decision"] == "HOLD"


def test_invalid_transaction_id():
    response = client.get("/api/v1/investigations/txn_does_not_exist_xyz")
    assert response.status_code == 404
