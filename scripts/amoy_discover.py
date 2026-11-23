#!/usr/bin/env python3
"""Read on-chain CropProduct metadata on Polygon Amoy (requires RPC_NODE_URL)."""

import os
import sys

from web3 import Web3

LEGACY_PRODUCT = "0x6d39A6458ABa448d3C5cbC00f2135352197e6091"
INSTANCE = "0x193491245A42d336ae5Fcb2d622d386041498a22"
REGISTRY = "0x7c19A25EF52c4E25Eb793d53B18F1811cE947455"
OPERATOR = "0xad8308964bcB8BfaCa77A625478D4D4E683CD433"


def main() -> None:
    rpc = os.getenv("RPC_NODE_URL", "https://rpc-amoy.polygon.technology/")
    product_addr = os.getenv("PRODUCT_CONTRACT_ADDRESS", LEGACY_PRODUCT)
    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        sys.exit("RPC not connected")
    print("chain_id", w3.eth.chain_id)
    print("operator", OPERATOR, "balance_wei", w3.eth.get_balance(OPERATOR))
    product_abi = [
        {"inputs": [], "name": "getInstance", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
        {"inputs": [], "name": "getToken", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
        {"inputs": [], "name": "getNftId", "outputs": [{"type": "uint96"}], "stateMutability": "view", "type": "function"},
    ]
    c = w3.eth.contract(address=w3.to_checksum_address(product_addr), abi=product_abi)
    print("product", product_addr)
    instance = c.functions.getInstance().call()
    print("getInstance", instance)
    print("getToken", c.functions.getToken().call())
    print("getNftId", c.functions.getNftId().call())
    instance_abi = [
        {"inputs": [], "name": "getRegistry", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    ]
    inst = w3.eth.contract(address=w3.to_checksum_address(instance), abi=instance_abi)
    print("registry", inst.functions.getRegistry().call())
    if not os.getenv("PRODUCT_CONTRACT_ADDRESS"):
        print("instance_default", INSTANCE)
        print("registry_default", REGISTRY)


if __name__ == "__main__":
    main()