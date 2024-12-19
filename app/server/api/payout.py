from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from server.model.payout import PayoutOut
from server.config import settings
from server.mongo import find_in_collection, get_list_of_models_in_collection, get_list_of_dicts_in_collection

from util.csv import write_csv_temp_file, get_field_list
from util.logging import get_logger

PATH_PREFIX = "/payout"
TAGS = ["Payout"]

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)
persons = {}

@router.get("/{payout_id}", response_model=PayoutOut, response_description="Payout data obtained")
async def get_payout(payout_id: str) -> PayoutOut:
    return find_in_collection(payout_id, PayoutOut)


@router.get("/all/json", response_model=list[PayoutOut], response_description="Payouts obtained")
async def get_all_payouts(
    page: int = 1, 
    items: int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    logger.info(f"GET {PATH_PREFIX}/all/json")
    return get_list_of_models_in_collection(PayoutOut, page, items)


@router.get("/all/csv", response_class=FileResponse, response_description="Payouts csv created")
async def get_all_payouts_csv(
    fields: str = settings.MODEL_CSV_PAYOUT_FIELDS, 
    delimiter: str = settings.MODEL_CSV_DELIMITER,
    page: int = 1, 
    items: int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    documents = get_list_of_dicts_in_collection(PayoutOut, page, items)
    field_list = get_field_list(fields)
    return write_csv_temp_file(field_list, documents, delimiter)

