from util.logging import get_logger
from web3utils.blocks import wait_for_blocks
from web3utils.send_eth import send_eth
from web3utils.wallet import Wallet

from server.config import settings
from server.model.person import PersonOut
from server.mongo import update_in_collection
from server.sync.onchain import token, operator, product, w3

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
    funding = settings.FARMER_FUNDING_AMOUNT - balance

    # send tokens to wallet if balance is below threshold
    if balance < settings.FARMER_FUNDING_AMOUNT or force:

        # execute transaction
        tx = token.transfer(person.wallet, funding, {'from': operator})
        logger.info(f"tx {tx} funding of {funding} token to {person.wallet}")

        # update person with tx
        person.tx = tx
        update_in_collection(person, PersonOut)

        # fund wallet with eth for approval
        send_eth(operator, person.wallet, settings.FARMER_ETH_FUNDING_AMOUNT, settings.GAS_PRICE) 

        # initialze farmer wallet 
        farmer_wallet = Wallet.from_mnemonic(settings.FARMER_WALLET_MNEMONIC, index=person.walletIndex)
        product_token_handler = product.getTokenHandler()
        farmer_wallet_balance = w3.eth.get_balance(farmer_wallet.address)
        logger.info(f"farmer wallet {farmer_wallet.address} token handler {product_token_handler} approval of {settings.FARMER_FUNDING_AMOUNT} balance {farmer_wallet_balance}")
        
        # and approve token handler for policy payment
        tx2 = token.approve(product_token_handler, settings.FARMER_FUNDING_AMOUNT, {'from': farmer_wallet, 'gasPrice': settings.GAS_PRICE, 'gasLimit': 50000})
        logger.info(f"tx {tx2} approval of {funding} token to {product_token_handler}")
        
