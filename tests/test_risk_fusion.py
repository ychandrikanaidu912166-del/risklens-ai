import pytest
from backend.app.risk_engine.fusion import RiskFusionEngine
from backend.app.decision_engine.policy import DecisionPolicyEngine
from backend.app.investigation.ai_investigator import AIInvestigator


def test_risk_fusion_bounds_and_contributions():
    fusion = RiskFusionEngine.fuse_signals(
        ml_prob=0.92,
        behaviour_diff={
            "amount_comparison": {"amount_ratio": 4.5, "is_anomaly": True},
            "device_comparison": {"is_new_device": True},
            "country_comparison": {"is_new_country": True, "current_country": "US"},
            "hour_comparison": {"is_unusual_hour": True, "current_hour": 3},
            "velocity_comparison": {"is_anomaly": True, "last_10m": 4, "last_1h": 8},
        },
        evidence_list=[{"type": "AMOUNT_ANOMALY", "evidence_id": "ev1"}],
        counter_evidence_list=[],
        entity_signals=[{"type": "SHARED_DEVICE_SYNDICATE", "severity": "CRITICAL", "description": "Device shared across accounts"}]
    )
    assert 0 <= fusion["risk_score"] <= 100
    assert fusion["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert fusion["risk_level"] == "CRITICAL"
    assert len(fusion["factors"]) > 0


def test_decision_policy_engine():
    # Critical risk policy test
    crit_context = {
        "risk_score": 92,
        "risk_level": "CRITICAL",
        "evidence": [{"type": "SHARED_DEVICE_SYNDICATE"}],
        "counter_evidence": [],
        "transaction": {"amount": 75000.0, "customer_transaction_count": 10},
        "ai_investigation": {"confidence": 0.95}
    }
    decision = DecisionPolicyEngine.evaluate_decision(crit_context)
    assert decision["decision"] in ["BLOCK", "HOLD"]
    assert decision["risk_score"] == 92

    # Low risk policy test
    low_context = {
        "risk_score": 12,
        "risk_level": "LOW",
        "evidence": [],
        "counter_evidence": [{"type": "KNOWN_DEVICE"}],
        "transaction": {"amount": 500.0, "customer_transaction_count": 20},
        "ai_investigation": {"confidence": 0.95}
    }
    low_decision = DecisionPolicyEngine.evaluate_decision(low_context)
    assert low_decision["decision"] == "APPROVE"


def test_ai_investigator_deterministic_fallback():
    context = {
        "transaction": {
            "transaction_id": "txn_test_ai",
            "customer_id": "cust_99",
            "amount": 25000.0,
            "customer_transaction_count": 12,
        },
        "risk_score": 88,
        "risk_level": "CRITICAL",
        "evidence": [
            {"type": "AMOUNT_ANOMALY", "severity": "CRITICAL", "description": "Amount is 6.2x baseline"}
        ],
        "counter_evidence": [
            {"type": "KNOWN_DEVICE", "description": "Device matched customer profile"}
        ],
        "customer_behaviour": {
            "amount_comparison": {"amount_ratio": 6.2, "baseline_avg": 4000.0}
        }
    }
    assessment = AIInvestigator.investigate(context)
    assert assessment.risk_level == "CRITICAL"
    assert assessment.is_deterministic_fallback is True
    assert assessment.recommended_action in ["BLOCK", "HOLD", "MANUAL_REVIEW"]
    assert len(assessment.primary_evidence) > 0
    assert len(assessment.counter_evidence) > 0
    assert "definitely fraud" not in assessment.assessment.lower()
