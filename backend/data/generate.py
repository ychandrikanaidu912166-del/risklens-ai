"""Reproducible synthetic payment dataset generator.

The generator intentionally embeds realistic-but-noisy patterns for fraud:

  - amount outliers vs the customer's own baseline
  - rapid transaction bursts (velocity)
  - unusual hours for the customer
  - new device / new country
  - repeated auth failures leading up to a fraud
  - device-sharing rings (small groups of customers reusing a device_id)
  - IP-sharing across otherwise-unrelated customers

Legitimate transactions are the vast majority; fraud base rate defaults to ~4%.

No PII: identifiers are opaque strings; IPs are stored as hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List

import numpy as np
import pandas as pd

MERCHANT_CATEGORIES = [
    "grocery", "electronics", "travel", "gaming", "wallet_topup",
    "utilities", "food_delivery", "streaming", "jewellery", "crypto_gateway",
]

# Categories with a higher intrinsic risk tier (used both in features and evidence).
HIGH_RISK_CATEGORIES = {"crypto_gateway", "jewellery", "gaming"}

COUNTRIES = ["IN", "US", "AE", "SG", "GB", "DE", "RU", "NG", "BR", "ID"]

CHANNELS = ["web", "mobile", "pos", "api"]


def _hash_ip(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:24]


@dataclass
class GenConfig:
    n_customers: int = 1500
    n_merchants: int = 120
    n_days: int = 60
    tx_per_customer_mean: float = 55.0
    fraud_base_rate: float = 0.04
    seed: int = 42
    device_ring_count: int = 6      # small fraud rings that share devices
    device_ring_size: int = 8


def _make_customer_profiles(cfg: GenConfig, rng: np.random.Generator) -> pd.DataFrame:
    ids = [f"C{100000 + i}" for i in range(cfg.n_customers)]
    countries = rng.choice(COUNTRIES, size=cfg.n_customers, p=[0.55, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.03, 0.04, 0.03])
    baseline_amount = rng.lognormal(mean=6.2, sigma=0.6, size=cfg.n_customers)  # roughly 500 INR mode, long tail
    baseline_std = baseline_amount * rng.uniform(0.15, 0.45, size=cfg.n_customers)
    active_hours = [tuple(sorted(rng.choice(range(6, 23), size=rng.integers(3, 8), replace=False))) for _ in ids]
    home_device = [f"D{200000 + i}" for i in range(cfg.n_customers)]
    return pd.DataFrame(
        {
            "customer_id": ids,
            "customer_country": countries,
            "baseline_amount": baseline_amount,
            "baseline_std": baseline_std,
            "active_hours": active_hours,
            "home_device": home_device,
        }
    )


def _make_merchants(cfg: GenConfig, rng: np.random.Generator) -> pd.DataFrame:
    ids = [f"M{300000 + i}" for i in range(cfg.n_merchants)]
    categories = rng.choice(MERCHANT_CATEGORIES, size=cfg.n_merchants)
    risk_tier = np.array([3 if c in HIGH_RISK_CATEGORIES else int(rng.integers(1, 3)) for c in categories])
    return pd.DataFrame({"merchant_id": ids, "merchant_category": categories, "risk_tier": risk_tier})


def _sample_hour(active_hours: Iterable[int], rng: np.random.Generator, unusual: bool) -> int:
    if unusual:
        # Pick a graveyard-shift hour outside the active set.
        candidates = [h for h in range(24) if h not in set(active_hours)]
        candidates = [h for h in candidates if h < 6 or h > 22]
        if not candidates:
            candidates = [h for h in range(24) if h not in set(active_hours)]
        return int(rng.choice(candidates))
    return int(rng.choice(list(active_hours)))


def _generate_legit(profile: pd.Series, merchants: pd.DataFrame, ts: datetime, rng: np.random.Generator) -> dict:
    merchant = merchants.sample(1, random_state=int(rng.integers(0, 10**9))).iloc[0]

    # Most legit tx follow baseline; some legit tx are unusual (vacations, big purchases).
    if rng.random() < 0.08:
        # Occasional legit outlier: 2-6x baseline amount.
        amount = float(max(1.0, profile["baseline_amount"] * rng.uniform(2.0, 6.0)))
    else:
        amount = float(max(1.0, rng.normal(profile["baseline_amount"], profile["baseline_std"])))

    # Legit customers occasionally transact at unusual hours.
    unusual_h = rng.random() < 0.10
    hour = _sample_hour(profile["active_hours"], rng, unusual=unusual_h)
    ts = ts.replace(hour=hour, minute=int(rng.integers(0, 60)), second=int(rng.integers(0, 60)))

    # Legit customers occasionally use new devices (new phone, browser reset).
    if rng.random() < 0.06:
        device_id = f"DL{int(rng.integers(0, 10**7))}"
    else:
        device_id = profile["home_device"]

    # Legit customers occasionally travel — IP from another country.
    if rng.random() < 0.05:
        ip_country = str(rng.choice([c for c in COUNTRIES if c != profile["customer_country"]]))
        ip_hash = _hash_ip(f"{profile['customer_id']}-travel-{ts.timestamp()}")
    else:
        ip_country = profile["customer_country"]
        ip_hash = _hash_ip(f"{profile['customer_id']}-home")

    # Legit tx can very occasionally have an auth failure (typo, network).
    auth = "failure" if rng.random() < 0.03 else "success"

    return {
        "ts": ts,
        "customer_id": profile["customer_id"],
        "merchant_id": merchant["merchant_id"],
        "merchant_category": merchant["merchant_category"],
        "amount": round(amount, 2),
        "currency": "INR",
        "device_id": device_id,
        "ip_hash": ip_hash,
        "ip_country": ip_country,
        "customer_country": profile["customer_country"],
        "channel": str(rng.choice(CHANNELS, p=[0.35, 0.5, 0.1, 0.05])),
        "auth_result": auth,
        "is_fraud_label": 0,
    }


def _generate_fraud(profile: pd.Series, merchants: pd.DataFrame, ts: datetime, rng: np.random.Generator,
                    ring_device: str | None = None, ring_ip: str | None = None) -> dict:
    # A quarter of fraud events look like "friendly fraud" or account takeover
    # with much subtler footprint — meant to be genuinely hard for the model.
    stealthy = rng.random() < 0.25

    # Fraud tilts toward high-risk merchants but not exclusively.
    if not stealthy and rng.random() < 0.55:
        pool = merchants[merchants["merchant_category"].isin(HIGH_RISK_CATEGORIES)]
        merchant = pool.sample(1, random_state=int(rng.integers(0, 10**9))).iloc[0]
    else:
        merchant = merchants.sample(1, random_state=int(rng.integers(0, 10**9))).iloc[0]

    if stealthy:
        # Modest multiplier so the amount doesn't scream fraud.
        multiplier = float(rng.uniform(0.8, 2.5))
    else:
        multiplier = float(rng.uniform(2.0, 10.0))
    amount = float(max(50.0, profile["baseline_amount"] * multiplier + rng.normal(0, profile["baseline_std"])))

    hour = _sample_hour(profile["active_hours"], rng, unusual=(not stealthy) and (rng.random() < 0.6))
    ts = ts.replace(hour=hour, minute=int(rng.integers(0, 60)), second=int(rng.integers(0, 60)))

    if stealthy:
        # Use customer's own device / home IP — hard case.
        device_id = profile["home_device"] if rng.random() < 0.6 else f"DX{int(rng.integers(0, 10**7))}"
        ip_country = profile["customer_country"] if rng.random() < 0.6 else str(rng.choice(
            [c for c in COUNTRIES if c != profile["customer_country"]]))
    else:
        device_id = ring_device if ring_device else f"DX{int(rng.integers(0, 10**7))}"
        if rng.random() < 0.75:
            ip_country = str(rng.choice([c for c in COUNTRIES if c != profile["customer_country"]]))
        else:
            ip_country = profile["customer_country"]
    ip_hash = ring_ip if ring_ip else _hash_ip(f"{device_id}-{ts.timestamp()}")

    if stealthy:
        auth = str(rng.choice(["success", "failure"], p=[0.8, 0.2]))
    else:
        auth = str(rng.choice(["failure", "success", "3ds_fail", "success"], p=[0.25, 0.4, 0.2, 0.15]))

    return {
        "ts": ts,
        "customer_id": profile["customer_id"],
        "merchant_id": merchant["merchant_id"],
        "merchant_category": merchant["merchant_category"],
        "amount": round(amount, 2),
        "currency": "INR",
        "device_id": device_id,
        "ip_hash": ip_hash,
        "ip_country": ip_country,
        "customer_country": profile["customer_country"],
        "channel": str(rng.choice(CHANNELS, p=[0.5, 0.3, 0.05, 0.15])),
        "auth_result": auth,
        "is_fraud_label": 1,
    }


def generate(cfg: GenConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)
    random.seed(cfg.seed)

    customers = _make_customer_profiles(cfg, rng)
    merchants = _make_merchants(cfg, rng)

    start = datetime(2025, 1, 1)
    rows: List[dict] = []

    # 1. Baseline legit + individual fraud events per customer.
    for _, profile in customers.iterrows():
        n_tx = max(5, int(rng.normal(cfg.tx_per_customer_mean, cfg.tx_per_customer_mean * 0.35)))
        for _ in range(n_tx):
            day = int(rng.integers(0, cfg.n_days))
            ts = start + timedelta(days=day)
            is_fraud = rng.random() < cfg.fraud_base_rate
            if is_fraud:
                row = _generate_fraud(profile, merchants, ts, rng)
                rows.append(row)
                # 40% of fraud events come with a small burst; the rest are singletons.
                if rng.random() < 0.4:
                    for _ in range(int(rng.integers(1, 3))):
                        burst_ts = ts + timedelta(minutes=int(rng.integers(1, 55)))
                        burst = _generate_fraud(profile, merchants, burst_ts, rng)
                        rows.append(burst)
            else:
                rows.append(_generate_legit(profile, merchants, ts, rng))

    # 2. Device-sharing rings — small groups of customers reusing a shared device+IP.
    for r in range(cfg.device_ring_count):
        ring_device = f"DR{r:03d}"
        ring_ip = _hash_ip(f"ring-{r}")
        ring_members = customers.sample(cfg.device_ring_size, random_state=cfg.seed + r)
        for _, profile in ring_members.iterrows():
            for _ in range(int(rng.integers(2, 6))):
                day = int(rng.integers(0, cfg.n_days))
                ts = start + timedelta(days=day)
                rows.append(_generate_fraud(profile, merchants, ts, rng, ring_device=ring_device, ring_ip=ring_ip))

    df = pd.DataFrame(rows)
    df = df.sort_values("ts").reset_index(drop=True)
    df["tx_id"] = [f"T{1_000_000 + i}" for i in range(len(df))]
    df["hour"] = df["ts"].dt.hour
    df["day_of_week"] = df["ts"].dt.dayofweek

    # Merge risk_tier onto rows for downstream feature parity.
    df = df.merge(merchants[["merchant_id", "risk_tier"]], on="merchant_id", how="left")

    ordered = [
        "tx_id", "ts", "customer_id", "merchant_id", "merchant_category", "risk_tier",
        "amount", "currency", "device_id", "ip_hash", "ip_country", "customer_country",
        "channel", "auth_result", "hour", "day_of_week", "is_fraud_label",
    ]
    return df[ordered]


def add_time_based_split(df: pd.DataFrame, train_frac: float = 0.70, val_frac: float = 0.15) -> pd.DataFrame:
    """Assign train/val/test by TIME. Random splits leak future customer state."""
    df = df.sort_values("ts").reset_index(drop=True)
    n = len(df)
    n_train = int(n * train_frac)
    n_val = int(n * val_frac)
    split = np.array(["train"] * n_train + ["val"] * n_val + ["test"] * (n - n_train - n_val))
    df["split"] = split
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic payments dataset.")
    parser.add_argument("--out", type=str, default="backend/artifacts/synthetic_payments.csv")
    parser.add_argument("--customers", type=int, default=1500)
    parser.add_argument("--merchants", type=int, default=120)
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cfg = GenConfig(
        n_customers=args.customers,
        n_merchants=args.merchants,
        n_days=args.days,
        seed=args.seed,
    )
    df = generate(cfg)
    df = add_time_based_split(df)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    print(f"Rows: {len(df):,}")
    print(f"Fraud rate: {df['is_fraud_label'].mean():.4f}")
    print(df["split"].value_counts().to_string())
    print(f"Written: {out}")


if __name__ == "__main__":
    main()
