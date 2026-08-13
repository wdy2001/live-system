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
    this_month_usage = {"electricity": 0.0, "water": 0.0, "gas": 0.0}
    repair_processing = 0
    monthly_usage = []

    if household_ids:
        unpaid_rows = (
            Bill.query.filter(Bill.household_id.in_(household_ids), Bill.status == "unpaid")
            .with_entities(func.sum(Bill.amount))
            .first()
        )
        unpaid_total = float(unpaid_rows[0] or 0)

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

        repair_processing = RepairRequest.query.filter_by(user_id=uid, status="processing").count()

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

    return jsonify(
        unpaid_total=unpaid_total,
        this_month_usage=this_month_usage,
        repair_processing=repair_processing,
        monthly_usage=monthly_usage,
    )
