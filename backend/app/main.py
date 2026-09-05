"""FastAPI entry point."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import (
    ai,
    audit,
    decisions,
    entities,
    health,
    investigations,
    metrics,
    overview,
    transactions,
)
from backend.app.config import get_settings
from backend.app.db.database import init_db
from backend.app.utils.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)

settings = get_settings()
init_db()

app = FastAPI(
    title="RiskLens AI",
    version="0.2.0",
    description="Autonomous Payment Risk Intelligence & Investigation Platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(overview.router, prefix=API_PREFIX)
app.include_router(transactions.router, prefix=API_PREFIX)
app.include_router(investigations.router, prefix=API_PREFIX)
app.include_router(ai.router, prefix=API_PREFIX)
app.include_router(decisions.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)
app.include_router(entities.router, prefix=API_PREFIX)
app.include_router(metrics.router, prefix=API_PREFIX)


@app.get("/")
def root() -> dict:
    return {
        "service": "risklens-ai",
        "version": app.version,
        "docs": "/docs",
        "api_prefix": API_PREFIX,
    }
