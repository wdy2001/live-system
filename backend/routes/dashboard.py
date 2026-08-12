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

    # 查询户号下所有账单，按 period 聚合
    all_bills = Bill.query.filter(Bill.household_id.in_(household_ids)).all()
    period_usage = {}
    for b in all_bills:
        if b.period not in period_usage:
            period_usage[b.period] = {"electricity": 0.0, "water": 0.0, "gas": 0.0}
        period_usage[b.period][b.type] += float(b.usage_amount)

    # 所有 period 倒序排列
    sorted_periods = sorted(period_usage.keys(), reverse=True)

    # 最近一期用量（this_month_usage = 最新一期用量）
    this_month_usage = {"electricity": 0.0, "water": 0.0, "gas": 0.0}
    if sorted_periods:
        latest_period = sorted_periods[0]
        this_month_usage = period_usage[latest_period]

    # 报修统计
    repairs = RepairRequest.query.filter_by(user_id=uid).all()
    repair_stats = {"pending": 0, "processing": 0, "resolved": 0}
    for r in repairs:
        if r.status in repair_stats:
            repair_stats[r.status] += 1

    # 近6个月趋势：从最近一期往前推 6 个日历月
    trends = []
    if sorted_periods:
        latest_period = sorted_periods[0]
        ly, lm = map(int, latest_period.split("-"))
        now = datetime(ly, lm, 1)
    else:
        now = datetime.utcnow()
    for i in range(5, -1, -1):
        y = now.year
        m = now.month - i
        while m <= 0:
            m += 12
            y -= 1
        period = f"{y:04d}-{m:02d}"
        usage = period_usage.get(period, {"electricity": 0.0, "water": 0.0, "gas": 0.0})
        trends.append({"period": period, "usage": usage})

    return jsonify(
        unpaid_total=unpaid_total,
        unpaid_count=unpaid_count,
        this_month_usage=this_month_usage,
        repair_stats=repair_stats,
        trends=trends,
        households=[h.to_dict() for h in households],
    )
