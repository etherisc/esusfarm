# from web3 import Web3
from eth_account import Account
from typing import Tuple

def generate_eth_account() -> Tuple[str, str, str]:
    """
    Generates a new random Ethereum account and returns its address, private key and mnemonic. 
    """

    Account.enable_unaudited_hdwallet_features()
    (account, mnemonic) = Account.create_with_mnemonic()

    return account.address, account.key.to_0x_hex(), mnemonic

def main():
    (address, private_key, mnemonic) = generate_eth_account()
    print(f"ETH_ADDRESS={address}")
    print(f"ETH_PRIVATE_KEY={private_key}")
    print(f'ETH_MNEMONIC="{mnemonic}"')

if __name__ == "__main__":
    main()

