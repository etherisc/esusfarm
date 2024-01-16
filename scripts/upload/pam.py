import os

from brownie import (
    accounts,
    web3,
    ArcModel,
    EXOF,
)

from datetime import datetime
from loguru import logger

from scripts.upload.util.csv import (
    load_csv, 
    write_csv_file
)

from scripts.upload.util.excel import get_data

from scripts.util import (
    contract_from_address, 
    from_block,
)

PROCESS_ID_ZERO = '0x0000000000000000000000000000000000000000000000000000000000000000'
SALT_DEFAULT = 'sR23coe+kc3wI8:6Z433/yv'

# assuming working directory /workspaces/wfp-accelerator/upload_data
FILE_PAM = './scripts/upload/data/Reporting_PAM_5500_Beneficiares_2023_Etherisc.fixed.xlsx'
FILE_PAM_LOG = './pam_log.csv'

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
}

SEX_PAM = {
    'F': 10,
    'M': 20
}

CROP_PAM = {
    'WRSI Fusion': 'Fusion',
    'WRSI Maïs': 'Maize',
    'WRSI Mil': 'Millet',
    'WRSI Sorgho': 'Sorghum',
    'M': 20
}

def hlp():
    print('from scripts.upload.pam import load, process_row, check_rows, hlp')
    print("mnemonic=''")
    print('data = load()')
    print('config_id = model.getConfigId(0)')
    print('is_final = False')
    print('set_gas_price = True')
    print("salt='sR23coe+kc3wI8:6Z433/yv'")
    print('row_num=2')
    print('(policy_id, risk_id, beneficiary_id, success) = process_row(data, row_num, config_id, model, product, mnemonic, is_final=is_final, salt=salt, set_gas_price=set_gas_price)')

def load_excel(file_name):
    # logger.info('get excel data, header: {}'.format(header))
    logger.info('get excel data, header: {}'.format(HEADER_PAM))
    data = get_data(file_name, HEADER_PAM, sheet_names=SHEETS_PAM)

    return data

def load():
    data = load_excel(FILE_PAM)

    logger.info('assumed last command: data = load()')
    logger.info("check first 1st excel row: data['Reporting PAM'][2]")

    return data


def process_rows(
    data, 
    row_offset:int, 
    row_count:int, 
    product,
    mapper,
    mnemonic,
    salt,
    is_final=False,
    set_gas_price=False
):
    model = contract_from_address(ArcModel, product.getModel())
    token = contract_from_address(EXOF, product.getToken())
    config_id = model.getConfigId(0)
    rows = 1

    for row_num in range(row_offset, row_offset + row_count):
        row = data[SHEETS_PAM[0]][row_num]
        yelen_id = row['Policy ID Yelen']
        mapper_id = int(yelen_id[4:])
        existing_process_id = mapper.getProcessId(mapper_id)
        po_balance = accounts.at(product.owner()).balance() / 10**18

        if po_balance < 0.05:
            logger.error(f"product owner balance {po_balance:.2f}. top up to contine")
            break

        if existing_process_id == PROCESS_ID_ZERO:
            logger.info(f"{yelen_id} ({mapper_id}) {rows}/{row_count} processing ... po_balance {po_balance:.2f}")

            (
                outcome, 
                process_id, 
                risk_id, 
                beneficiary_id
            ) = process_row(
                row, 
                yelen_id, 
                config_id, 
                model, 
                product,
                token,
                mnemonic,
                is_final=is_final,
                salt=salt,
                set_gas_price=set_gas_price)

            mapper.setProcessId(
                mapper_id, 
                process_id, 
                from_block(mapper.owner(), set_gas_price))
        else:
            logger.info(f"{yelen_id} ({mapper_id}) {rows}/{row_count} already processed {existing_process_id}")

        rows += 1


def process_row(
    row:dict, 
    yelen_id:str, 
    config_id, 
    model, 
    product,
    token,
    mnemonic,
    is_final=False,
    salt=SALT_DEFAULT,
    set_gas_price=False
):
    success = False
    policy_id = None
    beneficiary_id = None
    risk_id = None

    logger.debug(f"processing row {row}")

    location_id = model.toLocationId(
        row['Region'],
        row['Province'],
        row['Departements'],
        row['Villages de référence'],
        salt)

    if not model.isValidLocation(location_id):
        logger.info(f"adding location {row['Region']}, {row['Province']}, {row['Villages de référence']}")
        tx = product.setLocation(
            location_id,
            True, 
            from_block(product.owner(), set_gas_price))

        if web3.chain_id in [137]:
            tx.wait(2)


    index_type = row['Index Type']
    if index_type not in CROP_PAM:
        logger.error(f"invalid crop {index_type}")
        return (success, policy_id, risk_id, beneficiary_id)

    crop = CROP_PAM[index_type]
    risk_id = model.toRiskId(config_id, location_id, crop)

    index_refernce = int(row['Index Reference Value'] * 10**model.decimals())
    index_season = int(row['Index End of Season Value'] * 10**model.decimals())

    if not model.isValidRisk(risk_id):
        logger.info(f"adding risk {config_id}, {location_id}, {crop}")
        tx = product.createRisk(
            config_id, 
            location_id, 
            crop, 
            index_refernce, 
            index_season, 
            is_final, 
            from_block(product.owner(), set_gas_price))

        if web3.chain_id in [137]:
            tx.wait(2)

    yelen_num = int(yelen_id[2:])
    if yelen_id[:2] != "QF" or yelen_num < 100000 or yelen_num >= 200000:
        logger.error(f"invalid yelen policy {yelen_id}: expected id QF1...")
        return (success, policy_id, risk_id, beneficiary_id)

    beneficiary_id = model.toBeneficiaryId(
        yelen_id, 
        str(yelen_num), 
        salt)

    beneficiary_wallet = accounts.from_mnemonic(mnemonic, offset = yelen_num)

    sex_char = row['Sexe'].upper()
    if sex_char not in SEX_PAM:
        logger.error(f"invalid sex {sex_char}: expected F or M")
        return (success, policy_id, risk_id, beneficiary_id)

    sex = SEX_PAM[sex_char]

    subscription = row['Date de souscription']
    subscription_date = 0
    if isinstance(subscription_date, datetime):
        subscription_date = int(f"{subscription_date.year}{subscription_date.month:02}{subscription_date.day:02}")

    premium_amount = int(row["prime due à l'assureur"] * 10**token.decimals())
    sum_insured_amount = int(row["montant total assuré"] * 10**token.decimals())
    
    logger.info(f"creating policy {yelen_id} {beneficiary_wallet}, ({sex}), {risk_id}, {crop}, {premium_amount}, {sum_insured_amount}")
    underwrite = True
    tx = product.createPolicy(
        beneficiary_id, 
        beneficiary_wallet, 
        sex, 
        risk_id, 
        premium_amount,
        sum_insured_amount,
        subscription_date,
        underwrite,
        from_block(product.owner(), set_gas_price))

    if not 'LogArcPolicyCreated' in tx.events:
        logger.error(f"log entry 'LogArcPolicyCreated' missing in tx.events")
        return (success, policy_id, risk_id, beneficiary_id)
    else:
        policy_id = tx.events['LogArcPolicyCreated']['policyId']
        success = True

    return (success, policy_id, risk_id, beneficiary_id)


def check_rows(
    data, 
    row_offset:int, 
    row_count:int, 
    product,
    instance_service,
    salt,
    file_name
):
    model = contract_from_address(ArcModel, product.getModel())
    token = contract_from_address(EXOF, product.getToken())
    config_id = model.getConfigId(0)

    beneficiaries = {}

    process_ids = product.processIds()
    for idx in range(process_ids):
        process_id = str(product.getProcessId(idx))
        application = instance_service.getApplication(process_id).dict()
        application_data = product.decodeApplicationData(application['data']).dict()
        beneficiary_id = str(application_data['beneficiaryId'])
        beneficiaries[beneficiary_id] = process_id
        logger.debug(f"{idx} {process_ids} {beneficiary_id} {process_id}")

        if idx > row_count:
            break

    print("yelen_id outcome row_num process_id")
    data_out = {}

    for row_num in range(row_offset, row_offset + row_count):
        row = data[SHEETS_PAM[0]][row_num]
        (
            beneficiary_id,
            yelen_id,
            yelen_num,
            success
        ) = get_beneficiary_id(row, model, salt)

        process_id = None
        outcome = 'FAIL'

        if beneficiary_id in beneficiaries:
            outcome = 'OK'
            process_id = beneficiaries[beneficiary_id]

        row_id = f"row:{row_num}"
        data_out[row_id] = {
            'yelenId': yelen_id,
            'outcome': outcome,
            'row': row_num,
            'processId': process_id,
        }

        if row_num % 50 == 0:
            write_csv_file(
                ['yelenId','outcome','row','processId'], 
                data_out, 
                file_name)

        print(f"{yelen_id} {outcome} {row_num} {process_id}")


def get_beneficiary_id(row, model, salt):
    yelen_id = row['Policy ID Yelen']
    yelen_num = int(yelen_id[2:])
    success = True

    if yelen_id[:2] != "QF" or yelen_num < 100000 or yelen_num >= 200000:
        logger.error(f"invalid yelen policy {yelen_id} in row {row_num}: expected id QF1...")
        success = False

    beneficiary_id = str(model.toBeneficiaryId(
        yelen_id, 
        str(yelen_num), 
        salt))

    return (
        beneficiary_id,
        yelen_id,
        yelen_num,
        success)
