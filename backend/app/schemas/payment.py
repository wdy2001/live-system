from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


BillingType = Literal["electric", "water", "gas"]
PaymentStatus = Literal["unpaid", "paid", "overdue"]


class PaymentQuery(BaseModel):
    house_no: str
    type: BillingType
    month: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")


class PaymentOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    user_id: Optional[int] = None
    house_no: Optional[str] = None
    type: Optional[BillingType] = None
    month: Optional[str] = None
    total_amount: Optional[Decimal] = None
    status: PaymentStatus
    created_at: datetime
    paid_at: Optional[datetime] = None


class BillDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    base_total: Optional[Decimal] = None
    extra_fee: Optional[Decimal] = None
    tier_items: Optional[List[Dict[str, Any]]] = None
    extra_items: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None


class PaymentPay(BaseModel):
    order_id: int


class BillOut(BaseModel):
    tier_items: List[Dict[str, Any]]
    base_total: Decimal
    extra_items: List[Dict[str, Any]]
    extra_fee: Decimal
    total: Decimal


class PaymentQueryResultOut(BaseModel):
    order_id: int
    order_no: str
    house_no: str
    type: BillingType
    month: str
    total_amount: Decimal
    status: PaymentStatus
    bill: BillOut


class PaymentPayResultOut(BaseModel):
    success: bool
    order_id: int
    paid_at: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    already_paid: Optional[bool] = False


class PaymentOrderWithBillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    user_id: Optional[int] = None
    house_no: Optional[str] = None
    type: Optional[BillingType] = None
    month: Optional[str] = None
    total_amount: Optional[Decimal] = None
    status: PaymentStatus
    created_at: datetime
    paid_at: Optional[datetime] = None
    base_total: Optional[Decimal] = None
    extra_fee: Optional[Decimal] = None
    tier_items: Optional[List[Dict[str, Any]]] = None
    extra_items: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None

