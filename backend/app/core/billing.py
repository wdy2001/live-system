import random
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session

from app.models import BillingRule


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_bill(db: Session, type_: str, usage_amount: Decimal) -> dict:
    rules = (
        db.query(BillingRule)
        .filter(BillingRule.type == type_)
        .order_by(BillingRule.tier_min.asc())
        .all()
    )

    usage = Decimal(str(usage_amount))
    tier_items = []
    base_total = Decimal("0")

    for rule in rules:
        tier_min = Decimal(str(rule.tier_min))
        tier_max = Decimal(str(rule.tier_max)) if rule.tier_max is not None else None
        unit_price = Decimal(str(rule.unit_price))

        # 将离散区间 [tier_min, tier_max] 映射为连续累积的 (prev_cutoff, curr_cutoff]
        # 例：181-280 离散度 → prev_cutoff=180, curr_cutoff=280
        prev_cutoff = max(Decimal("0"), tier_min - 1)
        if tier_max is not None:
            curr_cutoff = tier_max
            tier_usage = max(Decimal("0"), min(usage, curr_cutoff) - prev_cutoff)
        else:
            tier_usage = max(Decimal("0"), usage - prev_cutoff)

        if tier_usage > 0:
            subtotal = _q(tier_usage * unit_price)
            tier_items.append({
                "tier_min": tier_min,
                "tier_max": tier_max,
                "usage": tier_usage,
                "unit_price": unit_price,
                "subtotal": subtotal,
            })
            base_total += subtotal

    base_total = _q(base_total)

    extra_map = {}
    total_usage = Decimal(str(usage_amount))
    for rule in rules:
        if rule.extra_fee_name and rule.extra_fee_rate:
            key = (rule.extra_fee_name, Decimal(str(rule.extra_fee_rate)))
            extra_map[key] = total_usage

    extra_items = []
    extra_fee = Decimal("0")
    for (name, rate), total_use in extra_map.items():
        subtotal = _q(total_use * rate)
        extra_items.append({
            "name": name,
            "rate": rate,
            "usage": total_use,
            "subtotal": subtotal,
        })
        extra_fee += subtotal

    extra_fee = _q(extra_fee)
    total = _q(base_total + extra_fee)

    return {
        "tier_items": tier_items,
        "base_total": base_total,
        "extra_items": extra_items,
        "extra_fee": extra_fee,
        "total": total,
    }


def random_usage_for_type(type_: str) -> Decimal:
    if type_ == "electric":
        value = random.randint(100, 500)
    elif type_ == "water":
        value = random.randint(5, 40)
    elif type_ == "gas":
        value = random.randint(100, 600)
    else:
        value = random.randint(10, 100)
    return Decimal(str(value))
