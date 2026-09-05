"""FastAPI entry point."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import health, investigations, metrics, transactions
from backend.app.config import get_settings
from backend.app.db.database import init_db
from backend.app.utils.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)

settings = get_settings()
init_db()

app = FastAPI(
    title="RiskLens AI",
    version="0.1.0",
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
app.include_router(transactions.router, prefix=API_PREFIX)
app.include_router(investigations.router, prefix=API_PREFIX)
app.include_router(metrics.router, prefix=API_PREFIX)


@app.get("/")
def root() -> dict:
    return {
        "service": "risklens-ai",
        "version": app.version,
        "docs": "/docs",
        "api_prefix": API_PREFIX,
    }
