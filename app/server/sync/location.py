from util.logging import get_logger

from server.config import settings
from server.model.location import LocationOut
from server.mongo import update_in_collection
from server.sync.onchain import operator, product

# setup for module
logger = get_logger()

def sync_location_onchain(location: LocationOut, force: bool = False):
    if not force and location.tx:
        logger.info(f"location {location.id} already synched onchain (tx: {location.tx})") 
        return

    logger.info(f"synching location {location.id} onchain")

    id = product.toStr(location.id)
    latitude = int(location.latitude * 10 ** settings.LOCATION_DECIMALS)
    longitude = int(location.longitude * 10 ** settings.LOCATION_DECIMALS)

    # execute transaction
    tx = product.createLocation(id, latitude, longitude, {'from': operator})
    logger.info(f"tx {tx} location {location.id} latitude {latitude} longitude {longitude} created")

    # update location with tx
    location.tx = tx
    update_in_collection(location, LocationOut)
