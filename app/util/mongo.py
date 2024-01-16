import json
import sys

from pymongo import MongoClient
from util.logging import get_logger

logger = get_logger()

def get_client(db_uri:str) -> MongoClient:
    logger.info(f"connecting to mongo {db_uri} ...")
    mongo = MongoClient(db_uri)
    logger.info(f"connected with database {mongo.get_database().name}")
    return mongo


def get_collection(mongo, collection_name, create=False):
    db = mongo.get_database()

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
    logger.info(f"read mongo db pipeline from file {pipeline_file}")

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
