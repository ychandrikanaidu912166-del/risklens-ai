from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    transactions,
    investigations,
    metrics,
    simulation,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(transactions.router, prefix="/api/v1", tags=["Transactions"])
api_router.include_router(investigations.router, prefix="/api/v1", tags=["Investigations"])
api_router.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
api_router.include_router(simulation.router, prefix="/api/v1", tags=["Simulation"])
