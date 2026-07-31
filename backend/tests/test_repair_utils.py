import pytest

from app.core.utils import infer_category


def test_infer_category_electric():
    assert infer_category("electric_leak") == "electric"
    assert infer_category("Electric_Short") == "electric"
    assert infer_category("elec_fault") == "electric"


def test_infer_category_water():
    assert infer_category("water_pipe") == "water"
    assert infer_category("Water_Leak") == "water"
    assert infer_category("plumb_issue") == "water"


def test_infer_category_gas():
    assert infer_category("gas_odor") == "gas"
    assert infer_category("Gas_Leak") == "gas"


def test_infer_category_other():
    assert infer_category("other") == "other"
    assert infer_category("unknown_xxx") == "other"
    assert infer_category("random_issue") == "other"
