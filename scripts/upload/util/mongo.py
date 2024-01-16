import json
import sys

from loguru import logger
from pymongo import MongoClient


def get_client(db_uri:str) -> MongoClient:
    return MongoClient(db_uri)


def get_collection(mongo, db_name, collection_name, create=False):
    # check if db exists
    if not db_name in mongo.list_database_names():
        if create:
            pass
        else:
            logger.error(f"no database '{db_name}' found in {mongo}")
            return None

    db = mongo[db_name]

    # check source collection exists
    if not collection_name in db.list_collection_names():
        if create:
            logger.info(f"creating collection '{collection_name}' in db")
            db.create_collection(collection_name)
        else:
            logger.error(f"no collection '{collection_name}' found in db")
            return None

    return db[collection_name]


def get_pipeline(pipeline_file:str):
    with open(pipeline_file, 'r') as file:
        pipeline = json.load(file)    
    
    return pipeline


def count_documents(collection, count_pipeline_file):
    pipeline = get_pipeline(count_pipeline_file)
    result_set = collection.aggregate(pipeline)
    nxt = next(iter(result_set), {'count': 0})
    logger.info('pipeline {} next {} result_set {}'.format(count_pipeline_file, nxt, result_set))
    count = nxt['count']
    return count


def document_exists(collection, filter_criteria) -> bool:
    return collection.count_documents(filter_criteria) > 0 