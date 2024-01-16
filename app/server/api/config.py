from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from data.onchain_data import get_config, get_configs
from server.config import settings
from server.model.config import ConfigOut
from util.csv import write_csv_temp_file, get_field_list
from util.logging import get_logger

PATH_PREFIX = "/config"
TAGS = ["Config"]

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)

@router.get("/{config_id}", response_model=ConfigOut, response_description="Config data obtained")
async def get_onchain_config(config_id:str):
    config = get_config(config_id)
    return ConfigOut.parse_obj(config)


@router.get("/all/json", response_model=list[ConfigOut], response_description="Configs obtained")
async def get_onchain_configs(
    page:int = 1, 
    items:int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    configs = get_configs(page, items)
    configs_out = []

    for config in configs:
        configs_out.append(ConfigOut.parse_obj(config))
    
    return configs_out

@router.get("/all/csv", response_class=FileResponse, response_description="Configs csv created")
async def get_configs_csv(
    fields:str = settings.MODEL_CSV_CONFIG_FIELDS, 
    delimiter:str = settings.MODEL_CSV_DELIMITER,
    page:int = 1, 
    items:int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    configs = get_configs(page, items)
    field_list = get_field_list(fields)
    return write_csv_temp_file(field_list, configs, delimiter)
