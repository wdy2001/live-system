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

    btype = request.args.get("type")
    status = request.args.get("status")
    period = request.args.get("period")
    try:
        page = int(request.args.get("page", 1))
        if page < 1:
            page = 1
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", 10))
        if per_page < 1:
            per_page = 10
        if per_page > 50:
            per_page = 50
    except (TypeError, ValueError):
        per_page = 10

    q = Bill.query.filter(Bill.household_id.in_(household_ids))
    if btype in ("electricity", "water", "gas"):
        q = q.filter(Bill.type == btype)
    if status in ("unpaid", "paid"):
        q = q.filter(Bill.status == status)
    if period:
        q = q.filter(Bill.period == period)

    q = q.order_by(Bill.period.desc(), Bill.id.desc())
    total = q.count()
    bills = q.offset((page - 1) * per_page).limit(per_page).all()
    result = []
    for b in bills:
        d = b.to_dict()
        d["household"] = b.household.to_dict()
        d["meter"] = b.meter.to_dict()
        result.append(d)
    return jsonify(bills=result, total=total, page=page, per_page=per_page)


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
    calc_result = calculate_tiered_amount(bill.type, float(bill.usage_amount))
    breakdown = calc_result["breakdown"]
    result["breakdown"] = breakdown
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
    try:
        payment = Payment(
            bill_id=bill.id,
            amount=bill.amount,
            method=method,
            transaction_no=f"PAY{uuid.uuid4().hex.upper()}",
        )
        bill.status = "paid"
        bill.paid_at = datetime.utcnow()
        bill.meter.current_reading = bill.current_reading

        db.session.add(payment)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(
        payment=payment.to_dict(),
        bill=bill.to_dict(),
    )
