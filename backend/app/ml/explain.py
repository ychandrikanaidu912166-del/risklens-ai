"""SHAP explanation with a dependency-free fallback."""
from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from backend.app.ml.model import LoadedModel


def _try_shap(loaded: LoadedModel, X: np.ndarray) -> Optional[np.ndarray]:
    try:
        import shap  # noqa: WPS433
    except Exception:
        return None
    try:
        explainer = shap.TreeExplainer(loaded.model)
        sv = explainer.shap_values(X)
        # xgboost returns np.ndarray; sklearn GBDT via shap sometimes returns a list
        if isinstance(sv, list):
            sv = sv[1] if len(sv) > 1 else sv[0]
        return sv
    except Exception:
        return None


def _fallback_contributions(loaded: LoadedModel, X: np.ndarray) -> np.ndarray:
    """Feature-importance × standardized-deviation from the background sample.

    This is coarser than SHAP but honest: it credits features that (a) the
    model considered important and (b) differ meaningfully from typical values.
    """
    if loaded.background is None or loaded.background.size == 0:
        bg_mean = np.zeros(X.shape[1])
        bg_std = np.ones(X.shape[1])
    else:
        bg_mean = loaded.background.mean(axis=0)
        bg_std = loaded.background.std(axis=0)
        bg_std[bg_std == 0] = 1.0

    importances = None
    m = loaded.model
    if hasattr(m, "feature_importances_"):
        importances = np.asarray(m.feature_importances_, dtype=float)
    if importances is None or importances.shape[0] != X.shape[1]:
        importances = np.ones(X.shape[1])

    z = (X - bg_mean) / bg_std
    return z * importances  # signed contribution proxy


def top_k_contributions(loaded: LoadedModel, X: np.ndarray, k: int = 8) -> Tuple[List[Tuple[str, float, float]], str]:
    """Return [(feature_name, feature_value, contribution)] sorted by |contribution|."""
    assert X.shape[0] == 1, "top_k_contributions expects a single-row matrix"

    sv = _try_shap(loaded, X)
    method = "shap"
    if sv is None:
        sv = _fallback_contributions(loaded, X)
        method = "fallback"

    row = sv[0] if sv.ndim == 2 else sv
    values = X[0]
    order = np.argsort(-np.abs(row))[:k]
    out = []
    for i in order:
        out.append((loaded.feature_columns[i], float(values[i]), float(row[i])))
    return out, method
