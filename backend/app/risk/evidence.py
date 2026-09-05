"""Evidence engine.

Every evidence item is derived from a concrete signal: a feature value, a rule,
or a model contribution. Nothing here fabricates a number.

Positive evidence adds risk points; counter-evidence subtracts.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from backend.app.schemas.evidence import Evidence, EvidenceBundle
from backend.app.schemas.investigation import BehaviorSnapshot


def build_evidence(
    tx: dict,
    features_row: dict,
    behavior: BehaviorSnapshot,
    fraud_probability: float,
    shap_top: List[Tuple[str, float, float]],
) -> EvidenceBundle:
    supporting: List[Evidence] = []
    counter: List[Evidence] = []

    amount = float(tx["amount"])

    # ---- amount vs baseline ------------------------------------------------
    z = features_row.get("amount_z_vs_customer", 0.0)
    ratio = features_row.get("amount_ratio_vs_customer", 1.0)
    if behavior.n_prior_tx >= 3 and z >= 3.0:
        supporting.append(Evidence(
            id="E-AMT-HIGH",
            code="AMOUNT_ABOVE_BASELINE",
            description=(
                f"Amount {amount:.2f} is {z:.1f}σ above this customer's baseline "
                f"({behavior.mean_amount:.2f})."
            ),
            weight=min(28.0, 6.0 + 3.5 * z),
            source="behavior",
            detail={"z_score": z, "ratio": ratio, "baseline_mean": behavior.mean_amount},
        ))
    elif behavior.n_prior_tx >= 3 and 1.5 <= z < 3.0:
        supporting.append(Evidence(
            id="E-AMT-ELEVATED",
            code="AMOUNT_ELEVATED",
            description=f"Amount {amount:.2f} is {z:.1f}σ above baseline.",
            weight=6.0 + 2.0 * (z - 1.5),
            source="behavior",
            detail={"z_score": z, "ratio": ratio},
        ))
    elif behavior.n_prior_tx >= 5 and -0.5 <= z <= 1.0:
        counter.append(Evidence(
            id="C-AMT-TYPICAL",
            code="AMOUNT_TYPICAL",
            description="Amount is within this customer's typical range.",
            weight=-6.0,
            source="behavior",
            detail={"z_score": z},
        ))

    # ---- velocity ----------------------------------------------------------
    v1h = int(features_row.get("velocity_1h", 0))
    v24h = int(features_row.get("velocity_24h", 0))
    if v1h >= 4:
        supporting.append(Evidence(
            id="E-VEL-1H",
            code="HIGH_VELOCITY_1H",
            description=f"{v1h} transactions from this customer in the last hour.",
            weight=min(22.0, 6.0 + 3.0 * v1h),
            source="velocity",
            detail={"velocity_1h": v1h},
        ))
    if v24h >= 10:
        supporting.append(Evidence(
            id="E-VEL-24H",
            code="HIGH_VELOCITY_24H",
            description=f"{v24h} transactions from this customer in the last 24h.",
            weight=min(14.0, 4.0 + 0.6 * v24h),
            source="velocity",
            detail={"velocity_24h": v24h},
        ))

    fails = int(features_row.get("fail_count_1h", 0))
    if fails >= 2:
        supporting.append(Evidence(
            id="E-FAIL-1H",
            code="REPEATED_AUTH_FAILURES",
            description=f"{fails} auth failures for this customer in the last hour.",
            weight=min(18.0, 5.0 + 3.0 * fails),
            source="velocity",
            detail={"fail_count_1h": fails},
        ))

    # ---- device ------------------------------------------------------------
    if behavior.is_new_device and behavior.n_prior_tx >= 3:
        supporting.append(Evidence(
            id="E-DEV-NEW",
            code="NEW_DEVICE",
            description=f"Device {tx['device_id']} not seen before for this customer.",
            weight=14.0,
            source="rule",
            detail={"device_id": tx["device_id"]},
        ))
    elif not behavior.is_new_device and behavior.n_prior_tx >= 3:
        counter.append(Evidence(
            id="C-DEV-KNOWN",
            code="KNOWN_DEVICE",
            description="Device is one the customer has used before.",
            weight=-5.0,
            source="rule",
            detail={"device_id": tx["device_id"]},
        ))

    # ---- country / IP mismatch --------------------------------------------
    if features_row.get("country_mismatch", 0):
        supporting.append(Evidence(
            id="E-GEO-MISMATCH",
            code="IP_COUNTRY_MISMATCH",
            description=(
                f"IP country {tx['ip_country']} differs from customer's home country "
                f"{tx['customer_country']}."
            ),
            weight=12.0,
            source="rule",
            detail={
                "ip_country": tx["ip_country"],
                "customer_country": tx["customer_country"],
            },
        ))
    if behavior.is_new_country and behavior.n_prior_tx >= 3:
        supporting.append(Evidence(
            id="E-GEO-NEW",
            code="UNSEEN_IP_COUNTRY",
            description=f"IP originates from {tx['ip_country']}, not in customer's usual countries.",
            weight=8.0,
            source="behavior",
            detail={"seen_countries": behavior.common_countries},
        ))

    # ---- unusual hour ------------------------------------------------------
    if behavior.unusual_hour:
        supporting.append(Evidence(
            id="E-HOUR-UNUSUAL",
            code="UNUSUAL_HOUR",
            description=f"Transaction at hour {tx['hour']:02d} outside this customer's usual pattern.",
            weight=6.0,
            source="behavior",
            detail={"hour": tx["hour"], "common_hours": behavior.common_hours},
        ))

    # ---- merchant risk tier -----------------------------------------------
    tier = int(features_row.get("risk_tier", 1))
    if tier >= 3:
        supporting.append(Evidence(
            id="E-MER-TIER",
            code="HIGH_RISK_MERCHANT",
            description=f"Merchant category '{tx['merchant_category']}' is high-risk tier.",
            weight=8.0,
            source="rule",
            detail={"merchant_category": tx["merchant_category"], "risk_tier": tier},
        ))

    # ---- model probability -------------------------------------------------
    if fraud_probability >= 0.7:
        supporting.append(Evidence(
            id="E-ML-HIGH",
            code="MODEL_HIGH_CONFIDENCE",
            description=f"ML model predicts fraud probability {fraud_probability:.2%}.",
            weight=22.0,
            source="model",
            detail={"probability": fraud_probability},
        ))
    elif fraud_probability >= 0.4:
        supporting.append(Evidence(
            id="E-ML-MED",
            code="MODEL_ELEVATED",
            description=f"ML model probability {fraud_probability:.2%} above alert threshold.",
            weight=10.0 + 20.0 * (fraud_probability - 0.4),
            source="model",
            detail={"probability": fraud_probability},
        ))
    elif fraud_probability < 0.05 and behavior.n_prior_tx >= 5:
        counter.append(Evidence(
            id="C-ML-LOW",
            code="MODEL_LOW",
            description=f"ML model probability only {fraud_probability:.2%}.",
            weight=-6.0,
            source="model",
            detail={"probability": fraud_probability},
        ))

    # ---- long-standing customer -------------------------------------------
    if behavior.n_prior_tx >= 40:
        counter.append(Evidence(
            id="C-CUST-TENURED",
            code="TENURED_CUSTOMER",
            description=f"Customer has {behavior.n_prior_tx} prior transactions.",
            weight=-4.0,
            source="behavior",
            detail={"n_prior_tx": behavior.n_prior_tx},
        ))

    # ---- SHAP top contributor (only if it isn't already redundant) --------
    seen_codes = {e.code for e in supporting}
    for feat_name, feat_val, contribution in shap_top[:3]:
        if contribution <= 0:
            continue
        code = f"SHAP_{feat_name.upper()}"
        if code in seen_codes:
            continue
        supporting.append(Evidence(
            id=f"E-SHAP-{feat_name}",
            code=code,
            description=f"Model attributes risk to feature '{feat_name}' (value {feat_val:.2f}).",
            weight=min(10.0, 3.0 + 5.0 * abs(contribution)),
            source="model",
            detail={"feature": feat_name, "value": feat_val, "contribution": contribution},
        ))

    return EvidenceBundle(supporting=supporting, counter=counter)
