from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from server.config import settings
from server.model.location import LocationIn, LocationOut
from server.mongo import create_in_collection, find_in_collection, get_list_of_models_in_collection, get_list_of_dicts_in_collection

from util.csv import write_csv_temp_file, get_field_list
from util.logging import get_logger

PATH_PREFIX = "/location"
TAGS = ["Location"]

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)

@router.post("/", response_model=LocationOut, response_description="Location data created")
async def create_location(location: LocationIn):
    logger.info(f"POST {PATH_PREFIX} {location}")
    return create_in_collection(location, LocationOut)


@router.get("/{location_id}", response_description="Location data obtained")
async def get_single_location(location_id: str):
    return find_in_collection(location_id, LocationOut)


@router.get("/all/json", response_model=list[LocationOut], response_description="Locations obtained")
async def get_all_locations(page: int = 1, items: int = settings.MONGO_DOCUMENTS_PER_PAGE):
    logger.info(f"GET {PATH_PREFIX}/all/json")
    return get_list_of_models_in_collection(LocationOut, page, items)


@router.get("/all/csv", response_class=FileResponse, response_description="Locations csv created")
async def get_all_locations_csv(
    fields: str = settings.MODEL_CSV_LOCATION_FIELDS, 
    delimiter: str = settings.MODEL_CSV_DELIMITER,
    page: int = 1, 
    items: int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    documents = get_list_of_dicts_in_collection(LocationOut, page, items)
    field_list = get_field_list(fields)
    return write_csv_temp_file(field_list, documents, delimiter)
