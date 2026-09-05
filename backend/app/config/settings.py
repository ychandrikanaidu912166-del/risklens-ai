import os
import json
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env file from project root or backend dir
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))


class Settings(BaseModel):
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))

    DATABASE_URL: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./risklens.db"))

    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

    MODEL_DIR: str = Field(default_factory=lambda: os.getenv("MODEL_DIR", "ml/models/artifacts"))
    FP_COST: float = Field(default_factory=lambda: float(os.getenv("FP_COST", "250.0")))
    FN_COST: float = Field(default_factory=lambda: float(os.getenv("FN_COST", "3500.0")))

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]


settings = Settings()
