from typing import List
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from server.model.payout import PayoutOut
from server.model.claim import ClaimOut
from server.config import settings
from server.api.util import verify_person_exists, verify_risk_exists
from server.model.policy import PolicyIn, PolicyOut
from server.mongo import create_in_collection, find_in_collection, get_collection_for_class, get_list_of_models_in_collection, get_list_of_dicts_in_collection

from data.offchain_data import get_policy_data, get_policies_data
from data.onchain_data import get_onchain_onboarding_data, amend_onchain_data
from util.csv import write_csv_temp_file, get_field_list
from util.logging import get_logger

PATH_PREFIX = "/policy"
TAGS = ["Policy"]

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)

@router.post("/", response_model=PolicyOut, response_description="Policy data created")
async def create_policy(policy: PolicyIn) -> PolicyOut:
    verify_person_exists(policy.personId)
    verify_risk_exists(policy.riskId)
    return create_in_collection(policy, PolicyOut)


@router.get("/{policy_id}", response_description="Policy data obtained")
async def get_policy(policy_id: str):
    return find_in_collection(policy_id, PolicyOut)

@router.get("/{policy_id}/claims", summary="Get all claims for a policy", response_description="Policy claim data obtained")
async def get_claims(policy_id: str) -> List[ClaimOut]:
    claim_collection = get_collection_for_class(ClaimOut)
    claims = claim_collection.find({"policyId": policy_id})
    return [ClaimOut.fromMongoDict(c) for c in claims]

@router.get("/{policy_id}/payouts", summary="Get all payouts for a policy", response_description="Policy payout data obtained")
async def get_payouts(policy_id: str) -> List[PayoutOut]:
    payout_collection = get_collection_for_class(PayoutOut)
    payouts = payout_collection.find({"policyId": policy_id})
    return [PayoutOut.fromMongoDict(p) for p in payouts]


# @router.get("/{policy_id}/onchain", response_description="Policy onchain data obtained")
# async def get_onchain_policy_data(policy_id: str) -> dict:
#     return get_onchain_onboarding_data(policy_id)


@router.get("/all/json", response_description="Policies data obtained")
async def get_all_policies(page:int = 1, items:int = settings.MONGO_DOCUMENTS_PER_PAGE):
    logger.info(f"GET {PATH_PREFIX}/all/json")
    return get_list_of_models_in_collection(PolicyOut, page, items)


@router.get("/all/csv", response_class=FileResponse, response_description="Locations csv created")
async def get_all_locations_csv(
    fields: str = settings.MODEL_CSV_LOCATION_FIELDS, 
    delimiter: str = settings.MODEL_CSV_DELIMITER,
    page: int = 1, 
    items: int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    documents = get_list_of_dicts_in_collection(PolicyOut, page, items)
    field_list = get_field_list(fields)
    return write_csv_temp_file(field_list, documents, delimiter)
