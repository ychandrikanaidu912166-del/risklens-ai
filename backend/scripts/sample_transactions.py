"""Print a handful of ready-to-POST sample transactions.

Each sample is picked from the generated dataset so that it references real
customers/merchants/devices whose history is already in the DB (after the
seeding step below).

Usage:
    python -m backend.scripts.sample_transactions               # print JSON to stdout
    python -m backend.scripts.sample_transactions --seed-db     # also load train+val+test
                                                                # rows into SQLite so
                                                                # customer history exists
                                                                # for scoring live tx.
"""
from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path

import pandas as pd

from backend.app.config import get_settings
from backend.app.db import models
from backend.app.db.database import init_db, session_scope
from backend.app.utils.logging import configure_logging, get_logger

log = get_logger(__name__)


def _row_to_tx_payload(row: pd.Series, offset_hours: int = 1) -> dict:
    """Turn a historical row into a NEW live transaction payload posted `offset_hours`
    after the last known historical activity for that customer."""
    ts = pd.to_datetime(row["ts"]) + timedelta(hours=offset_hours)
    return {
        "tx_id": f"LIVE-{row['tx_id']}",
        "ts": ts.isoformat(),
        "customer_id": row["customer_id"],
        "merchant_id": row["merchant_id"],
        "merchant_category": row["merchant_category"],
        "amount": float(row["amount"]),
        "currency": "INR",
        "device_id": row["device_id"],
        "ip_hash": row["ip_hash"],
        "ip_country": row["ip_country"],
        "customer_country": row["customer_country"],
        "channel": row.get("channel", "web"),
        "auth_result": row.get("auth_result", "success"),
    }


def _seed_db(csv_path: Path) -> None:
    log.info("Seeding SQLite with historical rows from %s ...", csv_path)
    df = pd.read_csv(csv_path, parse_dates=["ts"])

    init_db()

    with session_scope() as db:
        # Customers
        for cid, cdf in df.groupby("customer_id"):
            if db.get(models.Customer, cid) is None:
                db.add(models.Customer(
                    customer_id=cid,
                    country=cdf.iloc[0]["customer_country"],
                ))
        # Merchants
        for mid, mdf in df.groupby("merchant_id"):
            if db.get(models.Merchant, mid) is None:
                db.add(models.Merchant(
                    merchant_id=mid,
                    category=mdf.iloc[0]["merchant_category"],
                    risk_tier=int(mdf.iloc[0].get("risk_tier", 1)),
                ))
        # Devices
        for did in df["device_id"].unique():
            if db.get(models.Device, did) is None:
                db.add(models.Device(device_id=did))
        db.commit()

        # Transactions in bulk; skip if already present.
        existing_ids = set(x[0] for x in db.execute(
            models.Transaction.__table__.select().with_only_columns(models.Transaction.tx_id)
        ))
        to_insert = []
        for _, r in df.iterrows():
            if r["tx_id"] in existing_ids:
                continue
            to_insert.append({
                "tx_id": r["tx_id"],
                "ts": pd.to_datetime(r["ts"]).to_pydatetime(),
                "customer_id": r["customer_id"],
                "merchant_id": r["merchant_id"],
                "merchant_category": r["merchant_category"],
                "device_id": r["device_id"],
                "ip_hash": r["ip_hash"],
                "ip_country": r["ip_country"],
                "customer_country": r["customer_country"],
                "amount": float(r["amount"]),
                "currency": "INR",
                "channel": r.get("channel", "web"),
                "auth_result": r.get("auth_result", "success"),
                "hour": int(r["hour"]),
                "day_of_week": int(r["day_of_week"]),
                "is_fraud_label": int(r["is_fraud_label"]),
                "split": r.get("split", "train"),
            })
        if to_insert:
            db.execute(models.Transaction.__table__.insert(), to_insert)
        log.info("Seeded %d transactions.", len(to_insert))


def build_samples(csv_path: Path, k_each: int = 3) -> list[dict]:
    df = pd.read_csv(csv_path, parse_dates=["ts"])

    # We want samples that look "live": pick recent rows from the TEST split.
    test = df[df["split"] == "test"].copy()
    if test.empty:
        test = df.copy()

    frauds = test[test["is_fraud_label"] == 1].sort_values("ts").tail(k_each)
    legit = test[test["is_fraud_label"] == 0].sort_values("ts").tail(k_each)

    samples: list[dict] = []
    for _, r in legit.iterrows():
        samples.append(_row_to_tx_payload(r, offset_hours=2))
    for _, r in frauds.iterrows():
        samples.append(_row_to_tx_payload(r, offset_hours=2))
    return samples


def main() -> None:
    configure_logging()
    settings = get_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="backend/artifacts/synthetic_payments.csv")
    parser.add_argument("--seed-db", action="store_true", help="Also load historical rows into SQLite.")
    parser.add_argument("--k", type=int, default=3, help="Samples per class to emit.")
    parser.add_argument("--out", type=str, default="backend/artifacts/sample_transactions.json")
    args = parser.parse_args()

    csv_path = Path(args.data)

    if args.seed_db:
        _seed_db(csv_path)

    samples = build_samples(csv_path, k_each=args.k)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(samples, indent=2, default=str))
    log.info("Wrote %d sample payloads -> %s", len(samples), out)
    print(json.dumps(samples[:2], indent=2, default=str))
    print(f"\n... total {len(samples)} samples in {out}")


if __name__ == "__main__":
    main()
