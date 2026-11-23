from decimal import Decimal

import pytest

from util.money import major_to_base_units


@pytest.mark.parametrize(
    "amount,expected",
    [
        ("2.01", 2010000),
        ("1", 1000000),
        ("0.000001", 1),
        (Decimal("2.01"), 2010000),
    ],
)
def test_major_to_base_units(amount, expected):
    assert major_to_base_units(amount) == expected


def test_float_two_point_oh_one():
    assert major_to_base_units(2.01) == 2010000