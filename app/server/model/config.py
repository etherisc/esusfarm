from pydantic import BaseModel, Field
from server.error import raise_with_log
from server.mongo import MongoModel

EXAMPLE_IN = {
    "valid": True,
    "name": "MainSeasons2024",
    "year": 2024,
    "startOfSeason": "2024-08-01",
    "endOfSeason": "2024-12-31",
    "seasonDays": 120,
    "franchise": 0.1,
    "createdAt": 1700316957,
    "updatedAt": 1700316957,
}

EXAMPLE_OUT = EXAMPLE_IN
EXAMPLE_OUT["_id"] = "7Zv4TZoBLxUi"

class ConfigIn(MongoModel):
    valid:bool
    name:str
    year:int
    startOfSeason:str
    endOfSeason:str
    seasonDays:int
    franchise:float
    createdAt:int
    updatedAt:int

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_IN
        }

class ConfigOut(ConfigIn):
    _id: str
    id: str = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

