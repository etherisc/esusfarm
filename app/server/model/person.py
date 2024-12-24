from copy import deepcopy
from pydantic import field_validator, Field

from server.error import raise_with_log
from server.mongo import MongoModel
from web3utils.wallet import Wallet
from util.nanoid import is_valid_nanoid

EXAMPLE_IN = {
    "locationId": "U6ufadiIe0Xz",
    "externalId": "PRS1234",
    "lastName": "Auma",
    "firstName": "Florence",
    "gender": "f",
    "mobilePhone": "+25656234567",
}

EXAMPLE_OUT = deepcopy(EXAMPLE_IN)
EXAMPLE_OUT["id"] = "fXJ6Gwfgnw-C"
EXAMPLE_OUT["walletIndex"] = 2345,
EXAMPLE_OUT["wallet"] = "0x03507c8a16513F1615bD4a00BDD4570514a6ef21"
EXAMPLE_OUT["tx"] = "0x10cc6457d494d0fee7aeb89c63bcdd98f90aad18bb761591d8da1314551ca3ca"

class PersonIn(MongoModel):
    lastName: str
    firstName: str
    gender: str
    mobilePhone: str
    locationId: str
    externalId: str | None = Field(default=None)

    @field_validator('locationId')
    @classmethod
    def id_must_be_nanoid(cls, v: str) -> str:
        nanoid = v.strip()
        if not is_valid_nanoid(nanoid):
            raise_with_log(ValueError, f"location_id {nanoid} is not a valid nanoid")
        
        return nanoid

    @field_validator('firstName', 'lastName')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        name = v.strip()
        if len(name) == 0:
            raise_with_log(ValueError, f"name must not be empty")

        return name

    @field_validator('gender')
    @classmethod
    def gender_must_be_m_or_f(cls, v: str) -> str:
        if v is None:
            return None

        gender = v.strip().lower()
        if gender not in ["m", "f"]:
            raise_with_log(ValueError, f"gender {gender} invalid, must be 'm' or 'f'")

        return gender

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_IN
        }

class PersonOut(PersonIn):
    _id: str
    id: str = Field(default=None)
    walletIndex: int | None = Field(default=None)
    wallet: str = Field(default=None)
    tx: str | None = Field(default=None)

    @field_validator('walletIndex')
    @classmethod
    def wallet_index_must_be_positive(cls, v: int) -> int:
        wallet_index = v
        if not isinstance(wallet_index, int):
            raise_with_log(ValueError, f"wallet index must be of type int")
        if wallet_index < 0:
            raise_with_log(ValueError, f"wallet index must be positive")

        return wallet_index

    @field_validator('wallet')
    @classmethod
    def create_wallet_if_none(cls, v: str) -> str:
        print(f"validating wallet {v} ...")
        wallet = v
        if wallet is None:
            raise_with_log(ValueError, f"wallet address must not be emtpy")
        
        print(f"wallet now: {v}")
        return wallet

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

