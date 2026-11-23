from copy import deepcopy
from decimal import Decimal
from typing import Any

from pydantic import field_validator, Field, model_validator

from server.config import settings
from server.error import raise_with_log
from server.mongo import MongoModel
from util.currency import parse_amount
from util.date import Date
from util.nanoid import is_valid_nanoid

EXAMPLE_IN = {
    "personId": "fXJ6Gwfgnw-C",
    "riskId": "t4FcP75uGHHc",
    "externalId": "ABC123",
    "subscriptionDate": "2025-01-01",
    "currency": "UGX",
    "sumInsuredAmount": 600000,
    "premiumAmount": 40000,
}

EXAMPLE_OUT = deepcopy(EXAMPLE_IN)
EXAMPLE_OUT["id"] = "cwNCXQfypiTg"
EXAMPLE_OUT["nft"] = 2689313703


class PolicyIn(MongoModel):
    personId: str
    riskId: str
    externalId: str
    subscriptionDate: str
    currency: str = Field(default="UGX")
    sumInsuredAmount: float | str
    premiumAmount: float | str

    _sum_insured_decimal: Decimal | None = None
    _premium_decimal: Decimal | None = None

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

    @field_validator('currency')
    @classmethod
    def currency_upper(cls, v: str) -> str:
        return v.strip().upper()

    @model_validator(mode="after")
    def validate_amounts(self) -> "PolicyIn":
        currency = self.currency
        self._sum_insured_decimal = parse_amount(self.sumInsuredAmount, currency)
        self._premium_decimal = parse_amount(self.premiumAmount, currency)
        if self._sum_insured_decimal > settings.policy_ceiling(currency):
            raise_with_log(
                ValueError,
                f"sumInsuredAmount exceeds configured ceiling for {currency}",
            )
        if self._premium_decimal > settings.policy_ceiling(currency):
            raise_with_log(
                ValueError,
                f"premiumAmount exceeds configured ceiling for {currency}",
            )
        return self

    @property
    def sum_insured_decimal(self) -> Decimal:
        return self._sum_insured_decimal

    @property
    def premium_decimal(self) -> Decimal:
        return self._premium_decimal

    def idempotency_payload(self) -> dict[str, Any]:
        return {
            "personId": self.personId,
            "riskId": self.riskId,
            "subscriptionDate": self.subscriptionDate,
            "currency": self.currency,
            "sumInsuredAmount": str(self.sum_insured_decimal),
            "premiumAmount": str(self.premium_decimal),
        }

    def toMongoDict(self) -> dict:
        document = super().toMongoDict()
        document["sumInsuredAmount"] = float(self.sum_insured_decimal)
        document["premiumAmount"] = float(self.premium_decimal)
        return document

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