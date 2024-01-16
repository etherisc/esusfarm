from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from server.config import settings
from server.model.risk import RiskIn, RiskOut
from server.mongo import create_in_collection, find_in_collection

from data.onchain_data import get_risk, get_risks
from util.csv import write_csv_temp_file, get_field_list
from util.logging import get_logger

PATH_PREFIX = "/risk"
TAGS = ["Risk"]

MONGO = False

# setup for module
logger = get_logger()
router = APIRouter(prefix=PATH_PREFIX, tags=TAGS)

if MONGO:
    @router.post("/", response_model=RiskOut, response_description="Risk data created")
    async def create_risk(risk: RiskIn) -> RiskOut:
        verify_location_exists(risk.location_id)
        return create_in_collection(risk, RiskOut)


@router.get("/{risk_id}", response_model=RiskOut, response_description="Risk data obtained")
async def get_onchain_risk(risk_id: str) -> RiskOut:
    if MONGO:
        return find_in_collection(risk_id, RiskOut)
    else:
        risk = get_risk(risk_id)
        return RiskOut.parse_obj(risk)


@router.get("/all/json", response_model=list[RiskOut], response_description="Risks obtained")
async def get_onchain_risks(
    page:int = 1, 
    items:int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    risks = get_risks(page, items)
    risks_out = []

    for risk in risks:
        risks_out.append(RiskOut.parse_obj(risk))
    
    return risks_out


@router.get("/all/csv", response_class=FileResponse, response_description="Risks csv created")
async def get_onchain_risks_csv(
    fields:str = settings.MODEL_CSV_RISK_FIELDS, 
    delimiter:str = settings.MODEL_CSV_DELIMITER,
    page:int = 1, 
    items:int = settings.MONGO_DOCUMENTS_PER_PAGE
):
    risks = get_risks(page, items)
    field_list = get_field_list(fields)
    csv_file_path = write_csv_temp_file(field_list, risks, delimiter)

    response = FileResponse(csv_file_path, media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=risks.csv"

    return response
