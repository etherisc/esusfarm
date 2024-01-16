from pydantic import BaseModel

EXAMPLE_IN = {
    "valid": True,
    "name": "MainSeasons2023",
    "year": 2023,
    "startOfSeason": 13,
    "endOfSeason": 32,
    "indexType": "WRSI",
    "dataSource": "CHIRPS",
    "triggerSevereLevel": 700000,
    "triggerSeverePayout": 1000000,
    "triggerMediumLevel": 800000,
    "triggerMediumPayout": 250000,
    "triggerWeakLevel": 900000,
    "triggerWeakPayout": 100000,
    "createdAt": 1700316957,
    "updatedAt": 1700316957,
}

EXAMPLE_OUT = EXAMPLE_IN
EXAMPLE_OUT["id"] = "0xbec1f9e54b04a83d0769850c936d37a8"

class ConfigIn(BaseModel):
    valid:bool
    name:str
    year:int
    startOfSeason:int
    endOfSeason:int
    indexType:str
    dataSource:str
    triggerSevereLevel:int
    triggerSeverePayout:int
    triggerMediumLevel:int
    triggerMediumPayout:int
    triggerWeakLevel:int
    triggerWeakPayout:int
    createdAt:int
    updatedAt:int

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_IN
        }

class ConfigOut(ConfigIn):
    id: str

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

