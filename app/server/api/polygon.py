import os

from fastapi.routing import APIRouter

# from server.config import settings
from data.onchain_data import get_setup
from util.logging import get_logger

POLYGON_SCAN = 'https://polygonscan.com/address'
PATH_PREFIX = "/polygon"
TAGS = ["Polygon"]

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)

@router.get("/", response_description="Onchain config data obtained")
async def get_contract_links() -> dict:
    (
        _,
        mapper,
        product,
        model,
        instance_service
    ) = get_setup()

    return {
        'mapper': f"{POLYGON_SCAN}/{mapper.address}",
        'product': f"{POLYGON_SCAN}/{product.address}",
        'model': f"{POLYGON_SCAN}/{model.address}",
        'instanceService': f"{POLYGON_SCAN}/{instance_service.address}",
        'salt': os.getenv('SALT')
    }
