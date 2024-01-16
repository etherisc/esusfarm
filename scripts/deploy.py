import time

from brownie.network import accounts
from brownie.network.account import Account

from brownie import (
    interface,
    network,
    web3,
    ArcModel,
    ArcProduct,
    ArcPool,
    EXOF
)

from scripts.const import (
    INSTANCE_OPERATOR,
    INSTANCE_WALLET,
    PRODUCT_OWNER,
    RISKPOOL_KEEPER,
    RISKPOOL_WALLET,
    INVESTOR,
    CUSTOMER,
    OUTSIDER,
    BUNDLE_STATE,
    APPLICATION_STATE,
    POLICY_STATE,
    COMPONENT_STATE,
    ZERO_ADDRESS
)

from os.path import exists

from scripts.instance import GifInstance

from scripts.setup import (
    NAME_BASE, 
    GifSetupV2Complete
)

from scripts.util import (
    contract_from_address,
    new_accounts,
    get_package,
    is_forked_network,
    get_iso_datetime,
    b2s,
    s2b,
    deploy,
    from_block,
)

ERC20_TOKEN = 'erc20Token'
INSTANCE = 'instance'
INSTANCE_SERVICE = 'instanceService'
INSTANCE_OPERATOR_SERVICE = 'instanceOperatorService'
COMPONENT_OWNER_SERVICE = 'componentOwnerService'
PRODUCT = 'product'
RISKPOOL = 'riskpool'

PROCESS_ID1 = 'processId1'
PROCESS_ID2 = 'processId2'

INITIAL_ERC20_BUNDLE_FUNDING = 100000
BENEFICIARY_SALT = '624b6dbf-e083-427b-b3d2-fcc4a4a74adc'

# GAS_PRICE = web3.eth.gas_price
GAS_PRICE = 25 * 10**9 # 25 gwei, mainnet: https://owlracle.info/eth, goerli: https://owlracle.info/goerli
GAS_PRICE_SAFETY_FACTOR = 1.25

GAS_0 = 0
GAS_S = 1 * 10**6
GAS_M = 6 * 10**6
GAS_L = 10 * 10**6
GAS_XL = 60 * 10**6

GAS_PRODUCT = {
    INSTANCE_OPERATOR: GAS_XL,
    INSTANCE_WALLET:   GAS_S,
    PRODUCT_OWNER:     GAS_L,
    RISKPOOL_KEEPER:   GAS_L,
    RISKPOOL_WALLET:   GAS_S,
    INVESTOR:          GAS_M,
    CUSTOMER:         GAS_M,
}

def help():
    print('from scripts.util import deploy, deploy_with_args, from_block, transfer, contract_from_address, get_package, b2s, s2b')
    print('from scripts.deploy import all_in_1, get_setup, stakeholder_accounts_ganache, check_funds, amend_funds, create_bundle, get_bundle, help')
    print('')
    if web3.chain_id in [31337]:
        print('# create new setup (anvil)')
        print('a = stakeholder_accounts_ganache() # opt param new=True to create fresh unfunded accounts')
        print('set_gas_price = True')
        print('(product, pool, pool_wallet, token, customer, customer2, investor, instance_service, instance_operator, bundle_id, d) = all_in_1(a, set_gas_price=set_gas_price, deploy_all=True)')
        print('model = contract_from_address(ArcModel, product.getModel())')
        print('')
    else:
        print('# create new setup (mumbai/polygon)')
        print('a = ...')
        print('')
        print('set_gas_price = False')
        print('publish_source = True')
        print('# token = deploy(EXOF, instanceOperator, set_gas_price=set_gas_price, publish_source=publish_source)')
        print('check_funds(a, token)')
        print('amend_funds(a)')
        print('')
        print('(product, pool, pool_wallet, token, customer, customer2, investor, instance_service, instance_operator, bundle_id, d) = all_in_1(a, set_gas_price=set_gas_price, publish_source=publish_source, deploy_all=True)')

    # print("token = deploy(UsdcMock, a['instanceOperator'], set_gas_price=True)")
    # print('check_funds(a, token)')
    # print('# TODO')
    # print('')
    # print('# check setup')
    # print('product_address = product.address')
    # print('(setup, product, pool, token, instance_service) = get_setup(product_address)')
    # print('')
    # print('import json')
    # print("json.dump(setup, open('setup_ganache.json', 'w'), indent=4)")
    # print('')

    if web3.chain_id in [31337]:
        print('# create policy')
        print('model = contract_from_address(ArcModel, product.getModel())')
        print("salt = 'whatever you like best'")
        print("config_id = model.getConfigId(0)")
        print("location_id = model.toLocationId('Centre Nord', 'Sanmatenga', 'Kaya', 'Basberike', salt)")
        print("tx = product.createRisk(config_id, location_id, 'Sorghum', 71972600, 55671600, False, from_block(product.owner(), True))")
        print("risk_id = tx.events['LogArcRiskCreated']['riskId']")
        print("beneficiary_id = model.toBeneficiaryId('QF123456', '22623456789', salt)")
        print("beneficiary_wallet = accounts.add()")
        print("tx = product.createPolicy(beneficiary_id, beneficiary_wallet, model.SEX_FEMALE(), risk_id, 12600*10**token.decimals(), 100000*10**token.decimals(), 20230701, True, from_block(product.owner(), True))")
        print("policy_id = tx.events['LogArcPolicyCreated']['policyId']")
        print('')
        print('# check policy')
        print("model.getBeneficiary(beneficiary_id).dict()")
        print("instance_service.getApplication(policy_id).dict()")
        print("product.decodeApplicationData(instance_service.getApplication(policy_id).dict()['data']).dict()")
        print('instance_service.getPolicy(policy_id).dict()')
        print('')
        print('# process policy')
        print('tx = product.processPolicy(policy_id, from_block(product.owner(), True))')
        print("claim_id = tx.events['LogClaimCreated']['claimId']")
        print('instance_service.getClaim(policy_id, claim_id).dict()')


def get_deploy_timestamp(name):
    name_timestamp_from = len(NAME_BASE)
    name_timestamp_to = name_timestamp_from + 12

    timestamp = name[name_timestamp_from:name_timestamp_to]
    if timestamp[0] == '_':
        return int(timestamp[1:-1])
    
    return int(timestamp[:-2])


def get_bundle(bundle_id, product_address):
    product = contract_from_address(ProductV2, product_address)

    token = contract_from_address(interface.IERC20Metadata, product.getToken())
    tf = 10**token.decimals()

    (instance_service, instance_operator, treasury, instance_registry) = get_instance(product)
    riskpool = get_riskpool(product, instance_service)
    riskpool_contract = (riskpool._name, riskpool.getId(), str(riskpool))

    chain_registry = contract_from_address(interface.IChainRegistryFacadeExt, riskpool.getChainRegistry())
    staking = contract_from_address(interface.IStakingFacade, riskpool.getStaking())

    bundle = instance_service.getBundle(bundle_id).dict()
    bundle_params = riskpool.decodeBundleParamsFromFilter(bundle['filter']).dict()
    capacity = bundle['capital'] - bundle['lockedCapital']
    protection_factor = 100/riskpool.getSumInsuredPercentage()
    available = protection_factor * capacity

    bundle_setup = {}
    bundle_setup['bundle'] = {}
    bundle_setup['bundle']['id'] = bundle['id']
    bundle_setup['bundle']['name'] = bundle_params['name']
    bundle_setup['bundle']['lifetime'] = (bundle_params['lifetime']/(24 * 3600), bundle_params['lifetime'])
    bundle_setup['bundle']['riskpool_id'] = bundle['riskpoolId']
    bundle_setup['bundle']['riskpool'] = riskpool_contract
    bundle_setup['bundle']['state'] = _get_bundle_state(bundle['state'])

    bundle_setup['filter'] = {}
    bundle_setup['filter']['apr'] = (bundle_params['annualPercentageReturn']/riskpool.APR_100_PERCENTAGE(), bundle_params['annualPercentageReturn'])
    bundle_setup['filter']['duration_min'] = (bundle_params['minDuration']/(24 * 3600), bundle_params['minDuration'])
    bundle_setup['filter']['duration_max'] = (bundle_params['maxDuration']/(24 * 3600), bundle_params['maxDuration'])
    bundle_setup['filter']['protection_min'] = (protection_factor * bundle_params['minSumInsured']/tf, protection_factor * bundle_params['minSumInsured'])
    bundle_setup['filter']['protection_max'] = (protection_factor * bundle_params['maxSumInsured']/tf, protection_factor * bundle_params['maxSumInsured'])

    bundle_setup['financials'] = {}
    bundle_setup['financials']['available'] = (available/tf, available)
    bundle_setup['financials']['balance'] = (bundle['balance']/tf, bundle['balance'])
    bundle_setup['financials']['capacity'] = (capacity/tf, capacity)
    bundle_setup['financials']['capital'] = (bundle['capital']/tf, bundle['capital'])
    bundle_setup['financials']['capital_locked'] = (bundle['lockedCapital']/tf, bundle['lockedCapital'])

    bundle_nft_id = chain_registry.getBundleNftId(instance_service.getInstanceId(), bundle['id'])
    bundle_nft_info = None

    try:
        bundle_nft_info = chain_registry.getNftInfo(bundle_nft_id).dict()
    except Exception as e:
        bundle_nft_info = {'message': 'n/a'}

    bundle_cs = staking.capitalSupport(bundle_nft_id)
    bundle_setup['staking'] = {}
    bundle_setup['staking']['nft_id'] = bundle_nft_id
    bundle_setup['staking']['nft_info'] = bundle_nft_info
    bundle_setup['staking']['capital_support'] = (bundle_cs/tf, bundle_cs)

    bundle_setup['timestamps'] = {}
    bundle_setup['timestamps']['created_at'] = (get_iso_datetime(bundle['createdAt']), bundle['createdAt'])
    bundle_setup['timestamps']['updated_at'] = (get_iso_datetime(bundle['updatedAt']), bundle['updatedAt'])

    open_until = bundle['createdAt'] + bundle_params['lifetime']
    bundle_setup['timestamps']['open_until'] = (get_iso_datetime(open_until), open_until)

    return bundle_setup


def get_setup(product_address):

    product = contract_from_address(ProductV2, product_address)
    product_id = product.getId()
    product_name = b2s(str(product.getName()))
    product_contract = (product._name, str(product))
    product_owner = product.owner()

    token = contract_from_address(interface.IERC20Metadata, product.getToken())

    (instance_service, instance_operator, treasury, instance_registry) = get_instance(product)
    riskpool = get_riskpool(product, instance_service)
    riskpool_id = riskpool.getId()
    riskpool_name = b2s(str(riskpool.getName()))
    riskpool_contract = (riskpool._name, str(riskpool))
    riskpool_sum_insured_cap = riskpool.getSumOfSumInsuredCap()
    riskpool_owner = riskpool.owner()
    riskpool_token = contract_from_address(interface.IERC20Metadata, riskpool.getErc20Token())

    setup = {}
    setup['instance'] = {}
    setup['product'] = {}
    setup['riskpool'] = {}
    
    # instance specifics
    setup['instance']['id'] = str(instance_service.getInstanceId())
    setup['instance']['chain'] = (instance_service.getChainName(), instance_service.getChainId())
    setup['instance']['instance_registry'] = instance_service.getRegistry()
    setup['instance']['instance_operator'] = instance_operator
    setup['instance']['release'] = b2s(str(instance_registry.getRelease()))
    setup['instance']['wallet'] = instance_service.getInstanceWallet()
    setup['instance']['products'] = instance_service.products()
    setup['instance']['oracles'] = instance_service.oracles()
    setup['instance']['riskpools'] = instance_service.riskpools()
    setup['instance']['bundles'] = instance_service.bundles()

    wallet_balance = token.balanceOf(instance_service.getInstanceWallet())
    setup['instance']['wallet_balance'] = (wallet_balance / 10 ** token.decimals(), wallet_balance)

    # product specifics
    setup['product']['contract'] = product_contract
    setup['product']['id'] = product_id
    setup['product']['owner'] = product_owner
    setup['product']['state'] = _getComponentState(product.getId(), instance_service)
    setup['product']['riskpool_id'] = product.getRiskpoolId()
    setup['product']['deployed_at'] = (get_iso_datetime(get_deploy_timestamp(product_name)), get_deploy_timestamp(product_name))
    setup['product']['premium_fee'] = _get_fee_spec(product_id, treasury, instance_service)
    setup['product']['token'] = (token.symbol(), str(token), token.decimals())
    setup['product']['process_ids'] = product.applications()

    # riskpool specifics
    setup['riskpool']['contract'] = riskpool_contract
    setup['riskpool']['id'] = riskpool_id
    setup['riskpool']['owner'] = riskpool_owner
    setup['riskpool']['state'] = _getComponentState(riskpool.getId(), instance_service)
    setup['riskpool']['deployed_at'] = (get_iso_datetime(get_deploy_timestamp(riskpool_name)), get_deploy_timestamp(riskpool_name))
    setup['riskpool']['capital_fee'] = _get_fee_spec(riskpool_id, treasury, instance_service)
    setup['riskpool']['token'] = (riskpool_token.symbol(), str(riskpool_token), riskpool_token.decimals())

    setup['riskpool']['sum_insured_cap'] = (riskpool_sum_insured_cap / 10**riskpool_token.decimals(), riskpool_sum_insured_cap)

    setup['riskpool']['bundles'] = riskpool.bundles()
    setup['riskpool']['bundles_active'] = riskpool.activeBundles()
    setup['riskpool']['bundles_max'] = riskpool.getMaximumNumberOfActiveBundles()

    setup['riskpool']['balance'] = (riskpool.getBalance() / 10**riskpool_token.decimals(), riskpool.getBalance())
    setup['riskpool']['capital'] = (riskpool.getCapital() / 10**riskpool_token.decimals(), riskpool.getCapital())
    setup['riskpool']['capacity'] = (riskpool.getCapacity() / 10**riskpool_token.decimals(), riskpool.getCapacity())
    setup['riskpool']['total_value_locked'] = (riskpool.getTotalValueLocked() / 10**riskpool_token.decimals(), riskpool.getTotalValueLocked())

    riskpool_wallet = instance_service.getRiskpoolWallet(riskpool_id)
    setup['riskpool']['wallet'] = riskpool_wallet
    setup['riskpool']['wallet_allowance'] = (riskpool_token.allowance(riskpool_wallet, instance_service.getTreasuryAddress()) / 10**riskpool_token.decimals(), riskpool_token.balanceOf(riskpool_wallet))
    setup['riskpool']['wallet_balance'] = (riskpool_token.balanceOf(riskpool_wallet) / 10**riskpool_token.decimals(), riskpool_token.balanceOf(riskpool_wallet))

    return (
        setup,
        product,
        riskpool,
        token,
        instance_service
    )


def _getStakeBalance(staking, dip):
    stake_balance = 0

    try: 
        stake_balance = staking.stakeBalance()
    except Exception as e:
        return ('n/a', 0)

    return (stake_balance/10**dip.decimals(), stake_balance)


def _get_application_state(state):
    return (APPLICATION_STATE[state], state)


def _get_policy_state(state):
    return (POLICY_STATE[state], state)


def _get_bundle_state(state):
    return (BUNDLE_STATE[state], state)

def _getComponentState(component_id, instance_service):
    state = instance_service.getComponentState(component_id)
    return (COMPONENT_STATE[state], state)


def _get_version(versionable):
    (major, minor, patch) = versionable.versionParts()
    return('v{}.{}.{}'.format(major, minor, patch), versionable.version())


def _get_fee_spec(component_id, treasury, instance_service):
    spec = treasury.getFeeSpecification(component_id).dict()

    if spec['componentId'] == 0:
        return 'WARNING no fee spec available, not ready to use'

    return (
        spec['fractionalFee']/instance_service.getFeeFractionFullUnit(), spec['fixedFee'])


def get_riskpool(product, instance_service):
    riskpool_id = product.getRiskpoolId()
    riskpool_address = instance_service.getComponent(riskpool_id)
    return contract_from_address(PoolV2, riskpool_address)


def get_instance(product):
    gif = get_package('gif-contracts')

    registry_address = product.getRegistry()
    registry = contract_from_address(gif.RegistryController, registry_address)

    instance_service_address = registry.getContract(s2b('InstanceService'))
    instance_service = contract_from_address(gif.InstanceService, instance_service_address)
    instance_operator = instance_service.getInstanceOperator()

    treasury_address = registry.getContract(s2b('Treasury'))
    treasury = contract_from_address(gif.TreasuryModule, treasury_address)

    return (instance_service, instance_operator, treasury, registry)


def stakeholder_accounts_ganache(accs=None, new=False):

    a = accounts

    if accs and len(accs) >= 7:
        print(f"... using provided {len(accs)} accounts")
        a = accs
    elif new:
        (a, mnemonic) = new_accounts()
        print(f"... using {len(a)} new empty accounts from: {mnemonic}")
    else:
        print(f"... using {len(a)} default accounts from local chain")

    # define stakeholder accounts  
    instanceOperator=a[0]
    instanceWallet=a[1]
    productOwner=a[2]
    riskpoolKeeper=a[3]
    riskpoolWallet=a[4]
    investor=a[5]
    customer=a[6]
    outsider=a[7]

    return {
        INSTANCE_OPERATOR: instanceOperator,
        INSTANCE_WALLET: instanceWallet,
        PRODUCT_OWNER: productOwner,
        RISKPOOL_KEEPER: riskpoolKeeper,
        RISKPOOL_WALLET: riskpoolWallet,
        INVESTOR: investor,
        CUSTOMER: customer,
        OUTSIDER: outsider,
    }


def check_funds(
    stakeholders_accounts,
    erc20_token,
    gas_price=None,
    safety_factor=GAS_PRICE_SAFETY_FACTOR,
    print_requirements=False
):
    a = stakeholders_accounts

    if not gas_price:
        gas_price = get_gas_price()

    gp = int(safety_factor * gas_price)

    _print_constants(gas_price, safety_factor, gp)

    if print_requirements:
        print('--- funding requirements ---')
        print('Name;Address;ETH')

        for accountName, requiredAmount in GAS_PRODUCT.items():
            print('{};{};{:.4f}'.format(
                accountName,
                a[accountName],
                gp * requiredAmount / 10**18
            ))

        print('--- end of funding requirements ---')


    checkedAccounts = 0
    fundsAvailable = 0
    fundsMissing = 0
    native_token_success = True

    for accountName, requiredAmount in GAS_PRODUCT.items():
        balance = a[accountName].balance()
        fundsAvailable += balance
        checkedAccounts += 1

        if balance >= gp * GAS_PRODUCT[accountName]:
            print('{} funding OK, has [ETH]{:.5f} ([wei]{})'.format(
                accountName,
                balance/10**18,
                balance))
        else:
            fundsMissing += gp * GAS_PRODUCT[accountName] - balance
            print('{} needs [ETH]{:.5f}, has [ETH]{:.5f} ([wei]{})'.format(
                accountName,
                (gp * GAS_PRODUCT[accountName])/10**18,
                balance/10**18,
                balance
            ))
    
    if fundsMissing > 0:
        native_token_success = False

        if a[INSTANCE_OPERATOR].balance() >= gp * GAS_PRODUCT[INSTANCE_OPERATOR] + fundsMissing:
            print('{} sufficiently funded with native token to cover missing funds'.format(INSTANCE_OPERATOR))
        else:
            additionalFunds = gp * GAS_PRODUCT[INSTANCE_OPERATOR] + fundsMissing - a[INSTANCE_OPERATOR].balance()
            print('{} needs additional funding of {} ({} ETH) with native token to cover missing funds'.format(
                INSTANCE_OPERATOR,
                additionalFunds,
                additionalFunds/10**18
            ))
    else:
        native_token_success = True

    erc20_success = False
    if erc20_token:
        erc20_success = check_erc20_funds(a, erc20_token, a[INSTANCE_OPERATOR])
    else:
        print('WARNING: no erc20 token defined, skipping erc20 funds checking')

    print('total funds available ({} accounts) [ETH] {:.6f}, [wei] {}'
        .format(checkedAccounts, fundsAvailable/10**18, fundsAvailable))

    return native_token_success & erc20_success


def amend_funds(
    stakeholders_accounts,
    gas_price=None,
    safety_factor=GAS_PRICE_SAFETY_FACTOR,
):
    if web3.chain_id == 1:
        print('amend_funds not available on mainnet')
        return

    a = stakeholders_accounts

    if not gas_price:
        gas_price = get_gas_price()

    gp = int(safety_factor * gas_price)

    _print_constants(gas_price, safety_factor, gp)

    for accountName, requiredAmount in GAS_PRODUCT.items():
        fundsMissing = gp * GAS_PRODUCT[accountName] - a[accountName].balance()

        if fundsMissing > 0:
            print('funding {} with {}'.format(accountName, fundsMissing))
            a[INSTANCE_OPERATOR].transfer(a[accountName], fundsMissing)

    print('re-run check_funds() to verify funding before deploy')


def check_erc20_funds(a, erc20_token, token_owner):
    if erc20_token.balanceOf(token_owner) >= INITIAL_ERC20_BUNDLE_FUNDING:
        print('{} ERC20 funding ok'.format(token_owner))
        return True
    else:
        print('{} needs additional ERC20 funding of {} to cover missing funds'.format(
            token_owner,
            INITIAL_ERC20_BUNDLE_FUNDING - erc20_token.balanceOf(token_owner)))
        print('IMPORTANT: manual transfer needed to ensure ERC20 funding')
        return False


def get_gas_price():
    return web3.eth.gas_price


def _print_constants(gas_price, safety_factor, gp):
    print('chain id: {}'.format(web3.eth.chain_id))
    print('gas price [GWei]: {}'.format(gas_price/10**9))
    print('safe gas price [GWei]: {}'.format(gp/10**9))
    print('gas price safety factor: {}'.format(safety_factor))

    print('gas S: {}'.format(GAS_S))
    print('gas M: {}'.format(GAS_M))
    print('gas L: {}'.format(GAS_L))
    print('gas XL: {}'.format(GAS_XL))

    print('required S [ETH]: {}'.format(gp * GAS_S / 10**18))
    print('required M [ETH]: {}'.format(gp * GAS_M / 10**18))
    print('required L [ETH]: {}'.format(gp * GAS_L / 10**18))
    print('required XL [ETH]: {}'.format(gp * GAS_XL / 10**18))


def _get_balances(stakeholders_accounts):
    balance = {}

    for account_name, account in stakeholders_accounts.items():
        balance[account_name] = account.balance()

    return balance


def _get_balances_delta(balances_before, balances_after):
    balance_delta = { 'total': 0 }

    for accountName, account in balances_before.items():
        balance_delta[accountName] = balances_before[accountName] - balances_after[accountName]
        balance_delta['total'] += balance_delta[accountName]
    
    return balance_delta


def _pretty_print_delta(title, balances_delta):

    print('--- {} ---'.format(title))
    
    gasPrice = network.gas_price()
    print('gas price: {}'.format(gasPrice))

    for accountName, amount in balances_delta.items():
        if accountName != 'total':
            if gasPrice != 'auto':
                print('account {}: gas {}'.format(accountName, amount / gasPrice))
            else:
                print('account {}: amount {}'.format(accountName, amount))
    
    print('-----------------------------')
    if gasPrice != 'auto':
        print('account total: gas {}'.format(balances_delta['total'] / gasPrice))
    else:
        print('account total: amount {}'.format(balances_delta['total']))
    print('=============================')


def _add_tokens_to_deployment(
    deployment,
    token,
):
    deployment[ERC20_TOKEN] = token

    return deployment


def _copy_hashmap(map_in):
    map_out = {}

    for key, value in elements(map_in):
        map_out[key] = value
    
    return map_out


def _add_instance_to_deployment(
    deployment,
    instance
):
    deployment[INSTANCE] = instance
    deployment[INSTANCE_SERVICE] = instance.getInstanceService()
    deployment[INSTANCE_WALLET] = deployment[INSTANCE_SERVICE].getInstanceWallet()

    deployment[INSTANCE_OPERATOR_SERVICE] = instance.getInstanceOperatorService()
    deployment[COMPONENT_OWNER_SERVICE] = instance.getComponentOwnerService()

    return deployment


def _add_product_to_deployment(
    deployment,
    product,
    riskpool
):
    deployment[PRODUCT] = product
    deployment[RISKPOOL] = riskpool

    return deployment


def all_in_1(
    stakeholders_accounts=None,
    registry_address=None,
    riskpool_address=None,
    token_address=None,
    deploy_all=False,
    create_riskpool_setup=True,
    set_gas_price=False,
    publish_source=False
):
    a = stakeholders_accounts or stakeholders_accounts_ganache()

    # don't try to publish source on forked networks
    if publish_source and is_forked_network():
        publish_source = False

    # assess balances at beginning of deploy
    balances_before = _get_balances(a)

    # deploy full setup including tokens, and gif instance
    if deploy_all:
        token = deploy(EXOF, a[INSTANCE_OPERATOR], publish_source=publish_source, set_gas_price=True)
        instance = GifInstance(
            instanceOperator=a[INSTANCE_OPERATOR], 
            instanceWallet=a[INSTANCE_WALLET],
            set_gas_price=set_gas_price,
            publish_source=publish_source)

    # where available reuse tokens and gif instgance from existing deployments
    else:
        if token_address or get_address('kes'):
            token = contract_from_address(
                interface.IERC20Metadata, 
                token_address or get_address('kes'))
        else:
            token = deploy(EXOF, a[INSTANCE_OPERATOR], publish_source=publish_source, set_gas_price=True)

        reg_addr = registry_address or get_address('registry')
        instance = None

        if reg_addr:
            instance = GifInstance(
                registry_address=reg_addr)
        else:
            instance = GifInstance(
                instanceOperator=a[INSTANCE_OPERATOR], 
                instanceWallet=a[INSTANCE_WALLET],
                publish_source=publish_source)

    # mumbai registry = '0x6ee518A5D45aa1A4BDE6AA3F33c1f5A2A1F2A255'
    print('====== token setup ======')
    print('- premium {} {}'.format(token.symbol(), token))

    # populate deployment hashmap
    deployment = _copy_map(a)
    deployment = _add_tokens_to_deployment(deployment, token)
    deployment = _add_instance_to_deployment(deployment, instance)

    balances_after_instance_setup = _get_balances(a)

    # deploy and setup for product + riskpool
    instance_service = instance.getInstanceService()

    productOwner = a[PRODUCT_OWNER]
    investor = a[INVESTOR]
    riskpoolKeeper = a[RISKPOOL_KEEPER]
    riskpoolWallet = a[RISKPOOL_WALLET]

    base_name = f"{NAME_BASE}_{int(time.time())}"

    print('====== deploy pool (base name: {}) ======'.format(base_name))
    setupV2Deploy = GifSetupV2Complete(
        instance.getRegistry(),
        investor,
        token,
        productOwner,
        riskpoolKeeper,
        riskpoolWallet,
        base_name=base_name,
        set_gas_price=set_gas_price,
        publish_source=publish_source)

    # assess balances at beginning of deploy
    balances_after_deploy = _get_balances(a)
    product = setupV2Deploy.getProductV2().getContract()
    pool = setupV2Deploy.getPoolV2().getContract()
    deployment = _add_product_to_deployment(deployment, product, pool)

    print('--- create pool setup ---')
    mult = 10**token.decimals()

    # fund riskpool
    bundle_funding = 2 * 10**6
    chain_id = instance_service.getChainId()
    instance_id = instance_service.getInstanceId()
    pool_id = pool.getId()
    bundle_id = create_bundle(
        instance_service, 
        a[INSTANCE_OPERATOR],
        pool,
        riskpoolKeeper,
        bundle_funding,
        set_gas_price=set_gas_price)

    # approval necessary for payouts or pulling out funds by investor
    token.approve(
        instance_service.getTreasuryAddress(),
        2 * bundle_funding * mult,
        from_block(deployment[RISKPOOL_WALLET], set_gas_price))

    return (
        deployment[PRODUCT],
        deployment[RISKPOOL],
        deployment[RISKPOOL_WALLET],
        deployment[ERC20_TOKEN],
        deployment[PRODUCT_OWNER],
        deployment[CUSTOMER],
        deployment[INVESTOR],
        deployment[INSTANCE_SERVICE],
        deployment[INSTANCE_OPERATOR],
        bundle_id,
        deployment)


def create_bundle(
    instanceService, 
    instanceOperator: Account,
    pool: ArcPool,
    investor: Account,
    funding: int,
    set_gas_price=False
) -> int:
    tokenAddress = pool.getErc20Token()
    token = contract_from_address(interface.IERC20Metadata, tokenAddress)
    tf = 10 ** token.decimals()

    token.transfer(investor, funding * tf, from_block(instanceOperator, set_gas_price))
    token.approve(instanceService.getTreasuryAddress(), funding * tf, from_block(investor, set_gas_price))

    tx = pool.createBundle(
        b'',
        funding * tf, 
        from_block(investor, set_gas_price))

    return tx.events['LogRiskpoolBundleCreated']['bundleId']


def get_address(name):
    if not exists('gif_instance_address.txt'):
        return None
    with open('gif_instance_address.txt') as file:
        for line in file:
            if line.startswith(name):
                t = line.split('=')[1].strip()
                print('found {} in gif_instance_address.txt: {}'.format(name, t))
                return t
    return None


def inspect_fee(
    d,
    netPremium,
):
    instanceService = d[INSTANCE_SERVICE]
    product = d[PRODUCT]

    feeSpec = product.getFeeSpecification()
    fixed = feeSpec[1]
    fraction = feeSpec[2]
    fullUnit = product.getFeeFractionFullUnit()

    (feeAmount, totalAmount) = product.calculateFee(netPremium)

    return {
        'fixedFee': fixed,
        'fractionalFee': int(netPremium * fraction / fullUnit),
        'feeFraction': fraction/fullUnit,
        'netPremium': netPremium,
        'fees': feeAmount,
        'totalPremium': totalAmount
    }


def inspect_applications_d(d):
    instanceService = d[INSTANCE_SERVICE]
    product = d[PRODUCT]
    riskpool = d[RISKPOOL]
    usd1 = d[ERC20_PROTECTED_TOKEN]
    usd2 = d[ERC20_TOKEN]

    inspect_applications(instanceService, product, riskpool, usd1, usd2)


def inspect_applications(instanceService, product, riskpool, usd1, usd2):
    mul_usd1 = 10**usd1.decimals()
    mul_usd2 = 10**usd2.decimals()

    processIds = product.applications()

    # print header row
    print('i customer product id type state wallet premium suminsured duration bundle maxpremium')

    # print individual rows
    for idx in range(processIds):
        processId = product.getApplicationId(idx) 
        metadata = instanceService.getMetadata(processId)
        customer = metadata[0]
        productId = metadata[1]

        application = instanceService.getApplication(processId)
        state = application[0]
        premium = application[1]
        suminsured = application[2]
        appdata = application[3]

        (
            wallet,
            protected_balance,
            duration,
            bundle_id,
            maxpremium
        ) = riskpool.decodeApplicationParameterFromData(appdata)

        if state == 2:
            policy = instanceService.getPolicy(processId)
            state = policy[0]
            kind = 'policy'
        else:
            policy = None
            kind = 'application'

        print('{} {} {} {} {} {} {} {:.1f} {:.1f} {} {} {:.1f}'.format(
            idx,
            _shortenAddress(customer),
            productId,
            processId,
            kind,
            state,
            _shortenAddress(wallet),
            premium/mul_usd2,
            suminsured/mul_usd1,
            duration/(24*3600),
            str(bundle_id) if bundle_id > 0 else 'n/a',
            maxpremium/mul_usd2,
        ))


def _shortenAddress(address) -> str:
    return '{}..{}'.format(
        address[:5],
        address[-4:])


def get_bundle_data(
    instanceService,
    riskpool
):
    bundle_nft = contract_from_address(interface.IERC721, instanceService.getBundleToken())
    riskpoolId = riskpool.getId()
    activeBundleIds = riskpool.getActiveBundleIds()
    bundleData = []

    for idx in range(len(activeBundleIds)):
        bundleId = activeBundleIds[idx]
        bundle = instanceService.getBundle(bundleId)
        applicationFilter = bundle[4]
        (
            name,
            lifetime,
            minSumInsured,
            maxSumInsured,
            minDuration,
            maxDuration,
            annualPercentageReturn

        ) = riskpool.decodeBundleParamsFromFilter(applicationFilter)

        apr = 100 * annualPercentageReturn/riskpool.getApr100PercentLevel()
        capital = bundle[5]
        locked = bundle[6]
        capacity = bundle[5]-bundle[6]
        policies = riskpool.getActivePolicies(bundleId)

        bundleData.append({
            'idx':idx,
            'owner':bundle_nft.ownerOf(bundle['tokenId']),
            'riskpoolId':riskpoolId,
            'bundleId':bundleId,
            'apr':apr,
            'name':name,
            'lifetime':lifetime/(24*3600),
            'minSumInsured':minSumInsured,
            'maxSumInsured':maxSumInsured,
            'minDuration':minDuration/(24*3600),
            'maxDuration':maxDuration/(24*3600),
            'capital':capital,
            'locked':locked,
            'capacity':capacity,
            'policies':policies
        })

    return bundleData


def from_component(
    componentAddress,
    productId=0,
    riskpoolId=0
):
    component = contract_from_address(interface.IComponent, componentAddress)
    return from_registry(component.getRegistry(), productId=productId, riskpoolId=riskpoolId)


def from_registry(
    registryAddress,
    productId=0,
    riskpoolId=0
):
    instance = GifInstance(registryAddress=registryAddress)
    instanceService = instance.getInstanceService()

    products = instanceService.products()
    riskpools = instanceService.riskpools()

    product = None
    riskpool = None

    if products >= 1:
        if productId > 0:
            componentId = productId
        else:
            componentId = instanceService.getProductId(products-1)

            if products > 1:
                print('1 product expected, {} products available'.format(products))
                print('returning last product available')
        
        componentAddress = instanceService.getComponent(componentId)
        product = contract_from_address(ProductV2, componentAddress)

        if product.getType() != 1:
            product = None
            print('component (type={}) with id {} is not product'.format(product.getType(), componentId))
            print('no product returned (None)')
    else:
        print('1 product expected, no product available')
        print('no product returned (None)')

    if riskpools >= 1:
        if riskpoolId > 0:
            componentId = riskpoolId
        else:
            componentId = instanceService.getRiskpoolId(riskpools-1)

            if riskpools > 1:
                print('1 riskpool expected, {} riskpools available'.format(riskpools))
                print('returning last riskpool available')
        
        componentAddress = instanceService.getComponent(componentId)
        riskpool = contract_from_address(PoolV2, componentAddress)

        if riskpool.getType() != 2:
            riskpool = None
            print('component (type={}) with id {} is not riskpool'.format(component.getType(), componentId))
            print('no riskpool returned (None)')
    else:
        print('1 riskpool expected, no riskpools available')
        print('no riskpool returned (None)')

    return (instance, product, riskpool)


def _copy_map(map_in):
    map_out = {}

    for key, value in map_in.items():
        map_out[key] = value

    return map_out
