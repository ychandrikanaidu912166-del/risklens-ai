import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database.session import SessionLocal, Base, engine
from backend.app.database.models import TransactionModel, InvestigationModel
from backend.app.services.investigation_service import InvestigationService


def seed_database(limit: int = 350):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    csv_path = "data/transactions.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist. Run python data/generate_transactions.py first.")
        return

    df = pd.read_csv(csv_path)
    print(f"Seeding database with {limit} transactions from {csv_path}...")

    # Select representative mix: fraud and non-fraud
    fraud_df = df[df["is_fraud"] == 1].head(50)
    normal_df = df[df["is_fraud"] == 0].head(limit - 50)
    combined = pd.concat([fraud_df, normal_df]).sample(frac=1, random_state=42).reset_index(drop=True)

    count = 0
    for _, row in combined.iterrows():
        tx_dict = row.to_dict()
        try:
            InvestigationService.score_and_process_transaction(tx_dict, db)
            count += 1
            if count % 50 == 0:
                print(f"Scored and seeded {count}/{len(combined)} transactions...")
        except Exception as e:
            print(f"Error seeding transaction {tx_dict.get('transaction_id')}: {e}")

    total_in_db = db.query(TransactionModel).count()
    total_inv = db.query(InvestigationModel).count()
    crit_count = db.query(InvestigationModel).filter(InvestigationModel.risk_level == "CRITICAL").count()
    high_count = db.query(InvestigationModel).filter(InvestigationModel.risk_level == "HIGH").count()
    med_count = db.query(InvestigationModel).filter(InvestigationModel.risk_level == "MEDIUM").count()
    low_count = db.query(InvestigationModel).filter(InvestigationModel.risk_level == "LOW").count()

    print("\nDatabase Seeding Complete:")
    print(f"Total Transactions in DB: {total_in_db}")
    print(f"Total Investigations in DB: {total_inv}")
    print(f"Risk Breakdown: Critical={crit_count}, High={high_count}, Medium={med_count}, Low={low_count}")
    db.close()


if __name__ == "__main__":
    seed_database()
