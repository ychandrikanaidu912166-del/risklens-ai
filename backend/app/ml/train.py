"""Model training pipeline.

Steps:
  1. Load synthetic dataset.
  2. Build leakage-safe features.
  3. Time-based train/val/test split (already stamped in the CSV).
  4. Fit baseline (LogisticRegression) and primary (XGBoost or HistGBDT).
  5. Fit isotonic calibrator on validation.
  6. Evaluate on held-out test; write metrics.json.
  7. Persist all artifacts.

Reproducible: seeded end-to-end.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Tuple

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from backend.app.config import get_settings
from backend.app.ml import evaluate, features, model as model_mod
from backend.app.utils.logging import configure_logging, get_logger

log = get_logger(__name__)


def _train_primary(X_train: np.ndarray, y_train: np.ndarray, seed: int) -> Tuple[Any, str]:
    """Try XGBoost first; fall back to sklearn's HistGBDT if XGB is unavailable."""
    try:
        import xgboost as xgb

        pos = float((y_train == 1).sum())
        neg = float((y_train == 0).sum())
        spw = max(1.0, neg / max(pos, 1.0))

        clf = xgb.XGBClassifier(
            n_estimators=350,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            scale_pos_weight=spw,
            eval_metric="aucpr",
            tree_method="hist",
            random_state=seed,
            n_jobs=-1,
        )
        clf.fit(X_train, y_train)
        log.info("Trained XGBoost primary model (scale_pos_weight=%.2f)", spw)
        return clf, "xgboost"
    except Exception as exc:  # noqa: BLE001
        log.warning("XGBoost unavailable (%s); falling back to HistGradientBoostingClassifier", exc)
        clf = HistGradientBoostingClassifier(
            max_depth=None,
            max_iter=350,
            learning_rate=0.08,
            l2_regularization=1.0,
            random_state=seed,
        )
        clf.fit(X_train, y_train)
        return clf, "sklearn_hgb"


def _train_baseline(X_train: np.ndarray, y_train: np.ndarray, seed: int) -> Any:
    scaler = StandardScaler(with_mean=False)
    Xs = scaler.fit_transform(X_train)
    lr = LogisticRegression(max_iter=500, class_weight="balanced", random_state=seed, n_jobs=-1)
    lr.fit(Xs, y_train)
    return {"scaler": scaler, "clf": lr}


def _predict_baseline(bundle: dict, X: np.ndarray) -> np.ndarray:
    Xs = bundle["scaler"].transform(X)
    return bundle["clf"].predict_proba(Xs)[:, 1]


def main() -> None:
    configure_logging()
    settings = get_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="backend/artifacts/synthetic_payments.csv")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {data_path}. Run: python -m backend.data.generate"
        )

    log.info("Loading dataset from %s", data_path)
    df = pd.read_csv(data_path, parse_dates=["ts"])
    log.info("Rows: %d  |  fraud rate: %.4f", len(df), df["is_fraud_label"].mean())

    log.info("Building features with strict past-only rolling windows...")
    feats = features.build_batch_features(df)

    train_mask = feats["split"] == "train"
    val_mask = feats["split"] == "val"
    test_mask = feats["split"] == "test"

    X_train_raw = feats.loc[train_mask, features.NUMERIC_FEATURES + features.CATEGORICAL_FEATURES]
    X_val_raw = feats.loc[val_mask, features.NUMERIC_FEATURES + features.CATEGORICAL_FEATURES]
    X_test_raw = feats.loc[test_mask, features.NUMERIC_FEATURES + features.CATEGORICAL_FEATURES]

    X_train, cols = features.encode_matrix(X_train_raw)
    X_val, _ = features.encode_matrix(X_val_raw)
    X_test, _ = features.encode_matrix(X_test_raw)

    y_train = feats.loc[train_mask, "is_fraud_label"].astype(int).values
    y_val = feats.loc[val_mask, "is_fraud_label"].astype(int).values
    y_test = feats.loc[test_mask, "is_fraud_label"].astype(int).values

    log.info("Train %s  Val %s  Test %s", X_train.shape, X_val.shape, X_test.shape)

    # --- baseline
    baseline_bundle = _train_baseline(X_train, y_train, settings.random_seed)
    baseline_val = _predict_baseline(baseline_bundle, X_val)
    baseline_test = _predict_baseline(baseline_bundle, X_test)
    baseline_metrics = evaluate.compute_metrics(y_test, baseline_test, settings=settings)
    log.info("Baseline (LR) test PR-AUC=%.4f  ROC-AUC=%.4f", baseline_metrics["pr_auc"], baseline_metrics["roc_auc"])

    # --- primary
    primary, kind = _train_primary(X_train, y_train, settings.random_seed)
    raw_val = primary.predict_proba(X_val)[:, 1]
    raw_test = primary.predict_proba(X_test)[:, 1]

    # --- isotonic calibrator on validation
    log.info("Fitting isotonic calibrator on validation set...")
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(raw_val, y_val)
    cal_test = calibrator.predict(raw_test)

    # --- metrics on held-out test
    primary_metrics = evaluate.compute_metrics(y_test, cal_test, settings=settings)
    log.info(
        "Primary (%s) test  precision=%.4f  recall=%.4f  f1=%.4f  PR-AUC=%.4f  FPR=%.4f",
        kind,
        primary_metrics["precision"], primary_metrics["recall"], primary_metrics["f1"],
        primary_metrics["pr_auc"], primary_metrics["fpr"],
    )

    # --- SHAP background sample (small; supports the explainer at inference)
    rng = np.random.default_rng(settings.random_seed)
    bg_idx = rng.choice(X_train.shape[0], size=min(200, X_train.shape[0]), replace=False)
    background = X_train[bg_idx]

    # --- persist
    model_mod.save_artifacts(
        model=primary,
        calibrator=calibrator,
        feature_columns=cols,
        model_kind=kind,
        model_version=settings.model_version,
        background=background,
    )

    metrics_payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "model_version": settings.model_version,
        "model_kind": kind,
        "dataset_rows": int(len(df)),
        "fraud_rate": float(df["is_fraud_label"].mean()),
        "split_sizes": {
            "train": int(train_mask.sum()),
            "val": int(val_mask.sum()),
            "test": int(test_mask.sum()),
        },
        "primary": primary_metrics,
        "baseline": baseline_metrics,
        "feature_columns": cols,
    }

    metrics_path = Path(settings.artifact_dir) / "metrics.json"
    metrics_path.write_text(json.dumps(metrics_payload, indent=2))
    log.info("Wrote metrics -> %s", metrics_path)
    print(json.dumps(metrics_payload["primary"], indent=2))


if __name__ == "__main__":
    main()
