import sys

from os import getenv

from fastapi import HTTPException
from pydantic import BaseModel
from pymongo import MongoClient

from server.config import settings
from server.error import NotFoundError, raise_with_log
from util.logging import get_logger
from util.mongo import (
    get_client,
    get_collection,
    get_pipeline,
    count_documents
)
from util.nanoid import generate_nanoid, is_valid_nanoid

class MongoModel(BaseModel):

    def toMongoDict(this) -> dict:
        model = this.dict()
        model_id = None

        if not settings.MONGO_ID_ATTRIBUTE in model:
            model[settings.MONGO_ID_ATTRIBUTE] = generate_nanoid()
        
        return model

    @classmethod
    def fromMongoDict(cls, model:dict):
        if model is None:
            raise_with_log(ValueError, f"None not allowed as mongo dict model")

        id_attr = settings.MONGO_ID_ATTRIBUTE
        if not id_attr in model:
            raise_with_log(ValueError, f"Id attribugte '{id_attr}' missing in dict")

        modelOut = cls(**model)
        modelOut.id = model[id_attr]
        return modelOut

logger = get_logger()
mongo_client_available = False
mongo_client = None

mongo_collections = {}


def create_in_collection(obj, cls):
    collection = get_collection_for_object(obj)
    document = obj.toMongoDict()
    document_id = document[settings.MONGO_ID_ATTRIBUTE]

    if not document_id or len(document_id) == 0:
        document_id = generate_nanoid()
        document[settings.MONGO_ID_ATTRIBUTE] = document_id

    collection.insert_one(document)
    logger.info(f"document {document} for id {document_id} created in {collection.name}")
    model = cls.fromMongoDict(document)
    return model


def find_in_collection(obj_id: str, cls):
    if not is_valid_nanoid(obj_id):
        raise_with_log(ValueError, f"id {obj_id} is not a valid nanoid");

    collection = get_collection_for_class(cls)
    logger.info(f"fetching document with id {obj_id} from {collection.name}")
    document = collection.find_one({settings.MONGO_ID_ATTRIBUTE: obj_id})

    if document is None:
        raise_with_log(NotFoundError, f"no document found for id {obj_id} in collection {collection.name}")

    return cls.fromMongoDict(document)


def get_list_of_models_in_collection(cls, page: int, items_per_page: int):
    collection_name = get_collection_name_for_class(cls)
    logger.info(f"fetching from {collection_name} page {page} items {items_per_page}")
    result_set = _get_list_as_result_set(cls, page, items_per_page)

    documents = []
    for document in result_set:
        documents.append(cls.fromMongoDict(document))
    
    return documents


def get_list_of_dicts_in_collection(cls, page: int, items_per_page: int):
    result_set = _get_list_as_result_set(cls, page, items_per_page)

    documents = []
    for document in result_set:
        document[settings.MODEL_ID_ATTRIBUTE] = document[settings.MONGO_ID_ATTRIBUTE]
        del document[settings.MONGO_ID_ATTRIBUTE]
        documents.append(document)
    
    return documents


def _get_list_as_result_set(cls, page: int, items_per_page: int):
    collection = get_collection_for_class(cls)
    logger.info(f"fetching documents from {collection.name}, page: {page}, items: {items_per_page}")

    pages_count = int((collection.count_documents({}) + items_per_page - 1) / items_per_page)
    if page > 1 and page > pages_count:
        raise_with_log(ValueError, f"page {page} > expected number of pages ({pages_count})")

    skip_count = (page - 1) * items_per_page
    return collection.find().skip(skip_count).limit(items_per_page)


def get_collection_for_object(obj):
    collection_name = get_collection_name_for_object(obj)
    return get_mongo_collection(collection_name)

def get_collection_for_class(cls):
    collection_name = get_collection_name_for_class(cls)
    return get_mongo_collection(collection_name)


def get_collection_name_for_object(obj) -> str:
    if not isinstance(obj, MongoModel):
        raise_with_log(ValueError, f"object class not derived from MongoModel")

    return get_collection_name_for_class(obj.__class__)


def get_collection_name_for_class(cls) -> str:
    class_name = cls.__name__

    if class_name.endswith("In"):
        return class_name[:-2]
    elif class_name.endswith("Out"):
        return class_name[:-3]
    else:
        raise_with_log(ValueError, f"object class name '{class_name}' not ending with 'In' or 'Out'")


def get_mongo_collection(collection_name: str): 
    global mongo_collections

    if collection_name in mongo_collections:
        logger.debug(f"fetching collection {collection_name} from cache")
        return mongo_collections[collection_name]

    client = get_mongo()
    create_collection = settings.MONGO_CREATE_COLLECTIONS
    collection = get_collection(client, collection_name, create_collection)

    if collection is not None:
        mongo_collections[collection_name] = collection
    else:
        logger.error(f"failed to load collection {collection_name}")
    
    return collection


def get_mongo() -> MongoClient:
    global mongo_client_available
    global mongo_client

    if mongo_client_available:
        logger.debug(f"fetching mongo client from cache")
        return mongo_client

    logger.info(f"creating new mongo client")
    mongo_uri = get_mongo_uri()
    mongo_client = get_client(mongo_uri)

    if isinstance(mongo_client, MongoClient):
        mongo_client_available = True

    return mongo_client


def get_mongo_uri() -> str:
    mongo_url = getenv('MONGO_URL')
    if mongo_url and len(mongo_url) > 0:
        return mongo_url
    
    mongo_user = getenv('MONGO_USERNAME')
    mongo_pass = getenv('MONGO_PASSWORD')
    mongo_host = getenv('MONGO_HOSTNAME')
    mongo_port = getenv('MONGO_PORT')
    mongo_db = getenv('MONGO_DB')

    if not mongo_db or len(mongo_db) == 0:
        logger.error(f"environment variable MONGO_DB undefined, existing...")
        sys.exit(13)

    if not mongo_host or len(mongo_host) == 0:
        mongo_host = "host.docker.internal"

    if not mongo_port or len(mongo_port) == 0:
        mongo_port = "27017"

    if mongo_user and len(mongo_user) > 0:
        return f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/{mongo_db}"
    else:
        return f"mongodb://{mongo_host}:{mongo_port}/{mongo_db}"
