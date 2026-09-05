"""Re-evaluate the trained model on the held-out test set and pretty-print metrics.

Reads the CSV, rebuilds features (leakage-safe), loads the trained model,
computes calibrated probabilities on the TEST split only, and prints metrics.
Also refreshes `metrics.json` so the API surfaces the latest numbers.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from backend.app.config import get_settings
from backend.app.ml import evaluate, features, model as model_mod
from backend.app.utils.logging import configure_logging, get_logger

log = get_logger(__name__)


def main() -> None:
    configure_logging()
    settings = get_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="backend/artifacts/synthetic_payments.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.data, parse_dates=["ts"])
    feats = features.build_batch_features(df)
    test = feats[feats["split"] == "test"]
    if test.empty:
        raise SystemExit("No rows in the test split. Regenerate the dataset.")

    X_test, _ = features.encode_matrix(test[features.NUMERIC_FEATURES + features.CATEGORICAL_FEATURES])
    y_test = test["is_fraud_label"].astype(int).values

    loaded = model_mod.load_model()
    raw_p, cal_p = model_mod.predict_proba(loaded, X_test)
    metrics = evaluate.compute_metrics(y_test, cal_p, settings=settings)

    log.info(
        "Held-out test  precision=%.4f  recall=%.4f  f1=%.4f  PR-AUC=%.4f  FPR=%.4f  FNR=%.4f",
        metrics["precision"], metrics["recall"], metrics["f1"],
        metrics["pr_auc"], metrics["fpr"], metrics["fnr"],
    )
    log.info(
        "Business cost  FP=%.2f  FN=%.2f  expected=%.2f",
        metrics["business_cost"]["false_positive_cost"],
        metrics["business_cost"]["false_negative_cost"],
        metrics["business_cost"]["expected_business_cost"],
    )

    metrics_path = Path(settings.artifact_dir) / "metrics.json"
    existing = {}
    if metrics_path.exists():
        try:
            existing = json.loads(metrics_path.read_text())
        except json.JSONDecodeError:
            existing = {}
    existing["last_eval_at"] = datetime.utcnow().isoformat() + "Z"
    existing["primary"] = metrics
    metrics_path.write_text(json.dumps(existing, indent=2))
    log.info("Wrote refreshed metrics -> %s", metrics_path)


if __name__ == "__main__":
    main()
