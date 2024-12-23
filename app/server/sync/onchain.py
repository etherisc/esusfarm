from util.logging import get_logger
from web3 import Web3
from web3utils.contract import Contract
from web3utils.wallet import Wallet

from server.config import settings

# setup for module
logger = get_logger()

w3 = Web3(Web3.HTTPProvider(settings.RPC_NODE_URL))
product = Contract(w3, "CropProduct", settings.PRODUCT_CONTRACT_ADDRESS, out_path="./app/abi")
token = Contract(w3, "AccountingToken", settings.TOKEN_CONTRACT_ADDRESS, out_path="./app/abi")

operator = Wallet.from_mnemonic(settings.OPERATOR_WALLET_MNEMONIC)

