from brownie import (
    interface,
    history,
    network,
    web3,
    Contract
)

def transfer(
    account_a,
    account_b,
    amount,
    set_gas_price=False
):
    if set_gas_price:
        account_a.transfer(account_b, amount, gas_price=web3.eth.gas_price)
    else:
        account_a.transfer(account_b, amount)

def from_block(
    sender,
    set_gas_price
):
    if set_gas_price:
        return {
            'from': sender,
            'gas_price': web3.eth.gas_price
        }

    return {
            'from': sender
    }


def deploy_lib(
    lib_class, 
    deployer_account,
    set_gas_price=False,
    publish_source=False
):
    deploy(
        lib_class,
        deployer_account,
        set_gas_price=set_gas_price,
        publish_source=publish_source)

    return contract_from_address(lib_class, history[-1].contract_address)


def deploy(
    contract_class,
    deployer_account,
    set_gas_price=False,
    publish_source=False
):
    return deploy_with_args(
        contract_class, 
        [], 
        deployer_account, 
        set_gas_price=set_gas_price,
        publish_source=publish_source)

def deploy_with_args(
    contract_class,
    constructor_args,
    deployer_account,
    set_gas_price=False,
    publish_source=False
):
    if constructor_args is None:
        constructor_args=[]

    contract = None
    if set_gas_price:
        contract = contract_class.deploy(
            *constructor_args, 
            {
                'from': deployer_account,
                'gas_price': web3.eth.gas_price,
            },
            publish_source=publish_source)
    else:
        contract = contract_class.deploy(
            *constructor_args, 
            { 'from': deployer_account },
            publish_source=publish_source)

    return contract

import io
import json
import sys

from contextlib import redirect_stdout
from datetime import datetime
from web3 import Web3

from brownie.network.contract import Contract

from brownie import (
    chain,
    web3,
)

def unix_timestamp() -> int:
    return int(datetime.now().timestamp())

def contract_from_address(contractClass, contractAddress):
    return Contract.from_abi(contractClass._name, contractAddress, contractClass.abi)

from brownie import accounts, config, project
from brownie.convert import to_bytes
from brownie.network.account import Account

CONFIG_DEPENDENCIES = 'dependencies'

CHAIN_ID_MUMBAI = 80001
CHAIN_ID_GOERLI = 5
CHAIN_ID_GANACHE = 1337
CHAIN_ID_MAINNET = 1

CHAIN_IDS_REQUIRING_CONFIRMATIONS = [CHAIN_ID_MUMBAI, CHAIN_ID_GOERLI, CHAIN_ID_MAINNET]
REQUIRED_TX_CONFIRMATIONS_DEFAULT = 2

def s2h(text: str) -> str:
    return Web3.toHex(text.encode('ascii'))

def h2s(hex: str) -> str:
    return Web3.toText(hex).split('\x00')[-1]

def h2sLeft(hex: str) -> str:
    return Web3.toText(hex).split('\x00')[0]

def s2b32(text: str):
    return '{:0<66}'.format(Web3.toHex(text.encode('ascii')))[:66]

def b322s(b32: bytes):
    return b32.decode().split('\x00')[0]

def s2b(text:str):
    return s2b32(text)

def b2s(hex_string, encoding='utf-8'):
    if not isinstance(hex_string, str):
        hex_string = str(hex_string)

    if not hex_string.startswith('0x'):
        raise ValueError("hex string does not start with '0x'")
    
    hex_data = hex_string[2:]
    byte_data = bytes.fromhex(hex_data)
    decoded_string = byte_data.decode(encoding)
    return decoded_string.split('\x00')[0]


def keccak256(text:str):
    return Web3.solidityKeccak(['string'], [text]).hex()

def get_account(mnemonic: str, account_offset: int) -> Account:
    return accounts.from_mnemonic(
        mnemonic,
        count=1,
        offset=account_offset)

def get_package(substring: str):
    for dependency in config[CONFIG_DEPENDENCIES]:
        if substring in dependency:
            print("using package '{}' for '{}'".format(
                dependency,
                substring))
            
            return project.load(dependency, raise_if_loaded=False)
    
    print("no package for substring '{}' found".format(substring))
    return None


def save_json(contract_class, file_name=None):
    vi = contract_class.get_verification_info()
    sji = vi['standard_json_input']

    if not file_name or len(file_name) == 0:
        file_name = './{}.json'.format(contract_class._name)

    print('writing standard json input file {}'.format(file_name))
    with open(file_name, "w") as json_file:
        json.dump(sji, json_file)




def new_accounts(count=20):
    buffer = io.StringIO()

    with redirect_stdout(buffer):
        account = accounts.add()

    output = buffer.getvalue()
    mnemonic = output.split('\x1b')[1][8:]

    return accounts.from_mnemonic(mnemonic, count=count), mnemonic


# source: https://github.com/brownie-mix/upgrades-mix/blob/main/scripts/helpful_scripts.py 
def encode_function_data(*args, initializer=None):
    """Encodes the function call so we can work with an initializer.
    Args:
        initializer ([brownie.network.contract.ContractTx], optional):
        The initializer function we want to call. Example: `box.store`.
        Defaults to None.
        args (Any, optional):
        The arguments to pass to the initializer function
    Returns:
        [bytes]: Return the encoded bytes.
    """
    if not len(args): args = b''

    if initializer: return initializer.encode_input(*args)

    return b''


def wait_for_confirmations(
    tx,
    confirmations=REQUIRED_TX_CONFIRMATIONS_DEFAULT
):
    if web3.chain_id in CHAIN_IDS_REQUIRING_CONFIRMATIONS:
        if not is_forked_network():
            print('waiting for confirmations ...')
            tx.wait(confirmations)
        else:
            print('not waiting for confirmations in a forked network...')

    elif web3.chain_id == CHAIN_ID_GANACHE:
        chain.mine(1)


def is_forked_network():
    return 'fork' in network.show_active()


def get_iso_datetime(timestamp):
    return datetime.fromtimestamp(timestamp).isoformat()