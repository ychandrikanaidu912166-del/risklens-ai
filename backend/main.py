import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.config.settings import settings
from backend.app.database.session import engine, Base, SessionLocal
from backend.app.api.v1.router import api_router
from backend.app.database.models import TransactionModel
from backend.app.services.investigation_service import InvestigationService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Ensure database schema is created
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")

    # 2. Check if DB is empty; if so, auto-seed a representative batch for instant demo
    db = SessionLocal()
    try:
        tx_count = db.query(TransactionModel).count()
        if tx_count == 0:
            csv_path = "data/transactions.csv"
            if os.path.exists(csv_path):
                print(f"Auto-seeding initial transactions from {csv_path}...")
                import pandas as pd
                df = pd.read_csv(csv_path)
                # Take 300 transactions representing low, high, and critical risk
                sample_df = df.head(300)
                for _, row in sample_df.iterrows():
                    tx_dict = row.to_dict()
                    InvestigationService.score_and_process_transaction(tx_dict, db)
                print(f"Database seeded with {len(sample_df)} scored transactions.")
    except Exception as e:
        print(f"Warning during auto-seed: {e}")
    finally:
        db.close()

    yield
    print("Shutting down RiskLens AI application.")


app = FastAPI(
    title="RiskLens AI - Payment Risk Intelligence & Investigation Platform",
    description="Real-time payment fraud detection, customer behavioural baselines, structured evidence, and AI investigation platform.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
