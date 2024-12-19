from pydantic import field_validator, Field
from app.server.model.claim import ClaimOut
from app.server.model.policy import PolicyOut
from server.error import raise_with_log
from server.mongo import MongoModel, get_collection_for_class
from util.nanoid import is_valid_nanoid

EXAMPLE_OUT = {
    "id": "jxmbyupsh1rv",
    "onChainId": "2689313703",
    "policyId": "7Zv4TZoBLxUi",
    "claimId": "7Zv4TZoBLxUi",
    "amount": 1000,
    "paidAt": 1700316957,
    "beneficiary": "0x2769786a7f3f3b3b3b3b3b3b3b3b3b3b3b3b3b3b",
    "createdAt": 1700316957,
    "updatedAt": 1700316957
}

class Payout(MongoModel):
    _id: str
    onChainId: str
    policyId: str
    claimId: str
    amount: int
    paidAt: int
    beneficiary: str
    createdAt: int
    updatedAt: int

    @field_validator('policyId', 'claimId')
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
    
    @field_validator('claimId')
    @classmethod
    def claim_must_exist(cls, v:str) -> str:
        nanoid = v.strip()
        collection = get_collection_for_class(ClaimOut)
        if collection.count_documents({"_id": nanoid}) == 0:
            raise_with_log(ValueError, f"no claim found for id {nanoid}")
        return nanoid


class PayoutOut(Payout):
    id: str = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": EXAMPLE_OUT
        }

