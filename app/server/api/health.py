from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from server.mongo import get_mongo
from util.logging import get_logger

PATH_PREFIX = "/health"
TAGS = ["Health"]

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)


@router.get("/ping", response_description="endpoint that returns OK when server is up and running")
async def get_health_ping() -> JSONResponse:
    logger.info(f"GET {PATH_PREFIX}/ping")
    return JSONResponse(
        content = { 
            "response": "OK"
        })


@router.get("/ping_mongo", response_description="returns state and infor regarding mongodb client")
async def get_health_ping_mongo() -> JSONResponse:
    logger.info(f"GET {PATH_PREFIX}/ping_mongo")
    (status, database) = get_mongo_client_status()
    return JSONResponse(
        content = { 
            "status": status,
            "database": database
        })


def get_mongo_client_status() -> tuple[str, str]:
    try:
        mongo = get_mongo()
        database = mongo.get_default_database().name
        logger.info(f"attempt to ping mongdb {database}")
        mongo.admin.command('ping')
        return ("connected", database)
    except Exception as e:
        return (f"error in connection: {e}", None)