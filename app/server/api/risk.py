import time
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from server.model.payout import Payout, PayoutOut
from server.model.person import PersonOut
from server.model.claim import Claim, ClaimOut
from server.model.policy import PolicyOut
from server.config import settings
from server.model.risk import RiskIn, RiskUpdateIn, RiskOut, Risk, from_risk_in, update_risk
from server.mongo import create_in_collection, find_in_collection, get_collection_for_class, get_list_of_models_in_collection, get_list_of_dicts_in_collection, update_in_collection

from data.onchain_data import get_risk, get_risks
from util.csv import write_csv_temp_file, get_field_list
from util.logging import get_logger

PATH_PREFIX = "/risk"
TAGS = ["Risk"]


# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)

@router.post("/", response_model=RiskOut, response_description="Risk data created")
async def create_risk(riskIn: RiskIn) -> RiskOut:
    return create_in_collection(from_risk_in(riskIn), RiskOut)

@router.put("/{risk_id}", response_model=RiskOut, response_description="Risk data updated")
async def update_risk_data(riskUpdateIn: RiskUpdateIn) -> RiskOut:
    risk = find_in_collection(riskUpdateIn.id, RiskOut)
    risk = update_risk(risk, riskUpdateIn)
    return update_in_collection(risk, RiskOut)

@router.post("/{risk_id}/process_policies", response_description="Policies processed")
async def process_policies(risk_id: str) -> bool:
    policies_collection = get_collection_for_class(PolicyOut)
    num_policies = policies_collection.count_documents({'riskId': risk_id})
    policies = policies_collection.find({'riskId': risk_id})
    logger.info(f"processing {num_policies} policies for risk {risk_id}")

    for p in policies:
        policy = PolicyOut.fromMongoDict(p)
        person = find_in_collection(policy.personId, PersonOut)
        logger.info(f"processing policy {policy.id} for risk {risk_id}")
        claim = Claim(
            onChainId = "",
            policyId = policy.id,
            claimAmount = 1000,
            paidAmount=1000,
            closedAt=int(time.time()),
            createdAt=int(time.time()),
            updatedAt=int(time.time())
        )
        claim = create_in_collection(claim, ClaimOut)
        payout = Payout(
            onChainId = "",
            policyId = policy.id,
            claimId = claim.id,
            amount = claim.claimAmount,
            paidAt = claim.closedAt,
            beneficiary = person.wallet,
            createdAt = int(time.time()),
            updatedAt = int(time.time())
        )
        create_in_collection(payout, PayoutOut)
    
    return True



@router.get("/{risk_id}", response_model=RiskOut, response_description="Risk data obtained")
async def get_single_risk(risk_id: str) -> RiskOut:
    return find_in_collection(risk_id, RiskOut)


@router.get("/all/json", response_model=list[RiskOut], response_description="Risks obtained")
async def get_all_risks(
    page:int = 1, 
    items:int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    logger.info(f"GET {PATH_PREFIX}/all/json")
    return get_list_of_models_in_collection(RiskOut, page, items)


@router.get("/all/csv", response_class=FileResponse, response_description="Risks csv created")
async def get_onchain_risks_csv(
    fields:str = settings.MODEL_CSV_RISK_FIELDS, 
    delimiter:str = settings.MODEL_CSV_DELIMITER,
    page:int = 1, 
    items:int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    documents = get_list_of_dicts_in_collection(RiskOut, page, items)
    field_list = get_field_list(fields)
    return write_csv_temp_file(field_list, documents, delimiter)
