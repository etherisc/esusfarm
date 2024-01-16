import os

from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
from pymongo import MongoClient

from data.onchain_data import get_setup, get_location_id
from util.csv import load_csv
from util.excel import get_data
from util.nanoid import generate_nanoid_deterministic

DOT_ENV_PATH = 'server/.env'
COUNTRY='BF'


SHEETS_PAM = [
    "Reporting PAM"
]

HEADER_PAM = {
    'No': 'A',
    'Region': 'B',
    'Province': 'C',
    'Departements': 'D',
    'Villages de référence': 'F',
    'Sexe': 'H',
    'Numero de telephne': 'J',
    'Date de souscription': 'K',
    'Type de culture': 'L',
    'montant total assuré': 'P',
    "prime due à l'assureur": 'Q',
    'Policy ID Yelen': 'T',
    'Index Type': 'U',
    'Index Reference Value': 'Z',
    'Index End of Season Value': 'AA',
    'Year': 'AF',
    'Start of Season': 'AG',
    'End of Season': 'AH',
    'Trigger severe level': 'AJ',
    'Trigger severe payout': 'AK',
    'Trigger medium level': 'AL',
    'Trigger medium payout': 'AM',
    'Trigger weak level': 'AN',
    'Trigger weak payout': 'AO',
    'Payout estimated': 'AP',
}


INDEX_CROP = {
    'WRSI Fusion':'Fusion',
    'WRSI Maïs':'Maize',
    'WRSI Mil':'Millet',
    'WRSI Sorgho':'Sorghum'
}

# load .env file entries
load_dotenv(DOT_ENV_PATH)

data = {}
policies = {}
locations = {}
beneficiaries = {}

def load_yelen_data():
    load_dotenv(DOT_ENV_PATH)

    global data
    global policies
    global locations
    global beneficiaries

    excel_file = os.getenv('PAM_FILE')
    logger.info(f"reading yelen data from {excel_file}")

    data = get_data(excel_file, HEADER_PAM, sheet_names=SHEETS_PAM)
    policies = extract_policies(data)

    location_file = os.getenv('LOCATION_FILE')
    locations = load_locations(location_file)

    update_mongo(policies, locations)


def load_locations(location_file):
    locations_csv = load_csv(location_file, delimiter=';')
    locations = {}

    idx = 0
    for key, location_raw in locations_csv.items():
        if idx < 3:
            logger.info(f"key {key} location {location_raw}")

        location = location_raw
        location['latitude'] = float(location_raw['latitude'])
        location['longitude'] = float(location_raw['longitude'])

        nano_id = location['nanoId']
        locations[nano_id] = location
        idx += 1

    return locations


def update_mongo(policies, locations):
    mongo_url = os.getenv('MONGO_URL')

    if mongo_url[:10] != 'mongodb://':
        logger.warning(f"unexpeced MONGO_URL value '{mongo_url}': missing prefix 'mongodb://'. skipping mongodb refresh")
        return

    client = MongoClient(mongo_url)

    db_name = os.getenv('DB_NAME')
    if db_name is None or len(db_name) == 0:
        logger.warning(f"DB_NAME undefined. skipping mongodb refresh")
        return

    database = client[db_name]

    # clean and repopulate policies
    policies_name = os.getenv('COLLECTION_POLICIES')
    if policies_name is not None and len(policies_name) > 0:
        collection_policies = database[policies_name]    
        collection_policies.delete_many({})
        collection_policies.insert_many(list(policies.values()))
        logger.info(f"mongodb policies collection refreshed")
    else:
        logger.warning(f"COLLECTION_POLICIES undefined. skipping refresh of mongodb policies")

    # clean and repopulate policies
    locations_name = os.getenv('COLLECTION_LOCATIONS')
    if locations_name is not None and len(locations_name) > 0:
        collection_locations = database[locations_name]    
        collection_locations.delete_many({})
        collection_locations.insert_many(list(locations.values()))
        logger.info(f"mongodb locations collection refreshed")
    else:
        logger.warning(f"COLLECTION_LOCATIONS undefined. skipping refresh of mongodb locations")



def get_policies_data(page:int, items:int) -> dict:
    global policies
    plcs = list(policies.values())
    idx_start = (page - 1) * items
    idx_end = idx_start + items
    logger.info(f"plcs {len(plcs)} start {idx_start} end {idx_end} first {plcs[idx_start]}")
    return plcs[idx_start:idx_end]


def get_policy_data(yelen_id) -> dict:
    global policies
    return policies[yelen_id]


def get_location(location_nano_id:str) ->  dict:
    global locations

    if location_nano_id in locations:
        return locations[location_nano_id]
    
    logger.error(f"no location found for nano_id {location_nano_id}")
    return None


def get_locations(page:int = 1, items:int = 5) ->  dict:
    global locations
    locs = list(locations.values())
    idx_start = (page - 1) * items
    idx_end = idx_start + items
    logger.info(f"locs {len(locs)} start {idx_start} end {idx_end} first {locs[idx_start]}")
    return locs[idx_start:idx_end]


def extract_policies(data:dict) -> dict:
    policies = {}

    logger.info('extracting policies from data')
    sheet = data['Reporting PAM']

    for key, row in sheet.items():
        policy_id = row['Policy ID Yelen']
        region = row['Region']
        province = row['Province']
        department = row['Departements']
        village = row['Villages de référence']

        policy = {
            'year': row['Year'],
            'seasonStart': row['Start of Season'],
            'seasonEnd': row['End of Season'],
            'indexType': row['Index Type'],
            'crop': INDEX_CROP[row['Index Type']],
            'locationNanoId': get_location_nanoid(region,province,department,village),
            'region': region,
            'province': province,
            'department': department,
            'village': village,
            'beneficiarySex': row['Sexe'].upper(),
            'yelenId': policy_id,
            'subscriptionDate': row['Date de souscription'],
            'premium': row["prime due à l'assureur"],
            'sumInsured': row['montant total assuré'],

            'triggerSevere': row['Trigger severe level'],
            'payoutSevere': row['Trigger severe payout'],
            'triggerMedium': row['Trigger medium level'],
            'payoutMedium': row['Trigger medium payout'],
            'triggerLow': row['Trigger weak level'],
            'payoutLow': row['Trigger weak payout'],

            'indexReferenceValue': row['Index Reference Value'], 
            'indexEndOfSeasonValue': row['Index End of Season Value'], 
            'indexRatio': row['Index End of Season Value']/row['Index Reference Value'],
            'hasPayout': True if row['Payout estimated'] > 0 else False, 
            'payoutEstimated': row['Payout estimated']
        }

        policies[policy_id] = policy

    logger.info(f"number of policies extracted: {len(policies.keys())}")
    return policies


def extract_locations(data:dict) -> dict:
    locs = {}

    logger.info('extracting unique locations from data')
    sheet = data['Reporting PAM']

    for key, row in sheet.items():
        region = row['Region']
        province = row['Province']
        department = row['Departements']
        village = row['Villages de référence']
        name = f"{COUNTRY} {province} {village}"
        nano_id = get_location_nanoid(region,province,department,village)

        if nano_id not in locs:
            locs[nano_id] = {
                "nanoId": nano_id,
                "name": name,
                "country": COUNTRY,
                "region": region,
                "province": province,
                "department": department,
                "village": village,
            }

    logger.info(f"number of locations extracted: {len(locs.keys())}")
    return locs


def get_location_nanoid(region,province,department,village):
    return generate_nanoid_deterministic(
            f"{region}:{province}:{department}:{village}")
