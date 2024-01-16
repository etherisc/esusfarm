from fastapi.routing import APIRouter

from server.api.util import verify_location_exists
from server.model.person import PersonIn, PersonOut
from server.mongo import create_in_collection, find_in_collection
from util.logging import get_logger

PATH_PREFIX = "/person"
TAGS = ["Person"]

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)
persons = {}

@router.post("/", response_model=PersonOut, response_description="Person data created")
async def create_person(person: PersonIn) -> PersonOut:
    verify_location_exists(person.location_id)
    return create_in_collection(person, PersonOut)

@router.get("/", response_model=PersonOut, response_description="Person data obtained")
async def get_person(person_id: str) -> PersonOut:
    return find_in_collection(person_id, PersonOut)
