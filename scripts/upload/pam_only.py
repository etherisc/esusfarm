import os

from datetime import datetime
from loguru import logger
from pymongo import MongoClient

from scripts.upload.util.csv import load_csv

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "wfp-api"
COLLECTION_NAME = "policies"
POLICIES_CSV = "./scripts/upload/policies.csv"
DELIMITER = ';'

def help():
    print('from scripts.upload.pam_only import load help')
    print("data = load('./server/upload/policies.csv')")


def reset_mongo() -> list:
    client = MongoClient(MONGO_URI)
    database = client[DATABASE_NAME]
    collection = database[COLLECTION_NAME]    

    # load policy data from csv file
    policies = list(load_csv(POLICIES_CSV, delimiter=DELIMITER).values())
    policies_processed = [process_policy(policy) for policy in policies]

    # clean and repopulate collection content
    collection.delete_many({})
    collection.insert_many(policies)


def process_policiy(policy):
    policy_out = policy

    return policy_out