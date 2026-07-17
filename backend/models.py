"""SQLAlchemy 数据模型"""
from datetime import datetime
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum("user", "admin"), default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    households = db.relationship("Household", backref="user", lazy=True)
    repairs = db.relationship("RepairRequest", backref="user", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "real_name": self.real_name,
            "phone": self.phone,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Household(db.Model):
    __tablename__ = "households"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    household_no = db.Column(db.String(32), unique=True, nullable=False)
    address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    meters = db.relationship("Meter", backref="household", lazy=True)
    bills = db.relationship("Bill", backref="household", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "household_no": self.household_no,
            "address": self.address,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Meter(db.Model):
    __tablename__ = "meters"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("households.id"), nullable=False)
    type = db.Column(db.Enum("electricity", "water", "gas"), nullable=False)
    meter_no = db.Column(db.String(32), nullable=False)
    current_reading = db.Column(db.Numeric(12, 2), default=0)

    bills = db.relationship("Bill", backref="meter", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "household_id": self.household_id,
            "type": self.type,
            "meter_no": self.meter_no,
            "current_reading": float(self.current_reading or 0),
        }


class BillTypeRule(db.Model):
    __tablename__ = "bill_type_rules"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum("electricity", "water", "gas"), nullable=False)
    tier = db.Column(db.Integer, nullable=False)
    min_usage = db.Column(db.Numeric(12, 2), nullable=False)
    max_usage = db.Column(db.Numeric(12, 2))
    unit_price = db.Column(db.Numeric(10, 4), nullable=False)
    description = db.Column(db.String(255))

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "tier": self.tier,
            "min_usage": float(self.min_usage),
            "max_usage": float(self.max_usage) if self.max_usage is not None else None,
            "unit_price": float(self.unit_price),
            "description": self.description,
        }


class Bill(db.Model):
    __tablename__ = "bills"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("households.id"), nullable=False)
    meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"), nullable=False)
    type = db.Column(db.Enum("electricity", "water", "gas"), nullable=False)
    period = db.Column(db.String(7), nullable=False)  # YYYY-MM
    previous_reading = db.Column(db.Numeric(12, 2), nullable=False)
    current_reading = db.Column(db.Numeric(12, 2), nullable=False)
    usage_amount = db.Column(db.Numeric(12, 2), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.Enum("unpaid", "paid"), default="unpaid")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)

    payment = db.relationship("Payment", backref="bill", uselist=False, lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "household_id": self.household_id,
            "meter_id": self.meter_id,
            "type": self.type,
            "period": self.period,
            "previous_reading": float(self.previous_reading),
            "current_reading": float(self.current_reading),
            "usage_amount": float(self.usage_amount),
            "amount": float(self.amount),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey("bills.id"), unique=True, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(db.String(20), default="alipay")
    transaction_no = db.Column(db.String(64), nullable=False)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "bill_id": self.bill_id,
            "amount": float(self.amount),
            "method": self.method,
            "transaction_no": self.transaction_no,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }


class RepairRequest(db.Model):
    __tablename__ = "repair_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.Enum("electricity", "water", "gas", "other"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    urgency = db.Column(db.Enum("normal", "urgent"), default="normal")
    status = db.Column(db.Enum("pending", "processing", "resolved"), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "description": self.description,
            "phone": self.phone,
            "urgency": self.urgency,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
