import json
import os

from dotenv import load_dotenv
from loguru import logger
from web3 import Web3

DOT_ENV_PATH = './server/.env'

INFURA='Infura'
ALCHEMY='Alchemy'
NODE=ALCHEMY

# load .env file entries
load_dotenv(DOT_ENV_PATH)

def help():
    print('from dotenv import load_dotenv')
    print('from data.onchain_data import get_setup, get_config, to_hex, help')
    print('')
    print("load_dotenv('./server/.env')")
    print('(w3, mapper, product, model, instance_service) = get_setup()')
    print('')
    print('mapper.functions.ids().call()')
    print('yelen_id = mapper.functions.getId(478).call() ')
    print('process_id = mapper.functions.getProcessId(yelen_id).call() ')
    print('(state, premium, sum_insured, data, created_at, updated_at) = instance_service.functions.getApplication(process_id).call()')
    print('(risk_id, beneficiary_id, sex, location_id, crop, subscription_date) = product.functions.decodeApplicationData(data).call()')
    print('(valid, config_id, location_id, crop, index_reference, index_season, is_final, created_at, updated_at) = model.functions.getRisk(risk_id).call()')
    print('(valid,name,year,start,end,index,source,trg_severe,pay_severe,trg_med,pay_med,trg_low,pay_low,created_at,updated_at) = model.functions.getConfig(config_id).call()')
    print('name,year,start,end,index,source,trg_severe,trg_med,trg_low')
    print('')

# connect to rpc node
def get_web3():
    loaded = load_dotenv(DOT_ENV_PATH)
    if not loaded:
        logger.warning(f"failed to load .env file {DOT_ENV_PATH}, assuming variable are defined externally")
    else:
        logger.info(f".env file {DOT_ENV_PATH} successfully loaded")

    endpoint = os.getenv('WEB3_INFURA_ENDPOINT')
    key = os.getenv('WEB3_INFURA_PROJECT_ID')

    if NODE == ALCHEMY:
        endpoint = os.getenv('WEB3_ALCHEMY_ENDPOINT')
        key = os.getenv('WEB3_ALCHEMY_PROJECT_ID')

    logger.info(f"using {NODE} rpc node")
    return Web3(Web3.HTTPProvider(f"{endpoint}/{key}"))
    
# returns a web3 contract object given its abi file and contract address
def get_contract(web3, contract_file_name, contract_address):
    abi = None

    with open(contract_file_name) as f:
        abi = json.load(f)['abi']

    if abi is None:
        return None
    else:
        return web3.eth.contract(
            address=contract_address, 
            abi=abi)

# get polygon setup to query wfp contracts
def get_setup():
    web3 = get_web3()
    mapper = get_contract(web3, os.getenv('MAPPER_FILE'), os.getenv('MAPPER_ADDRESS'))
    product = get_contract(web3, os.getenv('PRODUCT_FILE'), os.getenv('PRODUCT_ADDRESS'))
    model = get_contract(web3, os.getenv('MODEL_FILE'), os.getenv('MODEL_ADDRESS'))
    instance_service = get_contract(web3, os.getenv('INSTANCE_SERVICE_FILE'), os.getenv('INSTANCE_SERVICE_ADDRESS'))

    return (
        web3,
        mapper,
        product,
        model,
        instance_service)


def get_config(model, config_idx=0):
    config_id = model.functions.getConfigId(config_idx).call()
    config = model.functions.getConfig(config_id).call()
    return tuple([to_hex(config_id)]) + config


def to_hex(data:bytes):
    if not isinstance(data, bytes):
        logger.error(f"not type bytes: {data} but type {type(data)}")
        return None

    return '0x' + ''.join(format(byte, '02x') for byte in data)


def to_bytes(data_hex):
    if not isinstance(data_hex, str):
        logger.error(f"not type hex: {data_hex} but type {type(data_hex)}")
        return None

    if data_hex[:2] != '0x':
        logger.error(f"not starting with '0x: {data_hex}")
        return None

    return bytes.fromhex(data_hex[2:])


def get_location_id(region,province,department,village):
    salt = os.getenv('SALT')
    logger.info(f"getting onchain location id for {region} {province} {department} {village} salt {salt}")
    (w3, mapper, product, model, instance_service) = get_setup()
    location_id = model.functions.toLocationId(
        region,province,department,village,salt).call()
    return to_hex(location_id)


def get_risk(risk_id:str):
    logger.info(f"getting onchain risk for {risk_id} ...")
    (w3, mapper, product, model, instance_service) = get_setup()
    risk = model.functions.getRisk(to_bytes(risk_id)).call()
    risk_dict = get_risk_dict(risk_id, risk)
    logger.info(f"obtained risk {risk_dict}")
    return risk_dict


def get_risks(page:int, items:int):
    logger.info(f"getting onchain risks for page {page} with items {items}...")
    (_, _, _, model, _) = get_setup()

    idx_start = (page - 1) * items
    idx_end = idx_start + items

    risks_count = model.functions.risks().call()
    if idx_start > risks_count:
        raise ValueError(f"requeste page number too big")
    
    if idx_end > risks_count:
        idx_end = risks_count

    risks = []
    for idx in range(idx_start, idx_end):
        risk_id = to_hex(model.functions.getRiskId(idx).call())
        logger.info(f"getting onchain risk {idx-idx_start+1}/{idx_end-idx_start} at {idx} {risk_id}")
        risks.append(get_risk(risk_id))

    return risks


def get_config(config_id:str):
    logger.info(f"getting onchain config for {config_id} ...")
    (w3, mapper, product, model, instance_service) = get_setup()
    config = model.functions.getConfig(to_bytes(config_id)).call()
    return get_config_dict(config_id, config)


def get_configs(page:int, items:int):
    if page > 1:
        raise ValueError('page > 1 not supported')

    (w3, mapper, product, model, instance_service) = get_setup()
    num_configs = model.functions.configs().call()

    if num_configs > items:
        raise ValueError('too many items')

    configs = []
    for idx in range(num_configs):
        config_id = model.functions.getConfigId(idx).call()
        config = model.functions.getConfig(config_id).call()
        configs.append(get_config_dict(config_id, config))

    return configs


def get_risk_dict(risk_id, risk):
    if isinstance(risk_id, bytes):
        risk_id = to_hex(risk_id)

    return {
        'id': risk_id,
        'isValid': risk[0],
        'configId': to_hex(risk[1]),
        'locationId': to_hex(risk[2]),
        'crop': risk[3],
        'indexReferenceValue': risk[4],
        'indexSeasonValue': risk[5],
        'indexIsFinal': risk[6],
        'createdAt':risk[7],
        'updatedAt':risk[8]
    }


def get_config_dict(config_id, config):
    if isinstance(config_id, bytes):
        config_id = to_hex(config_id)

    return {
        'id': config_id,
        'valid':config[0],
        'name':config[1],
        'year':config[2],
        'startOfSeason':config[3],
        'endOfSeason':config[4],
        'indexType':config[5],
        'dataSource':config[6],
        'triggerSevereLevel':config[7],
        'triggerSeverePayout':config[8],
        'triggerMediumLevel':config[9],
        'triggerMediumPayout':config[10],
        'triggerWeakLevel':config[11],
        'triggerWeakPayout':config[12],
        'createdAt':config[13],
        'updatedAt':config[14],
    }


def get_onchain_onboarding_data(yelen_id:str) -> dict:
    if yelen_id[:4] != "QF10":
        logger.error(f"yelen_id {yelen_id} not matching expected prefix 'QF10'")
        return None

    (
        _,
        mapper,
        product,
        model,
        instance_service
    ) = get_setup()

    yelen_num = int(yelen_id[4:])
    process_id = mapper.functions.getProcessId(yelen_num).call()

    (
        application_state, 
        premium, 
        sum_insured, 
        application_data, 
        application_created_at, 
        application_updated_at
    ) = instance_service.functions.getApplication(process_id).call()

    (
        risk_id, 
        beneficiary_id, 
        sex, 
        location_id, 
        crop, 
        subscription_date
    ) = product.functions.decodeApplicationData(application_data).call()

    (
        beneficiary_wallet,
        beneficiary_sex
    ) = model.functions.getBeneficiary(beneficiary_id).call()

    (
        risk_valid, 
        config_id, 
        location_id, 
        crop, 
        index_reference, 
        index_season, 
        is_final, 
        risk_created_at, 
        risk_updated_at
    ) = model.functions.getRisk(risk_id).call()

    (
        config_valid,
        config_name,
        year,
        season_start,
        season_end,
        index,
        data_source,
        trg_severe,
        pay_severe,
        trg_med,
        pay_med,
        trg_low,
        pay_low,
        config_created_at,
        config_updated_at
    ) = model.functions.getConfig(config_id).call()

    claims = instance_service.functions.claims(process_id).call()
    payouts = instance_service.functions.payouts(process_id).call()

    onchain_policy_data = {
        'year': year,
        'seasonStart': season_start,
        'seasonEnd': season_end,
        'indexType': index,
        'dataSource': data_source,
        'riskId': to_hex(risk_id),
        'configId': to_hex(config_id),
        'locationId': to_hex(location_id),
        'crop': crop,
        'beneficiaryId': to_hex(beneficiary_id), 
        'beneficiaryWallet': beneficiary_wallet, 
        'beneficiarySex': beneficiary_sex,
        'yelenId': yelen_id,
        'processId': to_hex(process_id),
        # 'subscriptionDate': subscription_date,
        'premium': premium,
        'sumInsured': sum_insured,
        'triggerSevere': trg_severe,
        'payoutSevere': pay_severe,
        'triggerMedium': trg_med,
        'payoutMedium': pay_med,
        'triggerLow': trg_low,
        'payoutLow': pay_low,
        'indexReferenceValue': index_reference, 
        'indexEndOfSeasonValue': index_season, 
        'indexIsFinal': is_final,
        'claims': claims,
        'payouts': payouts,
    }

    logger.info(f"collected onchain policy data {onchain_policy_data}")

    # only amend if no claims data so far
    if onchain_policy_data['claims'] == 0 and not onchain_policy_data['indexIsFinal']:
        onchain_policy_data = amend_onchain_data(
            onchain_policy_data,
            product)

    return onchain_policy_data


def amend_onchain_data(onchain_policy_data, product):
    d = onchain_policy_data
    amended = {}

    sum_insured = d['sumInsured']
    payout_amount = product.functions.calculatePayoutAmount(
        to_bytes(d['configId']),
        d['indexReferenceValue'],
        d['indexEndOfSeasonValue'],
        sum_insured
    ).call()

    payout_ratio = payout_amount / sum_insured
    trigger_type_estimate = None
    if payout_ratio == 1:
        trigger_type_estimate = 'Severe'
    elif payout_ratio > 0.24:
        trigger_type_estimate = 'Medium'
    elif payout_ratio > 0.24:
        trigger_type_estimate = 'Weak'

    d['indexRatioEstimate'] = d['indexEndOfSeasonValue']/d['indexReferenceValue']
    d['triggerTypeEstimate'] = trigger_type_estimate
    d['payoutEstimate'] = payout_amount

    amended['indexRatioEstimate'] = d['indexRatioEstimate']
    amended['triggerTypeEstimate'] = trigger_type_estimate
    amended['payoutEstimate'] = payout_amount

    logger.info(f"data amended {amended}")
    return d