"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="RISKLENS_",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    db_url: str = "sqlite:///./backend/artifacts/risklens.db"
    artifact_dir: str = "./backend/artifacts"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Business cost knobs — used by the evaluator and the API.
    fp_cost_per_tx: float = 12.0        # Cost of falsely blocking a legit tx (friction + churn proxy).
    fn_cost_per_tx: float = 250.0       # Cost of missing a fraud tx (chargeback + fee proxy).
    review_cost_per_tx: float = 2.5     # Cost of a manual review touch.

    # Decision thresholds. These map risk score -> action band. Overridable at runtime.
    threshold_low_max: int = 29
    threshold_medium_max: int = 59
    threshold_high_max: int = 79

    # Model config
    random_seed: int = 42
    model_version: str = "gbdt-v1"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def artifact_path(self) -> Path:
        p = Path(self.artifact_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
