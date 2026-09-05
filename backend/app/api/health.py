"""Health endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from backend.app.ml import model as model_mod

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    try:
        loaded = model_mod.load_model()
        model_info = {
            "model_version": loaded.model_version,
            "model_kind": loaded.model_kind,
            "n_features": len(loaded.feature_columns),
        }
        model_ok = True
    except FileNotFoundError as exc:
        model_info = {"error": str(exc)}
        model_ok = False

    return {
        "status": "ok" if model_ok else "degraded",
        "model_ok": model_ok,
        "model": model_info,
    }
