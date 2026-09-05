"""Model wrapper that loads the trained artifact and exposes predict_proba
with an isotonic calibrator applied on top.

The trainer picks XGBoost when available; otherwise it falls back to
HistGradientBoostingClassifier. Both are tree ensembles so SHAP TreeExplainer
works for both when SHAP is installed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple

import joblib
import numpy as np

from backend.app.config import get_settings
from backend.app.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class LoadedModel:
    model: Any
    calibrator: Any               # sklearn IsotonicRegression
    feature_columns: list
    model_kind: str               # "xgboost" or "sklearn_hgb"
    model_version: str
    background: Optional[np.ndarray]


_LOADED: Optional[LoadedModel] = None


def artifact_paths() -> dict:
    root = Path(get_settings().artifact_dir)
    return {
        "model": root / "model.joblib",
        "calibrator": root / "calibrator.joblib",
        "columns": root / "feature_columns.joblib",
        "meta": root / "model_meta.joblib",
        "background": root / "shap_background.npy",
        "metrics": root / "metrics.json",
    }


def save_artifacts(model: Any, calibrator: Any, feature_columns: list, model_kind: str,
                   model_version: str, background: np.ndarray) -> None:
    paths = artifact_paths()
    joblib.dump(model, paths["model"])
    joblib.dump(calibrator, paths["calibrator"])
    joblib.dump(feature_columns, paths["columns"])
    joblib.dump({"kind": model_kind, "version": model_version}, paths["meta"])
    np.save(paths["background"], background)


def load_model(force_reload: bool = False) -> LoadedModel:
    global _LOADED
    if _LOADED is not None and not force_reload:
        return _LOADED

    paths = artifact_paths()
    if not paths["model"].exists():
        raise FileNotFoundError(
            f"Model artifact not found at {paths['model']}. "
            "Run: python -m backend.scripts.train_model"
        )

    model = joblib.load(paths["model"])
    calibrator = joblib.load(paths["calibrator"])
    feature_columns = joblib.load(paths["columns"])
    meta = joblib.load(paths["meta"])
    background = np.load(paths["background"]) if paths["background"].exists() else None

    _LOADED = LoadedModel(
        model=model,
        calibrator=calibrator,
        feature_columns=feature_columns,
        model_kind=meta["kind"],
        model_version=meta["version"],
        background=background,
    )
    log.info("Loaded model %s (%s) with %d features", _LOADED.model_version, _LOADED.model_kind, len(feature_columns))
    return _LOADED


def raw_probabilities(loaded: LoadedModel, X: np.ndarray) -> np.ndarray:
    if loaded.model_kind == "xgboost":
        import xgboost as xgb  # noqa: F401
        return loaded.model.predict_proba(X)[:, 1]
    return loaded.model.predict_proba(X)[:, 1]


def predict_proba(loaded: LoadedModel, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Return (raw_prob, calibrated_prob)."""
    raw = raw_probabilities(loaded, X)
    if loaded.calibrator is not None:
        cal = loaded.calibrator.predict(raw)
    else:
        cal = raw
    return raw, cal
