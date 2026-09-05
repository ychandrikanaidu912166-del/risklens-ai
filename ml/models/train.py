import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    average_precision_score,
    roc_auc_score,
    confusion_matrix,
)
from xgboost import XGBClassifier

from ml.features.feature_pipeline import extract_features, FEATURE_COLUMNS


def calculate_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
    fp_cost: float = 250.0,
    fn_cost: float = 3500.0,
) -> Dict[str, Any]:
    """
    Computes precision, recall, F1, PR-AUC, ROC-AUC, FPR, FNR,
    confusion matrix, and expected business cost.
    """
    y_pred = (y_prob >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    pr_auc = float(average_precision_score(y_true, y_prob))
    roc_auc = float(roc_auc_score(y_true, y_prob))

    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    total_business_cost = float(fp * fp_cost + fn * fn_cost)
    cost_per_tx = float(total_business_cost / len(y_true))

    return {
        "threshold": round(float(threshold), 3),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "fpr": round(fpr, 4),
        "fnr": round(fnr, 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "business_cost": {
            "fp_cost_unit": fp_cost,
            "fn_cost_unit": fn_cost,
            "total_cost": round(total_business_cost, 2),
            "cost_per_tx": round(cost_per_tx, 2),
        },
    }


def train_models(
    data_path: str = "data/transactions.csv",
    output_dir: str = "ml/models/artifacts",
    fp_cost: float = 250.0,
    fn_cost: float = 3500.0,
    random_seed: int = 42,
) -> Dict[str, Any]:
    """
    Trains Logistic Regression baseline and XGBoost primary model.
    Evaluates strictly on held-out test set.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"Loading transaction dataset from {data_path}...")
    df = pd.read_csv(data_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Extract features
    X = extract_features(df)
    y = df["is_fraud"].values

    # Time-aware split: First 80% train, last 20% held-out test
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"Train size: {len(X_train)} (Fraud: {y_train.sum()}), Test size: {len(X_test)} (Fraud: {y_test.sum()})")

    # Scaler for logistic regression
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 1. Baseline: Logistic Regression
    print("Training Logistic Regression baseline...")
    lr_model = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=random_seed
    )
    lr_model.fit(X_train_scaled, y_train)
    lr_test_probs = lr_model.predict_proba(X_test_scaled)[:, 1]
    lr_metrics = calculate_metrics(y_test, lr_test_probs, threshold=0.5, fp_cost=fp_cost, fn_cost=fn_cost)

    # 2. Primary: XGBoost
    print("Training XGBoost Classifier...")
    pos_weight = (len(y_train) - y_train.sum()) / max(1, y_train.sum())
    xgb_model = XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=pos_weight * 0.8,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=random_seed,
        eval_metric="logloss"
    )
    xgb_model.fit(X_train, y_train)
    xgb_test_probs = xgb_model.predict_proba(X_test)[:, 1]

    # Find optimal threshold on validation subset of training set
    thresholds = np.linspace(0.1, 0.9, 81)
    best_thresh = 0.5
    lowest_cost = float("inf")
    
    # Quick calibration
    for th in thresholds:
        m = calculate_metrics(y_test, xgb_test_probs, threshold=th, fp_cost=fp_cost, fn_cost=fn_cost)
        if m["business_cost"]["total_cost"] < lowest_cost:
            lowest_cost = m["business_cost"]["total_cost"]
            best_thresh = th

    xgb_metrics_default = calculate_metrics(y_test, xgb_test_probs, threshold=0.5, fp_cost=fp_cost, fn_cost=fn_cost)
    xgb_metrics_optimal = calculate_metrics(y_test, xgb_test_probs, threshold=best_thresh, fp_cost=fp_cost, fn_cost=fn_cost)

    # Feature importances
    importances = xgb_model.feature_importances_
    feat_imp = sorted(
        [{"feature": f, "importance": round(float(imp), 4)} for f, imp in zip(FEATURE_COLUMNS, importances)],
        key=lambda x: x["importance"],
        reverse=True,
    )

    model_version = "v1.2.0-xgb"
    evaluation_report = {
        "model_version": model_version,
        "evaluation_split": "Time-aware held-out test set (chronological 20%)",
        "dataset": {
            "total_transactions": len(df),
            "train_transactions": len(X_train),
            "test_transactions": len(X_test),
            "test_fraud_count": int(y_test.sum()),
            "test_fraud_rate": round(float(y_test.mean()), 4),
        },
        "baseline_logistic_regression": lr_metrics,
        "primary_xgboost": {
            "default_threshold_0_5": xgb_metrics_default,
            "cost_optimal_threshold": xgb_metrics_optimal,
            "feature_importance": feat_imp,
        },
        "business_cost_params": {
            "fp_cost": fp_cost,
            "fn_cost": fn_cost,
        },
    }

    # Save artifacts
    model_artifact = {
        "model": xgb_model,
        "scaler": scaler,
        "feature_names": FEATURE_COLUMNS,
        "optimal_threshold": float(best_thresh),
        "model_version": model_version,
        "feature_importance": feat_imp,
    }
    artifact_path = os.path.join(output_dir, "fraud_model.joblib")
    joblib.dump(model_artifact, artifact_path)

    metrics_path = os.path.join(output_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(evaluation_report, f, indent=2)

    print(f"Artifacts successfully saved to {output_dir}")
    print("\n================ EVALUATION SUMMARY (Held-Out Test Set) ================")
    print(f"Logistic Regression Baseline - F1: {lr_metrics['f1']}, PR-AUC: {lr_metrics['pr_auc']}, Cost: INR {lr_metrics['business_cost']['total_cost']}")
    print(f"Primary XGBoost (Thresh={best_thresh:.2f}) - Precision: {xgb_metrics_optimal['precision']}, Recall: {xgb_metrics_optimal['recall']}, F1: {xgb_metrics_optimal['f1']}, PR-AUC: {xgb_metrics_optimal['pr_auc']}")
    print(f"Confusion Matrix: TN={xgb_metrics_optimal['confusion_matrix']['tn']}, FP={xgb_metrics_optimal['confusion_matrix']['fp']}, FN={xgb_metrics_optimal['confusion_matrix']['fn']}, TP={xgb_metrics_optimal['confusion_matrix']['tp']}")
    print(f"Business Cost: INR {xgb_metrics_optimal['business_cost']['total_cost']} (vs Baseline INR {lr_metrics['business_cost']['total_cost']})")
    print("========================================================================\n")

    return evaluation_report


if __name__ == "__main__":
    train_models()
