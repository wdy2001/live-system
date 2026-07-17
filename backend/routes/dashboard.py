"""工作台概览路由"""
from collections import defaultdict
from datetime import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from models import User, Household, Bill, RepairRequest

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("")
@jwt_required()
def overview():
    uid = int(get_jwt_identity())
    households = Household.query.filter_by(user_id=uid).all()
    household_ids = [h.id for h in households]

    if not household_ids:
        return jsonify(
            unpaid_total=0.0,
            unpaid_count=0,
            this_month_usage={"electricity": 0, "water": 0, "gas": 0},
            repair_stats={"pending": 0, "processing": 0, "resolved": 0},
            trends=[],
        )

    # 待缴总额与数量
    unpaid_rows = (
        Bill.query.filter(Bill.household_id.in_(household_ids), Bill.status == "unpaid")
        .with_entities(func.sum(Bill.amount), func.count(Bill.id))
        .first()
    )
    unpaid_total = float(unpaid_rows[0] or 0)
    unpaid_count = int(unpaid_rows[1] or 0)

    # 本月用量
    this_period = datetime.utcnow().strftime("%Y-%m")
    month_bills = (
        Bill.query.filter(Bill.household_id.in_(household_ids), Bill.period == this_period)
        .all()
    )
    this_month_usage = {"electricity": 0.0, "water": 0.0, "gas": 0.0}
    for b in month_bills:
        this_month_usage[b.type] += float(b.usage_amount)

    # 报修统计
    repairs = RepairRequest.query.filter_by(user_id=uid).all()
    repair_stats = {"pending": 0, "processing": 0, "resolved": 0}
    for r in repairs:
        if r.status in repair_stats:
            repair_stats[r.status] += 1

    # 近6个月趋势
    trends = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        y = now.year
        m = now.month - i
        while m <= 0:
            m += 12
            y -= 1
        period = f"{y:04d}-{m:02d}"
        period_bills = [b for b in month_bills if b.period == period] if period == this_period else (
            Bill.query.filter(Bill.household_id.in_(household_ids), Bill.period == period).all()
        )
        usage = {"electricity": 0.0, "water": 0.0, "gas": 0.0}
        for b in period_bills:
            usage[b.type] += float(b.usage_amount)
        trends.append({"period": period, "usage": usage})

    return jsonify(
        unpaid_total=unpaid_total,
        unpaid_count=unpaid_count,
        this_month_usage=this_month_usage,
        repair_stats=repair_stats,
        trends=trends,
        households=[h.to_dict() for h in households],
    )
