from datetime import datetime, timedelta
from util.logging import get_logger

from server.model.config import ConfigOut
from server.model.location import LocationOut
from server.model.risk import RiskOut
from server.mongo import find_in_collection, update_in_collection
from server.sync.config import sync_config_onchain
from server.sync.location import sync_location_onchain
from server.sync.onchain import operator, product

# setup for module
logger = get_logger()

def sync_risk_onchain(risk: RiskOut):
    if risk.tx:
        logger.info(f"risk {risk.id} already synched onchain (tx: {risk.tx})")
        return

    logger.info(f"synching risk {risk.id} onchain")

    # sync configuration (season) if not yet done
    config = find_in_collection(risk.configId, ConfigOut)
    sync_config_onchain(config)

    # sync risk if not yet done
    location = find_in_collection(risk.locationId, LocationOut)
    sync_location_onchain(location)

    # execute transaction
    id = product.toStr(risk.id)
    season_id = product.toStr(config.id)
    location_id = product.toStr(location.id)
    crop = product.toStr(risk.crop)
    season_end_at = int(
        (datetime.fromisoformat(config.startOfSeason) + timedelta(days=config.seasonDays)).timestamp())

    tx = product.createRisk(id, season_id, location_id, crop, season_end_at, {'from': operator})
    logger.info(f"tx {tx} risk {risk.id} season {config.id} ({config.name}) location {location.id} ({location.latitude}/{location.longitude}) crop {risk.crop} created")

    # update risk with tx
    risk.tx = tx
    update_in_collection(risk, RiskOut)
