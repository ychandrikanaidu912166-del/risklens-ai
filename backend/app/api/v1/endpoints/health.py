from fastapi import APIRouter
from backend.app.config.settings import settings
from ml.models.predictor import predictor

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RiskLens AI Payment Risk Intelligence",
        "version": "1.0.0",
        "ml_model_version": predictor.model_version,
        "environment": settings.ENVIRONMENT,
        "database": "connected",
        "ai_engine": "Gemini-1.5-Flash (configured)" if settings.GEMINI_API_KEY else "Deterministic Local Fallback",
    }
