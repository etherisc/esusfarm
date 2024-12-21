from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from server.config import settings
from server.model.person import PersonIn, PersonOut
from server.mongo import count_documents, create_in_collection, find_in_collection, get_list_of_models_in_collection, get_list_of_dicts_in_collection
from util.csv import write_csv_temp_file, get_field_list
from util.logging import get_logger
from web3_utils.wallet import Wallet


PATH_PREFIX = "/person"
TAGS = ["Person"]
PERSON_BASE_INDEX = 100000

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)
persons = {}

@router.post("/", response_model=PersonOut, response_description="Person data created")
async def create_person(person: PersonIn) -> PersonOut:
    # create unique wallet address for person
    persons = count_documents(PersonOut)
    wallet_index = PERSON_BASE_INDEX + persons
    wallet = Wallet.from_mnemonic(settings.FARMER_WALLET_MNEMONIC, index=wallet_index)

    # persist wallet info
    person_dict = person.toMongoDict()
    person_dict['walletIndex'] = wallet_index
    person_dict['wallet'] = wallet.address
    person_out = PersonOut.fromMongoDict(person_dict)

    return create_in_collection(person_out, PersonOut)


@router.get("/{person_id}", response_model=PersonOut, response_description="Person data obtained")
async def get_person(person_id: str) -> PersonOut:
    return find_in_collection(person_id, PersonOut)


@router.get("/all/json", response_model=list[PersonOut], response_description="Persons obtained")
async def get_all_persons(
    page:int = 1, 
    items:int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    logger.info(f"GET {PATH_PREFIX}/all/json")
    return get_list_of_models_in_collection(PersonOut, page, items)


@router.get("/all/csv", response_class=FileResponse, response_description="Locations csv created")
async def get_all_locations_csv(
    fields: str = settings.MODEL_CSV_PERSON_FIELDS, 
    delimiter: str = settings.MODEL_CSV_DELIMITER,
    page: int = 1, 
    items: int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    documents = get_list_of_dicts_in_collection(PersonOut, page, items)
    field_list = get_field_list(fields)
    return write_csv_temp_file(field_list, documents, delimiter)
