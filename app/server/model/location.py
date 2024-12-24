import iso3166

from copy import deepcopy
from pydantic import field_validator, Field
from server.error import raise_with_log
from server.mongo import MongoModel

EXAMPLE_IN = {
    "country": "UG",
    "zone": "Central",
    "district": "MASAKA",
    "subcounty": "Kabonera",
    "village": "Kiziba",
    "latitude": -0.4365,
    "longitude": 31.6780,
    "coordinatesLevel": "VILLAGE",
}

EXAMPLE_OUT = deepcopy(EXAMPLE_IN)
EXAMPLE_OUT["_id"] = "kDho7606IRdr"
EXAMPLE_OUT["openstreetmap"] = "https://www.openstreetmap.org/#map=14/-0.4365/31.6780",

class LocationIn(MongoModel):
    country: str
    zone: str
    district: str
    subcounty: str
    village: str
    latitude: float
    longitude: float
    coordinatesLevel: str

    @field_validator('country')
    @classmethod
    def country_must_be_iso_alpha2(cls, v: str) -> str:
        country_code = v.lower()
        country_code_length = len(country_code)
        if len(v) != 2:
            raise_with_log(ValueError, f"country code has length={country_code_length}, expected length is 2")
        if not country_code in iso3166.countries:
            raise_with_log(ValueError, f"country code {country_code} is not iso3166 code")

        return country_code

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_IN
        }

class LocationOut(LocationIn):
    _id: str
    openstreetmap: str| None = Field(default=None)
    id: str = Field(default=None)
    tx: str | None = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

