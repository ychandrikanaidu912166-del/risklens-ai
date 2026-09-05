import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.decision_engine.policy import DecisionPolicyEngine

client = TestClient(app)


def test_simulation_presets():
    res = client.get("/api/v1/transactions/simulation/presets")
    assert res.status_code == 200
    data = res.json()
    assert "presets" in data
    assert len(data["presets"]) >= 5
    preset_ids = [p["id"] for p in data["presets"]]
    assert "preset_ato" in preset_ids
    assert "preset_benign_high_ticket" in preset_ids


def test_simulate_ato_transaction():
    presets_res = client.get("/api/v1/transactions/simulation/presets").json()
    ato_preset = next(p for p in presets_res["presets"] if p["id"] == "preset_ato")
    
    sim_res = client.post("/api/v1/transactions/simulate", json=ato_preset["payload"])
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    
    assert sim_data["status"] == "success"
    assert "pipeline_trace" in sim_data
    assert len(sim_data["pipeline_trace"]) == 8
    
    res = sim_data["result"]
    assert res["risk_score"] >= 60
    assert "business_impact" in res
    assert "signals_breakdown" in res
    assert res["business_impact"]["potential_loss_exposure"] == 48500.0


def test_simulate_benign_high_ticket():
    presets_res = client.get("/api/v1/transactions/simulation/presets").json()
    benign_preset = next(p for p in presets_res["presets"] if p["id"] == "preset_benign_high_ticket")
    
    sim_res = client.post("/api/v1/transactions/simulate", json=benign_preset["payload"])
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    
    res = sim_data["result"]
    # Should have positive counter evidence (verified hardware device, established tenure)
    assert res["counter_evidence_count"] >= 2


def test_confidence_aware_high_risk_low_confidence_policy():
    # Context with elevated risk but low confidence
    context = {
        "risk_score": 75,
        "risk_level": "HIGH",
        "evidence": [{"type": "AMOUNT_ANOMALY", "severity": "HIGH", "description": "High amount"}],
        "counter_evidence": [],
        "transaction": {"amount": 35000.0, "customer_transaction_count": 1},  # Brand new customer (1 tx)
        "ai_investigation": {"confidence": 0.58}  # Low confidence
    }
    decision = DecisionPolicyEngine.evaluate_decision(context)
    
    # Must enforce: High Risk + Low Confidence -> MANUAL_REVIEW
    assert decision["decision"] == "MANUAL_REVIEW"
    assert "insufficient confidence" in decision["reason"].lower()
    assert decision["confidence_score"] < 0.70
    assert decision["business_impact"]["potential_loss_exposure"] == 35000.0
