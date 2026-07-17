"""计费服务：阶梯计价计算"""
from decimal import Decimal, ROUND_HALF_UP
from extensions import db  # noqa: F401  (保持会话可用)
from models import BillTypeRule


def calculate_tiered_amount(type_: str, usage: float) -> dict:
    """根据阶梯规则计算费用，返回金额与各阶梯拆分"""
    rules = (
        BillTypeRule.query.filter_by(type=type_)
        .order_by(BillTypeRule.tier.asc())
        .all()
    )
    if not rules:
        return {"amount": 0.0, "breakdown": []}

    remaining = Decimal(str(usage))
    total = Decimal("0")
    breakdown = []

    for rule in rules:
        if remaining <= 0:
            break

        tier_min = Decimal(str(rule.min_usage))
        tier_max = Decimal(str(rule.max_usage)) if rule.max_usage is not None else None
        tier_capacity = (tier_max - tier_min) if tier_max is not None else remaining

        used_in_tier = min(remaining, tier_capacity)
        if used_in_tier <= 0:
            continue

        subtotal = used_in_tier * Decimal(str(rule.unit_price))
        total += subtotal
        remaining -= used_in_tier

        breakdown.append({
            "tier": rule.tier,
            "min_usage": float(tier_min),
            "max_usage": float(tier_max) if tier_max is not None else None,
            "unit_price": float(rule.unit_price),
            "usage_in_tier": float(used_in_tier),
            "subtotal": float(subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "description": rule.description,
        })

    amount = float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {"amount": amount, "breakdown": breakdown}
