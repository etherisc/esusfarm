from pydantic import field_validator, Field
from server.error import raise_with_log
from server.mongo import MongoModel
from util.nanoid import is_valid_nanoid
from util.wallet import generate_wallet, is_valid_wallet_address

EXAMPLE_IN = {
    "locationId": "U6ufadiIe0Xz",
    "externalId": "PRS1234",
    "lastName": "Auma",
    "firstName": "Florence",
    "gender": "f",
    "mobilePhone": "+25656234567",
    "wallet":  "0x03507c8a16513F1615bD4a00BDD4570514a6ef21"
}

EXAMPLE_OUT = EXAMPLE_IN
EXAMPLE_OUT["id"] = "fXJ6Gwfgnw-C"

class PersonIn(MongoModel):
    lastName: str
    firstName: str
    gender: str
    mobilePhone: str
    locationId: str
    wallet: str = Field(default=None)
    externalId: str = Field(default=None)

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
    def sex_must_be_m_or_f(cls, v: str) -> str:
        if v is None:
            return None

        sex = v.strip().lower()
        if sex not in ["m", "f"]:
            raise_with_log(ValueError, f"sex {sex} invalid, must be 'm' or 'f'")

        return sex

    @field_validator('wallet')
    @classmethod
    def create_wallet_if_none(cls, v: str) -> str:
        print(f"validating wallet {v} ...")
        wallet = v
        if wallet is None:
            wallet = generate_wallet()
        else:
            if not is_valid_wallet_address(wallet):
                raise_with_log(ValueError, f"invalid wallet address {wallet}")
        
        print(f"wallet now: {v}")
        return wallet

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_IN
        }

class PersonOut(PersonIn):
    _id: str
    id: str = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

