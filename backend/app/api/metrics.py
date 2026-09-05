"""Model metrics endpoint — surfaces the last held-out evaluation."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.app.config import get_settings

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/model")
def model_metrics() -> dict:
    path = Path(get_settings().artifact_dir) / "metrics.json"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="metrics.json not found. Run: python -m backend.scripts.train_model",
        )
    return json.loads(path.read_text())
