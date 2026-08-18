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

    unpaid_total = 0.0
    unpaid_count = 0
    this_month_usage = {"electricity": 0.0, "water": 0.0, "gas": 0.0}
    repair_processing = 0
    repair_stats = {"pending": 0, "processing": 0, "resolved": 0}
    monthly_usage = []
    trends = []

    if household_ids:
        unpaid_query = Bill.query.filter(
            Bill.household_id.in_(household_ids), Bill.status == "unpaid"
        )
        unpaid_rows = unpaid_query.with_entities(func.sum(Bill.amount)).first()
        unpaid_total = float(unpaid_rows[0] or 0)
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

        for rs in repair_stats.keys():
            repair_stats[rs] = RepairRequest.query.filter_by(
                user_id=uid, status=rs
            ).count()
        repair_processing = repair_stats["processing"]

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
            monthly_usage.append({"period": period, **usage})
            trends.append({"period": period, "usage": usage})

    households_list = [
        {
            "id": h.id,
            "household_no": h.household_no,
            "address": h.address,
            "user_id": h.user_id,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in households
    ]

    return jsonify(
        unpaid_total=unpaid_total,
        unpaid_count=unpaid_count,
        this_month_usage=this_month_usage,
        repair_processing=repair_processing,
        repair_stats=repair_stats,
        monthly_usage=monthly_usage,
        trends=trends,
        households=households_list,
    )
