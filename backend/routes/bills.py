"""账单路由：查询 / 详情 / 支付"""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

from extensions import db
from models import User, Household, Bill, Payment
from services.billing import calculate_tiered_amount

bills_bp = Blueprint("bills", __name__)


def _user_household_ids(uid):
    return [h.id for h in Household.query.filter_by(user_id=uid).all()]


@bills_bp.get("")
@jwt_required()
def list_bills():
    uid = int(get_jwt_identity())
    household_ids = _user_household_ids(uid)
    if not household_ids:
        return jsonify(bills=[])

    btype = request.args.get("type")
    status = request.args.get("status")
    period = request.args.get("period")

    q = Bill.query.filter(Bill.household_id.in_(household_ids))
    if btype in ("electricity", "water", "gas"):
        q = q.filter(Bill.type == btype)
    if status in ("unpaid", "paid"):
        q = q.filter(Bill.status == status)
    if period:
        q = q.filter(Bill.period == period)

    bills = q.order_by(Bill.period.desc(), Bill.id.desc()).all()
    return jsonify(bills=[b.to_dict() for b in bills])


@bills_bp.get("/<int:bill_id>")
@jwt_required()
def bill_detail(bill_id):
    uid = int(get_jwt_identity())
    bill = Bill.query.get(bill_id)
    if not bill:
        return jsonify(msg="账单不存在"), 404
    if bill.household.user_id != uid:
        return jsonify(msg="无权访问该账单"), 403

    result = bill.to_dict()
    breakdown = calculate_tiered_amount(bill.type, float(bill.usage_amount))
    result["breakdown"] = breakdown["breakdown"]
    result["household"] = bill.household.to_dict()
    result["meter"] = bill.meter.to_dict()
    if bill.payment:
        result["payment"] = bill.payment.to_dict()
    return jsonify(bill=result)


@bills_bp.post("/<int:bill_id>/pay")
@jwt_required()
def pay_bill(bill_id):
    uid = int(get_jwt_identity())
    bill = Bill.query.get(bill_id)
    if not bill:
        return jsonify(msg="账单不存在"), 404
    if bill.household.user_id != uid:
        return jsonify(msg="无权操作该账单"), 403
    if bill.status == "paid":
        return jsonify(msg="该账单已支付"), 400

    method = (request.get_json() or {}).get("method", "alipay")
    payment = Payment(
        bill_id=bill.id,
        amount=bill.amount,
        method=method,
        transaction_no=f"PAY{uuid.uuid4().hex[:16].upper()}",
    )
    bill.status = "paid"
    bill.paid_at = datetime.utcnow()
    # 更新表当前读数
    bill.meter.current_reading = bill.current_reading

    db.session.add(payment)
    db.session.commit()

    return jsonify(
        payment_id=payment.id,
        transaction_no=payment.transaction_no,
        paid_at=payment.paid_at.isoformat(),
        bill=bill.to_dict(),
    )
