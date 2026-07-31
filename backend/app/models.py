from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    VARCHAR,
    CHAR,
    DECIMAL,
    DateTime,
    Enum,
    Text,
    JSON,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(VARCHAR(50), unique=True, nullable=False)
    password_hash = Column(VARCHAR(255), nullable=False)
    full_name = Column(VARCHAR(100))
    phone = Column(VARCHAR(20))
    address = Column(VARCHAR(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payment_orders = relationship("PaymentOrder", back_populates="user")
    repair_orders = relationship("RepairOrder", back_populates="user")


class BillingRule(Base):
    __tablename__ = "billing_rules"
    __table_args__ = (
        UniqueConstraint("type", "tier_min", name="uq_billing_rules_type_tier_min"),
        Index("ix_billing_rules_type", "type"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum("electric", "water", "gas", name="billing_type_enum"), nullable=False)
    tier_min = Column(DECIMAL(10, 2), nullable=False)
    tier_max = Column(DECIMAL(10, 2), nullable=True)
    unit_price = Column(DECIMAL(10, 4), nullable=False)
    extra_fee_name = Column(VARCHAR(50))
    extra_fee_rate = Column(DECIMAL(10, 4), default=0)
    description = Column(VARCHAR(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MeterUsage(Base):
    __tablename__ = "meter_usages"
    __table_args__ = (
        UniqueConstraint("house_no", "type", "month", name="uq_meter_usages_house_type_month"),
        Index("ix_meter_usages_house_no", "house_no"),
        Index("ix_meter_usages_type", "type"),
        Index("ix_meter_usages_month", "month"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    house_no = Column(VARCHAR(50), nullable=False)
    type = Column(Enum("electric", "water", "gas", name="meter_type_enum"), nullable=False)
    month = Column(CHAR(7), nullable=False)
    usage_amount = Column(DECIMAL(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PaymentOrder(Base):
    __tablename__ = "payment_orders"
    __table_args__ = (
        Index("ix_payment_orders_user_id_created_at", "user_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(VARCHAR(32), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    house_no = Column(VARCHAR(50))
    type = Column(Enum("electric", "water", "gas", name="payment_type_enum"))
    month = Column(CHAR(7))
    total_amount = Column(DECIMAL(10, 2))
    status = Column(Enum("unpaid", "paid", "overdue", name="payment_status_enum"), default="unpaid")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    paid_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="payment_orders")
    bill_detail = relationship("BillDetail", back_populates="order", uselist=False, cascade="all, delete-orphan")


class BillDetail(Base):
    __tablename__ = "bill_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("payment_orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    base_total = Column(DECIMAL(10, 2))
    extra_fee = Column(DECIMAL(10, 2))
    tier_items = Column(JSON)
    extra_items = Column(JSON)
    summary = Column(VARCHAR(500))

    order = relationship("PaymentOrder", back_populates="bill_detail")


class RepairOrder(Base):
    __tablename__ = "repair_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(VARCHAR(32), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    repair_type = Column(VARCHAR(50))
    category = Column(Enum("electric", "water", "gas", "other", name="repair_category_enum"), index=True)
    urgency = Column(Enum("low", "middle", "high", name="repair_urgency_enum"), default="middle")
    address = Column(VARCHAR(255))
    contact_name = Column(VARCHAR(50))
    contact_phone = Column(VARCHAR(20))
    description = Column(Text)
    image_urls = Column(JSON)
    status = Column(Enum("pending", "processing", "completed", "cancelled", name="repair_status_enum"), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    progress_timeline = Column(JSON)

    user = relationship("User", back_populates="repair_orders")
