from pydantic import BaseModel
from pydantic import field_validator

from server.error import raise_with_log
from server.mongo import MongoModel
from util.nanoid import is_valid_nanoid

EXAMPLE_IN = {
    "isValid": True,
    "configId": "0xbec1f9e54b04a83d0769850c936d37a8",
    "locationId": "0x9492fef57f9e671753f92b78a9958ada",
    "crop": "Sorghum",
    "indexReferenceValue": 71972625,
    "indexSeasonValue": 55671585,
    "indexIsFinal": False,
    "createdAt": 1700316957,
    "updatedAt": 1700316957
}

EXAMPLE_OUT = EXAMPLE_IN
EXAMPLE_OUT["id"] = "0x2e25dc055145b0eb1e5bef3879c675b6"

VALID_CROPS = ["maize"]

class RiskIn(BaseModel):
    isValid: bool
    configId: str
    locationId: str
    crop: str
    indexReferenceValue: int
    indexSeasonValue: int
    indexIsFinal: bool
    createdAt: int
    updatedAt: int

    # @field_validator('risk_config_id', 'location_id')
    # @classmethod
    # def id_must_be_nanoid(cls, v: str) -> str:
    #     nanoid = v.strip()
    #     if not is_valid_nanoid(nanoid):
    #         raise_with_log(ValueError, f"the id {nanoid} is not a valid nanoid")
        
    #     return nanoid

    # @field_validator('crop')
    # @classmethod
    # def crop_must_be_valid(cls, v: str) -> str:
    #     crop = v.strip().lower()

    #     if crop not in VALID_CROPS:
    #         raise_with_log(ValueError, f"crop {crop} invalid, valid crops are {VALID_CROPS}")

    #     return crop

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_IN
        }

class RiskOut(RiskIn):
    id: str

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

