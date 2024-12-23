from datetime import datetime

from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from server.config import settings
from server.error import raise_with_log
from server.model.config import ConfigIn, ConfigOut
from server.mongo import create_in_collection, find_in_collection, get_list_of_models_in_collection, get_list_of_dicts_in_collection

from util.csv import write_csv_temp_file, get_field_list
from util.logging import get_logger

PATH_PREFIX = "/config"
TAGS = ["Config"]

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)


@router.post("/", response_model=ConfigOut, response_description="Config data created")
async def create_config(config: ConfigIn):
    logger.info(f"POST {PATH_PREFIX} {config}")

    # check season start and end and calculate season days
    season_start = datetime.fromisoformat(config.startOfSeason)
    season_end = datetime.fromisoformat(config.endOfSeason)
    if season_start >= season_end:
        raise_with_log(ValueError, f"season start {config.startOfSeason} must be before season end {config.endOfSeason}")

    document = config.toMongoDict()
    document['year'] = season_start.year
    document['seasonDays'] = (season_end - season_start).days + 1
    config = ConfigOut.fromMongoDict(document)

    return create_in_collection(config, ConfigOut)


@router.get("/all/json", response_model=list[ConfigOut], response_description="Configs obtained")
async def get_onchain_configs(
    page:int = 1, 
    items:int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    logger.info(f"GET {PATH_PREFIX}/all/json")
    return get_list_of_models_in_collection(ConfigOut, page, items)


@router.get("/all/csv", response_class=FileResponse, response_description="Configs csv created")
async def get_configs_csv(
    fields:str = settings.MODEL_CSV_CONFIG_FIELDS, 
    delimiter:str = settings.MODEL_CSV_DELIMITER,
    page:int = 1, 
    items:int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    configs = get_list_of_dicts_in_collection(ConfigOut, page, items)
    field_list = get_field_list(fields)
    return write_csv_temp_file(field_list, configs, delimiter)
