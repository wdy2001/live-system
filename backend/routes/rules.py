"""计费规则路由"""
from flask import Blueprint, request, jsonify
from models import BillTypeRule
from services.billing import calculate_tiered_amount

rules_bp = Blueprint("rules", __name__)

EXAMPLE_USAGE_MAP = {
    "electricity": 250,
    "water": 15,
    "gas": 350,
}


@rules_bp.get("")
def list_rules():
    btype = request.args.get("type")
    q = BillTypeRule.query
    if btype in ("electricity", "water", "gas"):
        q = q.filter(BillTypeRule.type == btype)
    rules = q.order_by(BillTypeRule.type, BillTypeRule.tier).all()

    example_type = btype if btype in EXAMPLE_USAGE_MAP else "electricity"
    example_usage = EXAMPLE_USAGE_MAP[example_type]
    calc_result = calculate_tiered_amount(example_type, example_usage)
    example = {
        "usage": example_usage,
        "amount": calc_result["amount"],
        "breakdown": calc_result["breakdown"],
    }

    return jsonify(rules=[r.to_dict() for r in rules], example=example)
