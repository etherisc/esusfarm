import pytest

from util.currency import parse_amount


def test_ugx_whole_units():
    assert parse_amount("600000", "UGX") == parse_amount(600000, "UGX")


def test_ugx_rejects_fraction():
    with pytest.raises(ValueError):
        parse_amount("1.5", "UGX")


def test_usd_two_decimals():
    assert parse_amount("2.01", "USD") == parse_amount("2.01", "USD")


def test_usd_rejects_extra_precision():
    with pytest.raises(ValueError):
        parse_amount("2.019", "USD")