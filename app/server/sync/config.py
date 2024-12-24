from util.logging import get_logger

from server.config import settings
from server.model.config import ConfigOut
from server.mongo import update_in_collection
from server.sync.onchain import operator, product

# setup for module
logger = get_logger()

def sync_config_onchain(config: ConfigOut, force: bool = False):
    if not force and config.tx:
        logger.info(f"config {config.id} already synched onchain (tx: {config.tx})") 
        return

    logger.info(f"synching config {config.id} onchain")

    id = product.toStr(config.id)
    year = config.year
    name = product.toStr(config.name)
    season_start = product.toStr(config.name)
    season_end = product.toStr(config.name)
    season_days = config.seasonDays

    # execute transaction
    tx = product.createSeason(id, year, name, season_start, season_end, season_days, {'from': operator})
    logger.info(f"tx {tx} config {config.id} year {config.year} name {config.name} created")

    # update config with tx
    config.tx = tx
    update_in_collection(config, ConfigOut)
