from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from server.config import settings
from server.model.location import LocationIn, LocationOut
from server.mongo import create_in_collection, find_in_collection, get_list_of_models_in_collection, get_list_of_dicts_in_collection

from data.offchain_data import load_yelen_data, get_location, get_locations
from data.onchain_data import get_location_id, to_hex
from util.csv import write_csv_temp_file, get_field_list
from util.logging import get_logger

PATH_PREFIX = "/location"
TAGS = ["Location"]
MONGO = False

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)

if MONGO:
    @router.post("/", response_model=LocationOut, response_description="Location data created")
    async def create_location(location: LocationIn):
        return create_in_collection(location, LocationOut)
else:
    load_yelen_data()

@router.get("/{location_nano_id}", response_description="Location data obtained")
async def get_single_location(location_nano_id: str):
    if MONGO:
        return find_in_collection(location_nano_id, LocationOut)
    else:
        return get_location(location_nano_id)


@router.get("/all/json", response_model=list[LocationOut], response_description="Locations obtained")
async def get_all_locations(page: int = 1, items: int = settings.MONGO_DOCUMENTS_PER_PAGE):
    if MONGO:
        return get_list_of_models_in_collection(LocationOut, page, items)
    else:
        return [LocationOut.parse_obj(location) for location in get_locations(page, items)]


@router.get("/all/csv", response_class=FileResponse, response_description="Locations csv created")
async def get_all_locations_csv(
    fields: str = settings.MODEL_CSV_LOCATION_FIELDS, 
    delimiter: str = settings.MODEL_CSV_DELIMITER,
    page: int = 1, 
    items: int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    if MONGO:
        documents = get_list_of_dicts_in_collection(LocationOut, page, items)
        field_list = get_field_list(fields)
        return write_csv_temp_file(field_list, documents, delimiter)
    else:
        locations = get_locations(page, items)
        field_list = get_field_list(fields)
        csv_file_path = write_csv_temp_file(field_list, locations, delimiter)

        response = FileResponse(csv_file_path, media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=locations.csv"

        return response
