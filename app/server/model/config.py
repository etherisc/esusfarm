from datetime import datetime

from pydantic import BaseModel, field_validator, Field
from server.error import raise_with_log
from server.mongo import MongoModel

EXAMPLE_IN = {
    "name": "MainSeasons2024",
    "startOfSeason": "2024-08-01",
    "endOfSeason": "2024-12-31"
}

EXAMPLE_OUT = EXAMPLE_IN
EXAMPLE_OUT["_id"] = "7Zv4TZoBLxUi"
EXAMPLE_OUT["year"] = 2014
EXAMPLE_OUT["seasonDays"] = 120

class ConfigIn(MongoModel):
    name:str
    startOfSeason:str
    endOfSeason:str

    @field_validator('startOfSeason', 'endOfSeason')
    @classmethod
    def date_must_be_iso(cls, v: str) -> str:
        date = v.strip()
        try:
            datetime.fromisoformat(date)
        except ValueError:
            raise ValueError("Provided string is not a valid ISO date.")
            raise_with_log(ValueError, f"date {date} is not iso format (YYYY-MM-DD)")

        return date

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_IN
        }

class ConfigOut(ConfigIn):
    _id: str
    year:int
    seasonDays:int
    id: str = Field(default=None)
    tx: str | None = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

