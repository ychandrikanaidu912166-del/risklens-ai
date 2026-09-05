from backend.app.risk.fusion import fuse
from backend.app.schemas.evidence import Evidence, EvidenceBundle


def _bundle(pos_weights=(), neg_weights=()):
    return EvidenceBundle(
        supporting=[Evidence(id=f"E{i}", code=f"P{i}", description="x", weight=w, source="rule")
                    for i, w in enumerate(pos_weights)],
        counter=[Evidence(id=f"C{i}", code=f"N{i}", description="x", weight=w, source="rule")
                 for i, w in enumerate(neg_weights)],
    )


def test_score_in_range_for_low_prob_no_evidence():
    r = fuse(0.02, _bundle())
    assert 0 <= r.risk_score <= 100
    assert r.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_score_monotonic_in_probability():
    lo = fuse(0.1, _bundle()).risk_score
    hi = fuse(0.9, _bundle()).risk_score
    assert hi > lo


def test_counter_evidence_reduces_score():
    without = fuse(0.6, _bundle(pos_weights=(20, 10))).risk_score
    withcounter = fuse(0.6, _bundle(pos_weights=(20, 10), neg_weights=(-8,))).risk_score
    assert withcounter <= without


def test_score_capped_at_100():
    r = fuse(1.0, _bundle(pos_weights=(50, 50, 50)))
    assert r.risk_score == 100
    assert r.risk_level == "CRITICAL"
