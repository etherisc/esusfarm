from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from server.config import settings
from server.api.util import verify_person_exists, verify_risk_exists
from server.model.policy import PolicyIn, PolicyOut
from server.mongo import create_in_collection, find_in_collection

from data.offchain_data import get_policy_data, get_policies_data
from data.onchain_data import get_onchain_onboarding_data, amend_onchain_data
from util.csv import write_csv_temp_file, get_field_list
from util.logging import get_logger

PATH_PREFIX = "/policy"
TAGS = ["Policy"]

MONGO = False

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)

if MONGO:
    @router.post("/", response_model=PolicyOut, response_description="Policy data created")
    async def create_policy(policy: PolicyIn) -> PolicyOut:
        verify_person_exists(policy.person_id)
        verify_risk_exists(policy.risk_id)
        return create_in_collection(policy, PolicyOut)

@router.get("/{policy_id}", response_description="Policy data obtained")
async def get_policy(policy_id: str):
    if MONGO:
        return find_in_collection(policy_id, PolicyOut)
    else:
        return get_policy_data(policy_id)

@router.get("/{policy_id}/onchain", response_description="Policy onchain data obtained")
async def get_onchain_policy_data(policy_id: str) -> dict:
    return get_onchain_onboarding_data(policy_id)


@router.get("/all/json", response_description="Policies data obtained")
async def get_all_policies(page:int = 1, items:int = settings.MONGO_DOCUMENTS_PER_PAGE):
    return get_policies_data(page, items)


@router.get("/all/csv", response_class=FileResponse, response_description="Policies csv created")
async def get_all_policies_csv(
    fields: str = settings.MODEL_CSV_POLICY_FIELDS, 
    delimiter: str = settings.MODEL_CSV_DELIMITER,
    page: int = 1, 
    items: int = settings.MONGO_DOCUMENTS_PER_PAGE
) -> dict:
    policies = get_policies_data(page, items)
    field_list = get_field_list(fields)
    csv_file_path = write_csv_temp_file(field_list, policies, delimiter)

    response = FileResponse(csv_file_path, media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=policies.csv"

    return response
