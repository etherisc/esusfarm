from datetime import datetime, timedelta
from util.logging import get_logger
from web3 import Web3

from server.model.config import ConfigOut
from server.model.location import LocationOut
from server.model.risk import RiskOut
from server.mongo import find_in_collection, update_in_collection
from server.sync.config import sync_config_onchain
from server.sync.location import sync_location_onchain
from server.sync.onchain import operator, product, riskSet

U_FIXED_EXP = 15

# setup for module
logger = get_logger()

def sync_risk_onchain(risk: RiskOut, force: bool = False) -> str:
    if not force and risk.tx:
        logger.info(f"risk {risk.id} already synched onchain (tx: {risk.tx})")
        if not risk.risk_id:
            risk.risk_id = get_risk_id(product.w3, risk.tx, risk.id)
        ensure_risk_payout_defined(risk)
        return risk.tx

    logger.info(f"synching risk {risk.id} onchain")

    # sync configuration (season) if not yet done
    config = find_in_collection(risk.configId, ConfigOut)
    sync_config_onchain(config, force)

    # sync risk if not yet done
    location = find_in_collection(risk.locationId, LocationOut)
    sync_location_onchain(location, force)

    # execute transaction
    id = product.toStr(risk.id)
    season_id = product.toStr(config.id)
    location_id = product.toStr(location.id)
    crop = product.toStr(risk.crop)
    season_end_at = int(
        (datetime.fromisoformat(config.startOfSeason) + timedelta(days=config.seasonDays)).timestamp())

    try:
        product.createCrop(crop, {"from": operator})
    except Exception as err:
        logger.info(f"createCrop {risk.crop} skipped or exists: {err}")

    tx = product.createRisk(id, season_id, location_id, crop, season_end_at, {'from': operator})
    logger.info(f"tx {tx} risk {risk.id} season {config.id} ({config.name}) location {location.id} ({location.latitude}/{location.longitude}) crop {risk.crop} created")

    # update risk with tx and risk id
    risk.tx = tx
    risk.risk_id = get_risk_id(product.w3, tx, risk.id)
    update_in_collection(risk, RiskOut)

    ensure_risk_payout_defined(risk)

    return tx


def ensure_risk_payout_defined(risk: RiskOut) -> None:
    """Set payout on-chain when missing; persist finalPayout in Mongo."""
    if not risk.tx:
        return
    if not risk.risk_id:
        risk.risk_id = get_risk_id(product.w3, risk.tx, risk.id)
    payout = risk.finalPayout if risk.finalPayout > 0 else max(risk.payout, 0.01)
    risk.finalPayout = payout
    risk_id_bytes = bytes.fromhex(
        risk.risk_id[2:] if risk.risk_id.startswith("0x") else risk.risk_id
    )
    onchain = product.getRisk(risk_id_bytes)
    if onchain and onchain[0] and onchain[1][-1]:
        update_in_collection(risk, RiskOut)
        return
    update_payout_factor_onchain(risk)
    update_in_collection(risk, RiskOut)


def get_risk_id(w3: Web3, tx: str, risk_nanoid: str) -> str:
    w3.eth.wait_for_transaction_receipt(tx)
    str_key = product.toStr(risk_nanoid)
    onchain_id = product.getRiskId(str_key)
    if hasattr(onchain_id, "hex"):
        h = onchain_id.hex()
        return h if h.startswith("0x") else f"0x{h}"
    return str(onchain_id)


def update_payout_factor_onchain(risk: RiskOut) -> str:
    if not risk.tx:
        logger.error(f"risk {risk.id} not synched onchain")
        return
    
    risk_id = risk.risk_id
    if not risk.risk_id:
        risk_id = get_risk_id(product.w3, risk.tx, risk.id)
    
    payout_factor = to_u_fixed(risk.finalPayout)
    logger.info(f"updating risk {risk.id} payout factor to {risk.finalPayout} ({payout_factor}) onchain")

    tx = product.updatePayoutFactor(risk_id, payout_factor, {'from': operator})
    logger.info(f"tx {tx} risk {risk.id} payout factor updated to {payout_factor}")

    return tx


def to_u_fixed(x: float) -> int:    
    return int(x * 10 ** U_FIXED_EXP)
