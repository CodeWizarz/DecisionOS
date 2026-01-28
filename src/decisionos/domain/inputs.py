from datetime import datetime
from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator

class BaseInput(BaseModel):
    source_system: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(extra="forbid") # Strict validation: reject unknown fields

class CustomerTicketInput(BaseInput):
    """
    Schema for incoming customer support tickets.
    """
    ticket_id: str
    customer_tier: Literal["standard", "premium", "enterprise"]
    priority_label: Literal["low", "medium", "high", "critical"]
    text_content: str = Field(min_length=10, description="Raw ticket body")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MetricInput(BaseInput):
    """
    Schema for operational metrics (e.g. server load, latency).
    """
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str] = Field(default_factory=dict)

class MarketSignalInput(BaseInput):
    """
    Schema for external market signals (e.g. competitor price changes).
    """
    signal_type: Literal["price_change", "promo_launch", "stock_out"]
    competitor_id: str
    impact_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    details: Dict[str, Any]

