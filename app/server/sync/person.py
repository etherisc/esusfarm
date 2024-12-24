from util.logging import get_logger

from server.config import settings
from server.model.person import PersonOut
from server.mongo import update_in_collection
from server.sync.onchain import token, operator

# setup for module
logger = get_logger()

def sync_person_onchain(person: PersonOut, force: bool = False):
    if not force and person.tx:
        logger.info(f"person {person.id} already synched onchain (tx: {person.tx})") 
        return

    logger.info(f"synching person {person.id} onchain")

    # check balance of wallet
    balance = token.balanceOf(person.wallet)
    logger.info(f"balance {balance} (min amount {settings.FARMER_FUNDING_AMOUNT}) for wallet {person.wallet}")

    # send tokens to wallet if balance is below threshold
    if balance < settings.FARMER_FUNDING_AMOUNT:
        funding = settings.FARMER_FUNDING_AMOUNT - balance

        # execute transaction
        tx = token.transfer(person.wallet, funding, {'from': operator})
        logger.info(f"tx {tx} funding of {funding} token to {person.wallet}")

        # update person with tx
        person.tx = tx
        update_in_collection(person, PersonOut)

