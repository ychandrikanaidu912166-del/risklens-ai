"""Historical behaviour comparison for a single customer.

Pulls the customer's prior transactions from the DB and computes a compact
snapshot the UI and the evidence engine both consume.
"""
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db import models
from backend.app.schemas.investigation import BehaviorSnapshot


def load_customer_history(db: Session, customer_id: str, before_ts=None) -> pd.DataFrame:
    stmt = select(models.Transaction).where(models.Transaction.customer_id == customer_id)
    if before_ts is not None:
        stmt = stmt.where(models.Transaction.ts < before_ts)
    rows = db.scalars(stmt.order_by(models.Transaction.ts)).all()
    if not rows:
        return pd.DataFrame(columns=[
            "tx_id", "ts", "customer_id", "merchant_id", "merchant_category",
            "amount", "device_id", "ip_hash", "ip_country", "customer_country",
            "channel", "auth_result", "hour", "day_of_week",
        ])
    return pd.DataFrame(
        [
            {
                "tx_id": r.tx_id, "ts": r.ts, "customer_id": r.customer_id,
                "merchant_id": r.merchant_id, "merchant_category": r.merchant_category,
                "amount": r.amount, "device_id": r.device_id, "ip_hash": r.ip_hash,
                "ip_country": r.ip_country, "customer_country": r.customer_country,
                "channel": r.channel, "auth_result": r.auth_result,
                "hour": r.hour, "day_of_week": r.day_of_week,
            }
            for r in rows
        ]
    )


def snapshot_from_history(history: pd.DataFrame, tx: dict) -> BehaviorSnapshot:
    if history.empty:
        return BehaviorSnapshot(
            n_prior_tx=0,
            mean_amount=None,
            std_amount=None,
            common_hours=[],
            common_countries=[],
            known_devices=[],
            amount_z_score=None,
            is_new_device=True,
            is_new_country=True,
            unusual_hour=False,
        )
    amounts = history["amount"].astype(float)
    mean_amount = float(amounts.mean())
    std_amount = float(amounts.std()) if len(amounts) >= 2 else None
    z = None
    if std_amount and std_amount > 0:
        z = float((tx["amount"] - mean_amount) / std_amount)

    hour_counts = history["hour"].value_counts()
    common_hours = [int(h) for h in hour_counts.head(6).index.tolist()]

    country_counts = history["ip_country"].value_counts()
    common_countries = [str(c) for c in country_counts.head(4).index.tolist()]

    known_devices = history["device_id"].dropna().unique().tolist()

    return BehaviorSnapshot(
        n_prior_tx=int(len(history)),
        mean_amount=mean_amount,
        std_amount=std_amount,
        common_hours=common_hours,
        common_countries=common_countries,
        known_devices=known_devices,
        amount_z_score=z,
        is_new_device=tx["device_id"] not in known_devices,
        is_new_country=tx["ip_country"] not in common_countries if common_countries else True,
        unusual_hour=(bool(common_hours) and tx["hour"] not in common_hours),
    )
