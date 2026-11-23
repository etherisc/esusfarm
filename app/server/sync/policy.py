from datetime import datetime
from util.logging import get_logger

from server.config import settings
from server.mongo import find_in_collection, update_in_collection
from server.model.person import PersonOut
from server.model.policy import PolicyOut
from server.model.risk import RiskOut
from server.sync.onchain import operator, product, token

from server.sync.person import sync_person_onchain
from server.sync.risk import sync_risk_onchain
from util.money import major_to_base_units

# setup for module
logger = get_logger()

def sync_policy_onchain(policy: PolicyOut, force: bool = False):
    if not force and policy.tx:
        logger.info(f"policy {policy.id} already synced onchain (nft {policy.nft}")
        return

    logger.info(f"synching policy {policy.id} onchain")

    # sync person if not yet done
    person = find_in_collection(policy.personId, PersonOut)
    sync_person_onchain(person, force)

    # sync risk if not yet done
    risk = find_in_collection(policy.riskId, RiskOut)
    sync_risk_onchain(risk, force)

    # execute transaction
    policy_holder = person.wallet
    if risk.risk_id:
        risk_id = bytes.fromhex(risk.risk_id[2:] if risk.risk_id.startswith("0x") else risk.risk_id)
    else:
        risk_id_str = product.toStr(risk.id)
        risk_id = product.getRiskId(risk_id_str)
    subscription_date = datetime.fromisoformat(policy.subscriptionDate)
    activate_at = int(subscription_date.timestamp())
    sum_insured = major_to_base_units(policy.sum_insured_decimal)
    premium = major_to_base_units(policy.premium_decimal)

    logger.info(f"creating policy policy_holder {policy_holder} risk_id {risk_id} activate_at {activate_at} sum_insured {sum_insured} premium {premium}")
    tx = product.createPolicy(policy_holder, risk_id, activate_at, sum_insured, premium, {'from': operator, 'gasLimit': 10000000, 'gasPrice': settings.GAS_PRICE})

    logger.info(f"{tx} onchain policy {policy.id} created")

    # update policy with tx
    policy.tx = tx

    # update policy with policy nft
    receipt = product.w3.eth.wait_for_transaction_receipt(tx)
    if receipt["status"] != 1:
        raise RuntimeError(f"createPolicy reverted: {tx}")
    logs = receipt["logs"]
    logger.debug(f"policy {policy.id} transaction logs {logs}")

    policy_nft_id = None
    for log in logs:
        if log["address"].lower() != product.address.lower():
            continue
        try:
            policy_nft_id = product.contract.events.LogCropPolicyCreated().process_log(
                log
            ).args.policyNftId
            break
        except Exception:
            continue
    if policy_nft_id is None:
        raise RuntimeError(f"LogCropPolicyCreated not found in tx {tx}")
    policy.nft = policy_nft_id
    update_in_collection(policy, PolicyOut)
