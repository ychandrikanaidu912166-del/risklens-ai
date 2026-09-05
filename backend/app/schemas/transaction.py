from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TransactionCreate(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction ID")
    customer_id: str = Field(..., description="Customer account ID")
    merchant_id: str = Field(..., description="Merchant ID")
    amount: float = Field(..., gt=0, description="Amount in transaction currency")
    currency: str = Field(default="INR")
    timestamp: Optional[str] = Field(default=None)
    device_id: Optional[str] = Field(default="")
    ip_address: Optional[str] = Field(default="")
    country: Optional[str] = Field(default="IN")
    payment_method: Optional[str] = Field(default="upi")
    transaction_status: Optional[str] = Field(default="success")

    customer_age_days: Optional[int] = Field(default=30)
    customer_transaction_count: Optional[int] = Field(default=0)
    customer_avg_amount: Optional[float] = Field(default=1000.0)
    customer_max_amount: Optional[float] = Field(default=1000.0)
    customer_usual_country: Optional[str] = Field(default="IN")
    customer_usual_device: Optional[str] = Field(default="")

    transactions_last_10m: Optional[int] = Field(default=0)
    transactions_last_1h: Optional[int] = Field(default=0)
    transactions_last_24h: Optional[int] = Field(default=0)

    is_new_device: Optional[int] = Field(default=0)
    is_new_country: Optional[int] = Field(default=0)
    is_unusual_hour: Optional[int] = Field(default=0)


class TransactionResponse(TransactionCreate):
    risk_score: Optional[int] = 0
    risk_level: Optional[str] = "LOW"
    ml_probability: Optional[float] = 0.0

    class Config:
        from_attributes = True
