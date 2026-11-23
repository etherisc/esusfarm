"""Currency amount parsing for ESF-1.10 (UGX on-chain only)."""

from decimal import Decimal, InvalidOperation

from server.error import raise_with_log

SUPPORTED = frozenset({"UGX", "ZAR", "NGN", "USD", "SZL"})

CEILINGS: dict[str, Decimal] = {
    "UGX": Decimal("5000000"),
    "ZAR": Decimal("5000000"),
    "NGN": Decimal("5000000"),
    "USD": Decimal("5000000"),
    "SZL": Decimal("5000000"),
}


def parse_amount(value: float | str | Decimal, currency: str) -> Decimal:
    currency = currency.upper()
    if currency not in SUPPORTED:
        raise_with_log(ValueError, f"currency {currency} is not supported")

    if isinstance(value, Decimal):
        amount = value
    elif isinstance(value, (int, float)):
        amount = Decimal(str(value))
    else:
        try:
            amount = Decimal(value.strip())
        except InvalidOperation:
            raise_with_log(ValueError, f"amount {value!r} is not a valid decimal")

    if amount <= 0:
        raise_with_log(ValueError, f"amount must be positive")

    if currency == "UGX":
        if amount != amount.to_integral_value():
            raise_with_log(ValueError, "UGX amounts must be whole units")
        amount = amount.to_integral_value()
    else:
        exp = amount.as_tuple().exponent
        if exp < -2:
            raise_with_log(ValueError, f"{currency} allows at most 2 decimal places")

    ceiling = CEILINGS[currency]
    if amount > ceiling:
        raise_with_log(ValueError, f"amount exceeds ceiling {ceiling} for {currency}")

    return amount