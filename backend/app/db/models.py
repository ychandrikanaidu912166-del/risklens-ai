"""ORM tables. Kept intentionally flat and denormalized for demo scale."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(64), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    country = Column(String(2), nullable=False)
    kyc_level = Column(Integer, default=1)


class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id = Column(String(64), primary_key=True)
    category = Column(String(64), nullable=False)
    risk_tier = Column(Integer, default=1)  # 1 low, 2 medium, 3 high


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(String(64), primary_key=True)
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    os = Column(String(32), default="unknown")


class Transaction(Base):
    __tablename__ = "transactions"

    tx_id = Column(String(64), primary_key=True)
    ts = Column(DateTime, nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), nullable=False, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.merchant_id"), nullable=False, index=True)
    merchant_category = Column(String(64), nullable=False)
    device_id = Column(String(64), ForeignKey("devices.device_id"), nullable=False, index=True)
    ip_hash = Column(String(128), nullable=False, index=True)
    ip_country = Column(String(2), nullable=False)
    customer_country = Column(String(2), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR", nullable=False)
    channel = Column(String(16), default="web")
    auth_result = Column(String(16), default="success")
    hour = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    is_fraud_label = Column(Integer, nullable=True)  # ground truth for evaluation only
    split = Column(String(8), default="live", index=True)  # train/val/test/live
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


Index("ix_tx_customer_ts", Transaction.customer_id, Transaction.ts)


class Investigation(Base):
    __tablename__ = "investigations"

    tx_id = Column(String(64), primary_key=True)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(16), nullable=False)
    recommended_action = Column(String(24), nullable=False)
    fraud_probability = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    behavioral_deviation = Column(Float, nullable=False)
    confidence = Column(String(8), nullable=False)
    payload_json = Column(JSON, nullable=False)  # full InvestigationResult
    model_version = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String(64), default="system")
    action = Column(String(64), nullable=False)
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(String(64), nullable=False)
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_id = Column(String(64), ForeignKey("transactions.tx_id"), nullable=False, index=True)
    analyst_id = Column(String(64), default="analyst")
    action = Column(String(24), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
