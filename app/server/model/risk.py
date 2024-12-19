from pydantic import field_validator, Field, BaseModel
from server.error import raise_with_log
from server.model.location import LocationOut
from server.model.config import ConfigOut
from server.mongo import MongoModel, get_collection_for_class
from util.nanoid import is_valid_nanoid
import time


EXAMPLE_IN = {
    "isValid": True,
    "configId": "7Zv4TZoBLxUi",
    "locationId": "kDho7606IRdr",
    "crop": "coffee",
    "startOfSeason": "2024-08-01",
    "endOfSeason": "2024-11-30",
    "deductible": 0.0,
}

EXAMPLE_UPDATE_IN = {
    "id": "jxmbyupsh1rv",
    "draughtLoss": 0.27,
    "excessRainfallLoss": 0.05,
    "totalLoss": 0.27,
    "payout": 0.27,
    "finalPayout": 0.27
}


EXAMPLE_OUT = {
    "id": "jxmbyupsh1rv",
    "isValid": True,
    "configId": "7Zv4TZoBLxUi",
    "locationId": "kDho7606IRdr",
    "crop": "coffee",
    "startOfSeason": "2024-08-01",
    "endOfSeason": "2024-11-30",
    "deductible": 0.0,
    "draughtLoss": 0.27,
    "excessRainfallLoss": 0.05,
    "totalLoss": 0.27,
    "payout": 0.27,
    "finalPayout": 0.27,
    "onchainId": "2689313703",
    "createdAt": 1700316957,
    "updatedAt": 1700316957
}


VALID_CROPS = ["coffee"]

class RiskIn(BaseModel):
    isValid: bool
    configId: str
    locationId: str
    crop: str
    deductible: float
    startOfSeason: str
    endOfSeason: str


    @field_validator('configId', 'locationId')
    @classmethod
    def id_must_be_nanoid(cls, v: str) -> str:
        nanoid = v.strip()
        if not is_valid_nanoid(nanoid):
            raise_with_log(ValueError, f"the id {nanoid} is not a valid nanoid")
        
        return nanoid

    @field_validator('locationId')
    @classmethod
    def location_must_exist(cls, v:str) -> str:
        nanoid = v.strip()
        collection = get_collection_for_class(LocationOut)
        if collection.count_documents({"_id": nanoid}) == 0:
            raise_with_log(ValueError, f"no location found for id {nanoid}")
        return nanoid

    @field_validator('configId')
    @classmethod
    def config_must_exist(cls, v:str) -> str:
        nanoid = v.strip()
        collection = get_collection_for_class(ConfigOut)
        if collection.count_documents({"_id": nanoid}) == 0:
            raise_with_log(ValueError, f"no config found for id {nanoid}")
        return nanoid

    @field_validator('crop')
    @classmethod
    def crop_must_be_valid(cls, v: str) -> str:
        crop = v.strip().lower()

        if crop not in VALID_CROPS:
            raise_with_log(ValueError, f"crop {crop} invalid, valid crops are {VALID_CROPS}")

        return crop

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_IN
        }

class RiskUpdateIn(BaseModel):
    id: str
    draughtLoss: float = Field(default=0.0)
    excessRainfallLoss: float = Field(default=0.0)
    totalLoss: float = Field(default=0.0)
    payout: float = Field(default=0.0)
    finalPayout: float = Field(default=0.0)


    @field_validator('id')
    @classmethod
    def risk_must_exist(cls, v:str) -> str:
        nanoid = v.strip()
        collection = get_collection_for_class(Risk)
        if collection.count_documents({"_id": nanoid}) == 0:
            raise_with_log(ValueError, f"no risk found for id {nanoid}")
        return nanoid
    
    class Config:
        json_schema_extra = {
            "example": EXAMPLE_UPDATE_IN
        }


class Risk(MongoModel):
    _id: str
    isValid: bool
    configId: str
    locationId: str
    crop: str
    deductible: float
    startOfSeason: str
    endOfSeason: str
    draughtLoss: float = Field(default=0.0)
    excessRainfallLoss: float = Field(default=0.0)
    totalLoss: float = Field(default=0.0)
    payout: float = Field(default=0.0)
    finalPayout: float = Field(default=0.0)
    onchainId: str
    createdAt: int
    updatedAt: int

    @field_validator('configId', 'locationId')
    @classmethod
    def id_must_be_nanoid(cls, v: str) -> str:
        nanoid = v.strip()
        if not is_valid_nanoid(nanoid):
            raise_with_log(ValueError, f"the id {nanoid} is not a valid nanoid")
        
        return nanoid

    @field_validator('locationId')
    @classmethod
    def location_must_exist(cls, v:str) -> str:
        nanoid = v.strip()
        collection = get_collection_for_class(LocationOut)
        if collection.count_documents({"_id": nanoid}) == 0:
            raise_with_log(ValueError, f"no location found for id {nanoid}")
        return nanoid

    @field_validator('configId')
    @classmethod
    def config_must_exist(cls, v:str) -> str:
        nanoid = v.strip()
        collection = get_collection_for_class(ConfigOut)
        if collection.count_documents({"_id": nanoid}) == 0:
            raise_with_log(ValueError, f"no config found for id {nanoid}")
        return nanoid

    @field_validator('crop')
    @classmethod
    def crop_must_be_valid(cls, v: str) -> str:
        crop = v.strip().lower()

        if crop not in VALID_CROPS:
            raise_with_log(ValueError, f"crop {crop} invalid, valid crops are {VALID_CROPS}")

        return crop


class RiskOut(Risk):
    id: str = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }


def from_risk_in(riskIn) -> Risk:
    return Risk(
        isValid=riskIn.isValid,
        configId=riskIn.configId,
        locationId=riskIn.locationId,
        crop=riskIn.crop,
        deductible=riskIn.deductible,
        startOfSeason=riskIn.startOfSeason,
        endOfSeason=riskIn.endOfSeason,
        draughtLoss=0.0,
        excessRainfallLoss=0.0,
        totalLoss=0.0,
        payout=0.0,
        finalPayout=0.0,
        onchainId="",
        createdAt=int(time.time()),
        updatedAt=int(time.time())
    )

def update_risk(risk, riskUpdateIn) -> Risk:
    risk.draughtLoss = riskUpdateIn.draughtLoss
    risk.excessRainfallLoss = riskUpdateIn.excessRainfallLoss
    risk.totalLoss = riskUpdateIn.totalLoss
    risk.payout = riskUpdateIn.payout
    risk.finalPayout = riskUpdateIn.finalPayout
    risk.updatedAt = int(time.time())
    return risk
