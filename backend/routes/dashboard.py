"""工作台概览路由"""
from datetime import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from models import Household, Bill, RepairRequest

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("")
@jwt_required()
def overview():
    uid = int(get_jwt_identity())
    households = Household.query.filter_by(user_id=uid).all()
    household_ids = [h.id for h in households]

    total_unpaid_amount = 0.0
    unpaid_count = 0
    this_month_usage = {"electricity": 0.0, "water": 0.0, "gas": 0.0}
    repair_stats = {"pending": 0, "processing": 0, "resolved": 0}
    usage_trend = []

    if household_ids:
        unpaid_query = Bill.query.filter(
            Bill.household_id.in_(household_ids), Bill.status == "unpaid"
        )
        unpaid_rows = unpaid_query.with_entities(func.sum(Bill.amount)).first()
        total_unpaid_amount = float(unpaid_rows[0] or 0)
        unpaid_count = unpaid_query.count()

        all_bills = Bill.query.filter(Bill.household_id.in_(household_ids)).all()
        period_usage = {}
        for b in all_bills:
            if b.period not in period_usage:
                period_usage[b.period] = {"electricity": 0.0, "water": 0.0, "gas": 0.0}
            period_usage[b.period][b.type] += float(b.usage_amount)

        sorted_periods = sorted(period_usage.keys(), reverse=True)

        if sorted_periods:
            latest_period = sorted_periods[0]
            this_month_usage = period_usage[latest_period]

        repair_stats["pending"] = RepairRequest.query.filter_by(user_id=uid, status="pending").count()
        repair_stats["processing"] = RepairRequest.query.filter_by(user_id=uid, status="processing").count()
        repair_stats["resolved"] = RepairRequest.query.filter_by(user_id=uid, status="resolved").count()

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
            usage_trend.append({"period": period, **usage})

    households_data = [h.to_dict() for h in households]
    for h in households_data:
        h["meters"] = [m.to_dict() for m in Household.query.get(h["id"]).meters]

    return jsonify(
        total_unpaid_amount=total_unpaid_amount,
        unpaid_count=unpaid_count,
        this_month_usage=this_month_usage,
        repair_stats=repair_stats,
        usage_trend=usage_trend,
        households=households_data,
    )
