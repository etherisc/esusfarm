from copy import deepcopy
from decimal import Decimal

from pydantic import field_validator, Field

from server.config import settings
from server.error import raise_with_log
from server.mongo import MongoModel
from util.date import Date
from util.money import float_to_decimal
from util.nanoid import is_valid_nanoid

EXAMPLE_IN = {
    "personId": "fXJ6Gwfgnw-C",
    "riskId": "t4FcP75uGHHc",
    "externalId": "ABC123",
    "subscriptionDate": "2025-01-01",
    "sumInsuredAmount": 600000.0,
    "premiumAmount": 40000.0,
}

EXAMPLE_OUT = deepcopy(EXAMPLE_IN)
EXAMPLE_OUT["id"] = "cwNCXQfypiTg"
EXAMPLE_OUT["nft"] = "2689313703"


class PolicyIn(MongoModel):
    personId: str
    riskId: str
    externalId: str
    subscriptionDate: str
    sumInsuredAmount: float
    premiumAmount: float

    @field_validator('personId', 'riskId')
    @classmethod
    def id_must_be_nanoid(cls, v: str) -> str:
        nanoid = v.strip()
        if not is_valid_nanoid(nanoid):
            raise_with_log(ValueError, f"the id {nanoid} is not a valid nanoid")

        return nanoid

    @field_validator('subscriptionDate')
    @classmethod
    def date_must_be_valid_iso(cls, v: str) -> str:
        date = Date.create_from(v)
        return date.to_iso_string()

    @field_validator('sumInsuredAmount', 'premiumAmount')
    @classmethod
    def monetary_amount_must_be_meaningful(cls, amount: float) -> float:
        if amount <= 0.0:
            raise_with_log(ValueError, f"amount {amount} invalid, value must not be 0 or negative")
        ceiling = settings.POLICY_MAX_AMOUNT_UGX
        if float_to_decimal(amount) > ceiling:
            raise_with_log(
                ValueError,
                f"amount {amount} invalid, value is larger than maximum amount of {ceiling}",
            )

        return amount

    @classmethod
    def sum_insured_as_decimal(cls, amount: float) -> Decimal:
        return float_to_decimal(amount)

    @classmethod
    def premium_as_decimal(cls, amount: float) -> Decimal:
        return float_to_decimal(amount)

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_IN
        }

class PolicyOut(PolicyIn):
    _id: str
    id: str = Field(default=None)
    nft: int | None = Field(default=None)
    tx: str | None = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }