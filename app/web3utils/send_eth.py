from server.sync.onchain import w3
from util.logging import get_logger
from web3utils.wallet import Wallet

logger = get_logger()

def send_eth(sender: Wallet, rcpt: str, amount: int, gas_price: int) -> str:
    """Send a specified amount of wei to a specified address."""
    nonce = w3.eth.get_transaction_count(sender.account.address)
    tx = {
        'nonce': nonce,  #prevents from sending a transaction twice on ethereum
        'to': rcpt,
        'value': w3.to_wei(amount, 'wei'),
        'gas': 21000,
        'gasPrice': gas_price,
        'chainId': w3.eth.chain_id
    }
    signed_tx = w3.eth.account.sign_transaction(tx, sender.account.key)
    logger.info(f"Sending {amount} wei to {rcpt}")
    #send the transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    logger.info(f"Transaction sent: {tx_hash.hex()}")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info(f"Transaction mined: {tx_hash}")
    