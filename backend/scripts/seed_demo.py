"""Seed the analyst queue with a broader mix of live transactions.

Pulls a stratified sample from the historical CSV so the Overview dashboard
shows all four risk bands populated. Uses the real /score pipeline via the
DB session — never fabricates scores.
"""
from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path

import pandas as pd

from backend.app.db.database import init_db, session_scope
from backend.app.risk import engine
from backend.app.schemas.transaction import TransactionIn
from backend.app.utils.logging import configure_logging, get_logger

log = get_logger(__name__)


def _tx_from_row(row: pd.Series, tx_id: str, ts_offset_hours: int) -> TransactionIn:
    return TransactionIn(
        tx_id=tx_id,
        ts=(pd.to_datetime(row["ts"]) + timedelta(hours=ts_offset_hours)).to_pydatetime(),
        customer_id=row["customer_id"],
        merchant_id=row["merchant_id"],
        merchant_category=row["merchant_category"],
        amount=float(row["amount"]),
        currency="INR",
        device_id=row["device_id"],
        ip_hash=row["ip_hash"],
        ip_country=row["ip_country"],
        customer_country=row["customer_country"],
        channel=row.get("channel", "web"),
        auth_result=row.get("auth_result", "success"),
    )


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="backend/artifacts/synthetic_payments.csv")
    parser.add_argument("--count", type=int, default=60,
                        help="How many live transactions to score in total.")
    args = parser.parse_args()

    csv_path = Path(args.data)
    if not csv_path.exists():
        raise SystemExit(f"Dataset missing: {csv_path}. Run backend.data.generate first.")

    df = pd.read_csv(csv_path, parse_dates=["ts"])
    test = df[df["split"] == "test"].sort_values("ts")
    frauds = test[test["is_fraud_label"] == 1]
    legits = test[test["is_fraud_label"] == 0]

    n_fraud = min(len(frauds), max(1, args.count // 3))
    n_legit = args.count - n_fraud
    pick = pd.concat([
        frauds.sample(n=n_fraud, random_state=42),
        legits.sample(n=min(len(legits), n_legit), random_state=42),
    ]).sort_values("ts").reset_index(drop=True)

    init_db()
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    with session_scope() as db:
        for i, row in pick.iterrows():
            tx_id = f"LIVE-DEMO-{i:04d}"
            tx = _tx_from_row(row, tx_id, ts_offset_hours=6)
            try:
                result = engine.score_transaction(db, tx, persist=True)
                counts[result.risk_level] += 1
            except Exception as exc:  # noqa: BLE001
                log.warning("Failed to score %s: %s", tx_id, exc)
    log.info("Seeded live scored transactions: %s", counts)
    print(counts)


if __name__ == "__main__":
    main()
