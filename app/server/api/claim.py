from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from server.model.claim import ClaimOut
from server.config import settings
from server.mongo import find_in_collection, get_list_of_models_in_collection, get_list_of_dicts_in_collection

from util.csv import write_csv_temp_file, get_field_list
from util.logging import get_logger

PATH_PREFIX = "/claim"
TAGS = ["Claim"]

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)
persons = {}

@router.get("/{claim_id}", response_model=ClaimOut, response_description="Claim data obtained")
async def get_claim(claim_id: str) -> ClaimOut:
    return find_in_collection(claim_id, ClaimOut)


@router.get("/all/json", response_model=list[ClaimOut], response_description="Claims obtained")
async def get_all_claims(
    page: int = 1, 
    items: int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    logger.info(f"GET {PATH_PREFIX}/all/json")
    return get_list_of_models_in_collection(ClaimOut, page, items)


@router.get("/all/csv", response_class=FileResponse, response_description="Claims csv created")
async def get_all_claims_csv(
    fields: str = settings.MODEL_CSV_CLAIM_FIELDS, 
    delimiter: str = settings.MODEL_CSV_DELIMITER,
    page: int = 1, 
    items: int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    documents = get_list_of_dicts_in_collection(ClaimOut, page, items)
    field_list = get_field_list(fields)
    return write_csv_temp_file(field_list, documents, delimiter)

