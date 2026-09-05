"""Evaluation utilities.

Every reported metric is computed from actual predictions on a held-out set.
We never hardcode metric values.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    brier_score_loss,
)

from backend.app.config import Settings, get_settings


def _pick_operating_threshold(y_true: np.ndarray, y_proba: np.ndarray, target_fpr: float = 0.01) -> float:
    """Pick the smallest threshold whose empirical FPR on the given data <= target."""
    thresholds = np.linspace(0.01, 0.99, 99)
    best = 0.5
    for t in thresholds:
        pred = (y_proba >= t).astype(int)
        tn = int(((pred == 0) & (y_true == 0)).sum())
        fp = int(((pred == 1) & (y_true == 0)).sum())
        fpr = fp / max(fp + tn, 1)
        if fpr <= target_fpr:
            best = float(t)
            break
    return best


def compute_metrics(y_true: np.ndarray, y_proba: np.ndarray,
                    settings: Optional[Settings] = None,
                    threshold: Optional[float] = None) -> Dict:
    settings = settings or get_settings()

    if threshold is None:
        threshold = _pick_operating_threshold(y_true, y_proba, target_fpr=0.01)

    y_pred = (y_proba >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    pr_auc = average_precision_score(y_true, y_proba) if y_true.sum() > 0 else 0.0
    try:
        roc_auc = roc_auc_score(y_true, y_proba)
    except ValueError:
        roc_auc = float("nan")
    fpr = fp / max(fp + tn, 1)
    fnr = fn / max(fn + tp, 1)
    brier = brier_score_loss(y_true, y_proba)

    # Business cost using configurable knobs.
    fp_cost = float(fp) * settings.fp_cost_per_tx
    fn_cost = float(fn) * settings.fn_cost_per_tx
    review_cost = 0.0  # reserved for a threshold band that maps to review
    expected_business_cost = fp_cost + fn_cost + review_cost

    # PR curve for the frontend to render + let the user pick their own threshold.
    prec_curve, rec_curve, thr_curve = precision_recall_curve(y_true, y_proba)
    # Down-sample the curve to at most 100 points.
    stride = max(1, len(prec_curve) // 100)
    pr_curve = [
        {"precision": float(prec_curve[i]), "recall": float(rec_curve[i]),
         "threshold": float(thr_curve[i]) if i < len(thr_curve) else 1.0}
        for i in range(0, len(prec_curve), stride)
    ]

    return {
        "threshold": float(threshold),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "pr_auc": float(pr_auc),
        "roc_auc": float(roc_auc),
        "fpr": float(fpr),
        "fnr": float(fnr),
        "brier": float(brier),
        "confusion_matrix": {
            "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
        },
        "business_cost": {
            "fp_cost_per_tx": settings.fp_cost_per_tx,
            "fn_cost_per_tx": settings.fn_cost_per_tx,
            "review_cost_per_tx": settings.review_cost_per_tx,
            "false_positive_cost": float(fp_cost),
            "false_negative_cost": float(fn_cost),
            "expected_business_cost": float(expected_business_cost),
        },
        "pr_curve": pr_curve,
    }
