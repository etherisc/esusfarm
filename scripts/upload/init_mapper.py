from brownie import (
    accounts,
    Mapper,
)

from loguru import logger

from scripts.upload.util.csv import load_csv

from scripts.util import (
    contract_from_address, 
    from_block,
)

PROCESS_ID_ZERO = '0x0000000000000000000000000000000000000000000000000000000000000000'

def init(pam_file_name, mapper_address, max_rows=10000, set_gas_price=False):
    data = load_csv(pam_file_name)
    mapper = contract_from_address(Mapper, mapper_address)
    owner = mapper.owner()
    rows = 0

    for (key, value) in data.items():
        if rows > max_rows:
            break

        yelen_id = data[key]['yelenId']
        outcome = data[key]['outcome']
        process_id = data[key]['processId']

        if outcome == 'OK' and yelen_id[:4] == 'QF10':
            id = int(yelen_id[4:])

            existing_process_id = mapper.getProcessId(id)
            if existing_process_id == PROCESS_ID_ZERO:
                logger.info(f"{yelen_id} ({id}) setting {process_id} ...")
                mapper.setProcessId(id, process_id, from_block(owner, set_gas_price))
                rows += 1
            else:
                logger.info(f"{yelen_id} ({id}) already processed {existing_process_id}")