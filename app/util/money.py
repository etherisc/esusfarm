"""Exact conversion between major units and token base units (6 decimals for UGX)."""

from decimal import Decimal, ROUND_DOWN


TOKEN_DECIMALS = 6
SCALE = Decimal(10) ** TOKEN_DECIMALS


def major_to_base_units(amount: Decimal | str | float) -> int:
    """Convert a major-unit amount to integer base units without float error."""
    value = amount if isinstance(amount, Decimal) else Decimal(str(amount))
    base = (value * SCALE).to_integral_value(rounding=ROUND_DOWN)
    return int(base)


def float_to_decimal(amount: float) -> Decimal:
    return Decimal(str(amount))