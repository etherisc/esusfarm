import iso3166

from pydantic import field_validator
from server.error import raise_with_log
from server.mongo import MongoModel

EXAMPLE_IN = {
    "country": "BF",
    "region": "Centre Nord",
    "province": "Sanmatenga",
    "department": "KAYA",
    "village": "Basberike",
    "latitude": 13.148262,
    "longitude": -1.0357304,
    "openstreetmap": "https://www.openstreetmap.org/#map=14/13.148262/-1.0357304",
    "coordinatesLevel": "VILLAGE"

}

EXAMPLE_OUT = EXAMPLE_IN
EXAMPLE_OUT["nanoId"] = "jxmbyupsh1rv"
EXAMPLE_OUT["onchainId"] = "0x9492fef57f9e671753f92b78a9958ada"

class LocationIn(MongoModel):
    country: str
    region: str
    province: str
    department: str
    village: str
    latitude: float
    longitude: float
    openstreetmap: str
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
    nanoId: str
    onchainId: str

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

