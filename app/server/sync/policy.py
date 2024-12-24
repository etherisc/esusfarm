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
    risk_id_str = product.toStr(risk.id)
    risk_id = product.getRiskId(risk_id_str)
    subscription_date = datetime.fromisoformat(policy.subscriptionDate)
    activate_at = int(subscription_date.timestamp())
    sum_insured = int(policy.sumInsuredAmount * 10 ** token.decimals())
    premium = int(policy.premiumAmount * 10 ** token.decimals())

    logger.info(f"creating policy policy_holder {policy_holder} risk_id {risk_id} activate_at {activate_at} sum_insured {sum_insured} premium {premium}")
    tx = product.createPolicy(policy_holder, risk_id, activate_at, sum_insured, premium, {'from': operator, 'gasLimit': 10000000, 'gasPrice': settings.GAS_PRICE})

    logger.info(f"{tx} onchain policy {policy.id} created")

    # update policy with tx and nft id
    # logs = product.get_logs({'fromBlock':'latest'})
    # log_policy = product.contract.events.LogCropPolicyCreated.process_log(logs[0])
    # policy.nft = log_policy.args['policyNftId']
    policy.tx = tx
    update_in_collection(policy, PolicyOut)
