"""Idempotent create by externalId."""

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from server.mongo import MongoModel, get_collection_for_class
from util.logging import get_logger

logger = get_logger()

PERSON_COMPARE = (
    "locationId",
    "firstName",
    "lastName",
    "gender",
    "mobilePhone",
)


def _person_payload(doc: dict) -> dict:
    return {k: doc.get(k) for k in PERSON_COMPARE}


def _policy_payload(model: MongoModel) -> dict:
    return model.idempotency_payload()


def find_by_external_id(cls: type, external_id: str) -> dict | None:
    collection = get_collection_for_class(cls)
    return collection.find_one({"externalId": external_id})


def assert_idempotent_match(
    cls: type,
    external_id: str,
    incoming_payload: dict,
    payload_fn,
) -> object | None:
    existing = find_by_external_id(cls, external_id)
    if existing is None:
        return None
    existing_model = cls.fromMongoDict(existing)
    existing_payload = payload_fn(existing_model)
    if existing_payload == incoming_payload:
        logger.info(f"idempotent externalId={external_id} on {cls.__name__}")
        return existing_model
    raise HTTPException(
        status_code=409,
        detail=f"externalId {external_id} already exists with different data",
    )


def insert_with_external_id(obj: MongoModel, cls_out: type, insert_fn):
    try:
        return insert_fn(obj, cls_out)
    except DuplicateKeyError:
        existing = find_by_external_id(cls_out, obj.externalId)  # type: ignore[attr-defined]
        if existing:
            raise HTTPException(status_code=409, detail="duplicate externalId conflict")
        raise