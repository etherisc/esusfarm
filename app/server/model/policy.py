from pydantic import field_validator, Field
from server.error import raise_with_log
from server.mongo import MongoModel
from util.date import Date
from util.nanoid import is_valid_nanoid

EXAMPLE_IN = {
    "personId": "fXJ6Gwfgnw-C",
    "riskId": "t4FcP75uGHHc",
    "externalId": "ABC123",
    "subscriptionDate": "2024-06-14",
    "sumInsuredAmount": 1000000.0,
    "premiumAmount": 200000.0,
}

EXAMPLE_OUT = EXAMPLE_IN
EXAMPLE_OUT["id"] = "cwNCXQfypiTg"
EXAMPLE_OUT["onchainId"] = "2689313703"

# https://www.xe.com/currencyconverter/convert/?Amount=300&From=USD&To=UGX
MAX_MONETARY_AMOUNT = 5000000.0

MIN_DATE = Date.create_from("2024-01-01")
MAX_DATE = Date.create_from("2024-12-31")

class PolicyIn(MongoModel):
    personId: str
    riskId: str
    externalId: str
    subscriptionDate: str
    sumInsuredAmount: float
    premiumAmount: float
    onchainId: str = Field(default=None)

    @field_validator('personId', 'riskId')
    @classmethod
    def id_must_be_nanoid(cls, v: str) -> str:
        nanoid = v.strip()
        if not is_valid_nanoid(nanoid):
            raise_with_log(ValueError, f"the id {nanoid} is not a valid nanoid")
        
        return nanoid

    @field_validator('subscriptionDate')
    @classmethod
    def date_must_be_meaningful(cls, v: str) -> str:
        date = Date.create_from(v)
        date_str = date.to_iso_string()
        if date < MIN_DATE:
            raise_with_log(ValueError, f"date {date_str} too early, must be {MIN_DATE} or later")
        if date > MAX_DATE:
            raise_with_log(ValueError, f"date {date_str} too late, must be {MAX_DATE} or earlier")

        return date_str

    @field_validator('sumInsuredAmount', 'premiumAmount')
    @classmethod
    def monetary_amount_must_be_meaningful(cls, amount: float) -> str:
        if amount <= 0.0:
            raise_with_log(ValueError, f"amount {amount} invalid, value must not be 0 or negative")
        if amount > MAX_MONETARY_AMOUNT:
            raise_with_log(ValueError, f"amount {amount} invalid, value is larger than maximum amount of {MAX_MONETARY_AMOUNT}")

        return amount

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_IN
        }

class PolicyOut(PolicyIn):
    _id: str
    id: str = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

