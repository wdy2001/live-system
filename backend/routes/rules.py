"""计费规则路由"""
from flask import Blueprint, request, jsonify
from models import BillTypeRule

rules_bp = Blueprint("rules", __name__)


@rules_bp.get("")
def list_rules():
    btype = request.args.get("type")
    q = BillTypeRule.query
    if btype in ("electricity", "water", "gas"):
        q = q.filter(BillTypeRule.type == btype)
    rules = q.order_by(BillTypeRule.type, BillTypeRule.tier).all()
    return jsonify(rules=[r.to_dict() for r in rules])
