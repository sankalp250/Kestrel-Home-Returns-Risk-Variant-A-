from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    order_id: str
    order_placed_at: str
    customer_id: str
    sku: str
    sales_channel: str
    payment_mode: str
    discount_pct: float = Field(ge=0)
    qty: int = Field(ge=1)
    order_value_inr: float = Field(ge=0)
    promised_delivery_days: int = Field(ge=0)
    delivery_pincode: int
    is_gift: str
    customer_prior_orders: int = Field(ge=0)
    customer_prior_returns: int = Field(ge=0)
    delivery_note: Optional[str] = None
    last_service_event_type: Optional[str] = None
    pickup_scheduled_at: Optional[str] = None
    source: str


class PredictionResponse(BaseModel):
    order_id: str
    score: float
    risk_band: str
    recommended_action: str
    reasons: list[str]
