from pydantic import field_validator, Field
from server.model.policy import PolicyOut
from server.error import raise_with_log
from server.mongo import MongoModel, get_collection_for_class
from util.nanoid import is_valid_nanoid

EXAMPLE_OUT = {
    "id": "jxmbyupsh1rv",
    "onChainId": "2689313703",
    "policyId": "7Zv4TZoBLxUi",
    "claimAmount": 1000,
    "paidAmount": 500,
    "closedAt": 1700316957,
    "createdAt": 1700316957,
    "updatedAt": 1700316957
}

class Claim(MongoModel):
    _id: str
    onChainId: str
    policyId: str
    claimAmount: int
    paidAmount: int
    closedAt: int
    createdAt: int
    updatedAt: int

    @field_validator('policyId')
    @classmethod
    def id_must_be_nanoid(cls, v: str) -> str:
        nanoid = v.strip()
        if not is_valid_nanoid(nanoid):
            raise_with_log(ValueError, f"the id {nanoid} is not a valid nanoid")
        
        return nanoid

    @field_validator('policyId')
    @classmethod
    def policy_must_exist(cls, v:str) -> str:
        nanoid = v.strip()
        collection = get_collection_for_class(PolicyOut)
        if collection.count_documents({"_id": nanoid}) == 0:
            raise_with_log(ValueError, f"no policy found for id {nanoid}")
        return nanoid


class ClaimOut(Claim):
    id: str = Field(default=None)
    tx: str | None = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }


