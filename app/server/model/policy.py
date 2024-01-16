from pydantic import field_validator
from server.error import raise_with_log
from server.mongo import MongoModel
from util.date import Date
from util.nanoid import is_valid_nanoid

EXAMPLE_IN = {
    "person_id": "fXJ6Gwfgnw-C",
    "risk_id": "t4FcP75uGHHc",
    "external_id": "QF123456",
    "subscription_date": "2023-06-14",
    "sum_insured_amount": 20000.0,
    "premium_amount": 1500.0,
}

EXAMPLE_OUT = EXAMPLE_IN
EXAMPLE_OUT["id"] = "cwNCXQfypiTg"
EXAMPLE_OUT["process_id"] = "FC643008A2EC718EBB1C5001B426A2AC65035B1AA910B1BA0769541F391967A8"

# https://www.xe.com/currencyconverter/convert/?Amount=500&From=USD&To=XOF
MAX_MONETARY_AMOUNT = 500000.0

MIN_DATE = Date.create_from("2023-01-01")
MAX_DATE = Date.create_from("2024-12-31")

class PolicyIn(MongoModel):
    person_id: str
    risk_id: str
    external_id: str
    subscription_date: str
    sum_insured_amount: float
    premium_amount: float

    @field_validator('person_id', 'risk_id')
    @classmethod
    def id_must_be_nanoid(cls, v: str) -> str:
        nanoid = v.strip()
        if not is_valid_nanoid(nanoid):
            raise_with_log(ValueError, f"the id {nanoid} is not a valid nanoid")
        
        return nanoid

    @field_validator('subscription_date')
    @classmethod
    def date_must_be_meaningful(cls, v: str) -> str:
        date = Date.create_from(v)
        date_str = date.to_iso_string()
        if date < MIN_DATE:
            raise_with_log(ValueError, f"date {date_str} too early, must be {MIN_DATE} or later")
        if date > MAX_DATE:
            raise_with_log(ValueError, f"date {date_str} too late, must be {MAX_DATE} or earlier")

        return date_str

    @field_validator('sum_insured_amount', 'premium_amount')
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
    id: str
    process_id: str

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

