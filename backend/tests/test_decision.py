from backend.app.risk.decision import decide
from backend.app.schemas.evidence import Evidence, EvidenceBundle


def _bundle(pos):
    return EvidenceBundle(
        supporting=[Evidence(id=f"E{i}", code=f"P{i}", description="x", weight=w, source="rule")
                    for i, w in enumerate(pos)],
    )


def test_low_risk_approves():
    r = decide(risk_level="LOW", risk_score=15, fraud_probability=0.05,
               evidence=_bundle([]), amount=500.0, prior_tx=20)
    assert r.action == "APPROVE"


def test_medium_small_amount_step_up():
    r = decide(risk_level="MEDIUM", risk_score=45, fraud_probability=0.35,
               evidence=_bundle([10, 8]), amount=1500.0, prior_tx=20)
    assert r.action == "STEP_UP"


def test_medium_large_amount_manual_review():
    r = decide(risk_level="MEDIUM", risk_score=45, fraud_probability=0.35,
               evidence=_bundle([10, 8]), amount=50_000.0, prior_tx=20)
    assert r.action == "MANUAL_REVIEW"


def test_high_score_but_no_evidence_manual_review():
    r = decide(risk_level="HIGH", risk_score=70, fraud_probability=0.9,
               evidence=_bundle([]), amount=1000.0, prior_tx=20)
    assert r.action == "MANUAL_REVIEW"
    assert r.confidence == "low"


def test_critical_strong_evidence_blocks():
    r = decide(
        risk_level="CRITICAL", risk_score=95, fraud_probability=0.95,
        evidence=_bundle([22, 14, 12, 10, 8, 6]),
        amount=25_000.0, prior_tx=50,
    )
    assert r.action == "BLOCK"
    assert r.confidence == "high"


def test_critical_uncertain_holds():
    r = decide(
        risk_level="CRITICAL", risk_score=85, fraud_probability=0.55,
        evidence=_bundle([12, 8, 6]),
        amount=5_000.0, prior_tx=6,
    )
    assert r.action == "HOLD"
