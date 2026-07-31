from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.core.billing import calculate_bill
from app.models import BillingRule


def _make_rule(id_, type_, tier_min, tier_max, unit_price, extra_fee_name=None, extra_fee_rate=None):
    rule = BillingRule()
    rule.id = id_
    rule.type = type_
    rule.tier_min = Decimal(str(tier_min))
    rule.tier_max = Decimal(str(tier_max)) if tier_max is not None else None
    rule.unit_price = Decimal(str(unit_price))
    rule.extra_fee_name = extra_fee_name
    rule.extra_fee_rate = Decimal(str(extra_fee_rate)) if extra_fee_rate is not None else None
    return rule


def test_calculate_electric_bill_350():
    electric_rules = [
        _make_rule(1, "electric", 0, 180, "0.52", "政府性基金及附加", "0.05"),
        _make_rule(2, "electric", 181, 280, "0.57", "政府性基金及附加", "0.05"),
        _make_rule(3, "electric", 281, None, "0.87", "政府性基金及附加", "0.05"),
    ]

    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_order_by = MagicMock()
    mock_order_by.all.return_value = electric_rules
    mock_filter.order_by.return_value = mock_order_by
    mock_query.filter.return_value = mock_filter

    mock_db = MagicMock()
    mock_db.query.return_value = mock_query

    result = calculate_bill(mock_db, "electric", Decimal("350"))

    assert result["base_total"] == Decimal("211.50")
    assert result["extra_fee"] == Decimal("17.50")
    assert result["total"] == Decimal("229.00")

    tier_items = result["tier_items"]
    assert len(tier_items) == 3
    assert tier_items[0]["subtotal"] == Decimal("93.60")
    assert tier_items[1]["subtotal"] == Decimal("57.00")
    assert tier_items[2]["subtotal"] == Decimal("60.90")


def test_calculate_water_bill_18():
    water_rules = [
        _make_rule(4, "water", 0, 15, "2.90", "污水处理费", "1.20"),
        _make_rule(5, "water", 16, 25, "4.30", "污水处理费", "1.20"),
        _make_rule(6, "water", 26, None, "7.00", "污水处理费", "1.20"),
    ]

    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_order_by = MagicMock()
    mock_order_by.all.return_value = water_rules
    mock_filter.order_by.return_value = mock_order_by
    mock_query.filter.return_value = mock_filter

    mock_db = MagicMock()
    mock_db.query.return_value = mock_query

    result = calculate_bill(mock_db, "water", Decimal("18"))

    assert result["base_total"] == Decimal("56.40")
    assert result["extra_fee"] == Decimal("21.60")
    assert result["total"] == Decimal("78.00")
