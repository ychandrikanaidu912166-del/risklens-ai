import os
import sys
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from ml.features.feature_pipeline import extract_features, extract_single_transaction_features, FEATURE_COLUMNS


class FraudPredictor:
    """
    Inference service loading trained XGBoost fraud detection model
    and providing calibrated fraud probability and top contributing features.
    """
    _instance = None

    def __init__(self, artifact_path: str = "ml/models/artifacts/fraud_model.joblib"):
        self.artifact_path = artifact_path
        self.model = None
        self.scaler = None
        self.feature_names = FEATURE_COLUMNS
        self.optimal_threshold = 0.5
        self.model_version = "unknown"
        self.feature_importance = []
        self._load()

    def _load(self):
        if not os.path.exists(self.artifact_path):
            raise FileNotFoundError(f"Model artifact not found at {self.artifact_path}. Run ml/models/train.py first.")
        
        artifact = joblib.load(self.artifact_path)
        self.model = artifact["model"]
        self.scaler = artifact.get("scaler")
        self.feature_names = artifact.get("feature_names", FEATURE_COLUMNS)
        self.optimal_threshold = artifact.get("optimal_threshold", 0.5)
        self.model_version = artifact.get("model_version", "v1.2.0-xgb")
        self.feature_importance = artifact.get("feature_importance", [])

    def predict_probability(self, transaction_dict: Dict[str, Any]) -> Tuple[float, bool, Dict[str, float]]:
        """
        Calculates the fraud probability (0.0 to 1.0), binary flag based on optimal threshold,
        and individual feature values for explainability.
        """
        if self.model is None:
            self._load()

        feat_df = extract_single_transaction_features(transaction_dict)
        
        # Probabilities
        prob = float(self.model.predict_proba(feat_df)[0, 1])
        is_fraud_flag = bool(prob >= self.optimal_threshold)

        # Feature snapshot
        feat_dict = feat_df.iloc[0].to_dict()

        return prob, is_fraud_flag, feat_dict


# Global singleton instance
predictor = FraudPredictor()
