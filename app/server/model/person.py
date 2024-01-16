from pydantic import field_validator
from server.error import raise_with_log
from server.mongo import MongoModel
from util.nanoid import is_valid_nanoid
from util.wallet import generate_wallet, is_valid_wallet_address

EXAMPLE_IN = {
    "location_id": "U6ufadiIe0Xz",
    "external_id": "PRS1234",
    "last_name": "Kienou",
    "first_name": "Hawa",
    "sex": "f",
    "mobile_phone": "+22660123456",
    "wallet":  "0x03507c8a16513F1615bD4a00BDD4570514a6ef21"
}

EXAMPLE_OUT = EXAMPLE_IN
EXAMPLE_OUT["id"] = "fXJ6Gwfgnw-C"

class PersonIn(MongoModel):
    location_id: str
    external_id: str
    last_name: str
    first_name: str
    sex: str
    mobile_phone: str
    wallet: str

    @field_validator('location_id')
    @classmethod
    def id_must_be_nanoid(cls, v: str) -> str:
        nanoid = v.strip()
        if not is_valid_nanoid(nanoid):
            raise_with_log(ValueError, f"location_id {nanoid} is not a valid nanoid")
        
        return nanoid

    @field_validator('first_name', 'last_name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        name = v.strip()
        if len(name) == 0:
            raise_with_log(ValueError, f"name must not be empty")

        return name

    @field_validator('sex')
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
    id: str

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

