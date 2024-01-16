from server.model.location import LocationOut
from server.model.risk import RiskOut
from server.model.person import PersonOut
from server.mongo import find_in_collection
from util.logging import get_logger

logger = get_logger()

def verify_location_exists(location_id: str) -> None:
    logger.info(f"verifying existence of location for id {location_id}")
    find_in_collection(location_id, LocationOut)

def verify_risk_exists(risk_id: str) -> None:
    logger.info(f"verifying existence of risk for id {risk_id}")
    find_in_collection(risk_id, RiskOut)

def verify_person_exists(person_id: str) -> None:
    logger.info(f"verifying existence of person for id {person_id}")
    find_in_collection(person_id, PersonOut)
