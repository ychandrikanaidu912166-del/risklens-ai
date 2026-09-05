import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from backend.app.database.session import Base


class TransactionModel(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), index=True, nullable=False)
    merchant_id = Column(String(64), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    device_id = Column(String(128), index=True)
    ip_address = Column(String(64), index=True)
    country = Column(String(8), default="IN")
    payment_method = Column(String(32), default="upi")
    transaction_status = Column(String(32), default="success")

    # Historical state at transaction time
    customer_age_days = Column(Integer, default=30)
    customer_transaction_count = Column(Integer, default=0)
    customer_avg_amount = Column(Float, default=1000.0)
    customer_max_amount = Column(Float, default=1000.0)
    customer_usual_country = Column(String(8), default="IN")
    customer_usual_device = Column(String(128))

    # Velocity
    transactions_last_10m = Column(Integer, default=0)
    transactions_last_1h = Column(Integer, default=0)
    transactions_last_24h = Column(Integer, default=0)

    # Flags
    is_new_device = Column(Integer, default=0)
    is_new_country = Column(Integer, default=0)
    is_unusual_hour = Column(Integer, default=0)
    is_fraud = Column(Integer, default=0)

    # Risk Engine outputs
    risk_score = Column(Integer, default=0)
    risk_level = Column(String(16), default="LOW")
    ml_probability = Column(Float, default=0.0)

    # Relationships
    investigation = relationship("InvestigationModel", back_populates="transaction", uselist=False)


class InvestigationModel(Base):
    __tablename__ = "investigations"

    investigation_id = Column(String(64), primary_key=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), unique=True, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(16), nullable=False)
    status = Column(String(32), default="PENDING")  # PENDING, IN_REVIEW, RESOLVED
    priority = Column(String(16), default="MEDIUM")  # LOW, MEDIUM, HIGH, URGENT

    policy_recommendation = Column(String(32), default="MANUAL_REVIEW")
    automation_allowed = Column(Boolean, default=False)
    evidence_quality = Column(String(16), default="HIGH")

    # AI assessment stored as JSON text
    ai_assessment_json = Column(Text, nullable=True)
    ai_is_fallback = Column(Boolean, default=True)

    # Analyst decision
    analyst_decision = Column(String(32), nullable=True)  # APPROVE, HOLD, BLOCK, FALSE_POSITIVE, ESCALATE
    analyst_reason = Column(Text, nullable=True)
    decision_timestamp = Column(DateTime, nullable=True)
    model_version = Column(String(64), default="v1.2.0-xgb")
    policy_version = Column(String(32), default="v2.1")

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    transaction = relationship("TransactionModel", back_populates="investigation")
    evidence_items = relationship("EvidenceItemModel", back_populates="investigation", cascade="all, delete-orphan")
    counter_evidence_items = relationship("CounterEvidenceItemModel", back_populates="investigation", cascade="all, delete-orphan")


class EvidenceItemModel(Base):
    __tablename__ = "investigation_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(String(64), ForeignKey("investigations.investigation_id"), nullable=False, index=True)
    evidence_id = Column(String(64), nullable=False)
    type = Column(String(64), nullable=False)
    source = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(16), default="MEDIUM")
    observed_value = Column(String(256), nullable=True)
    baseline_value = Column(String(256), nullable=True)
    timestamp = Column(String(64), nullable=True)

    investigation = relationship("InvestigationModel", back_populates="evidence_items")


class CounterEvidenceItemModel(Base):
    __tablename__ = "investigation_counter_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(String(64), ForeignKey("investigations.investigation_id"), nullable=False, index=True)
    item_id = Column(String(64), nullable=False)
    type = Column(String(64), nullable=False)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    confidence_impact = Column(Integer, default=0)
    timestamp = Column(String(64), nullable=True)

    investigation = relationship("InvestigationModel", back_populates="counter_evidence_items")


class TimelineEventModel(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), index=True, nullable=False)
    event_type = Column(String(64), nullable=False)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(16), default="INFO")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    metadata_json = Column(Text, nullable=True)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False, index=True)
    actor = Column(String(64), default="system")
    details_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
