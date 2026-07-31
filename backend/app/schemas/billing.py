from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict


BillingType = Literal["electric", "water", "gas"]


class BillingRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: BillingType
    tier_min: Decimal
    tier_max: Optional[Decimal] = None
    unit_price: Decimal
    extra_fee_name: Optional[str] = None
    extra_fee_rate: Optional[Decimal] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MeterUsageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    house_no: str
    type: BillingType
    month: str
    usage_amount: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
