from web3 import Web3

import time

from brownie.network.account import Account

from brownie import (
    chain,
    web3,
    interface,
    Wei,
    Contract, 
    ArcModel,
    ArcProduct,
    ArcPool
)

from scripts.util import (
    contract_from_address,
    s2b,
    wait_for_confirmations,
    from_block,
    deploy,
    deploy_with_args,
)

from scripts.instance import GifInstance

# base name for products, pools, distribution
NAME_BASE = 'Arc'

SUM_OF_SUM_INSURED_CAP = 10 * 10**12
MAX_ACTIVE_BUNDLES = 10

CAPITAL_FIXED_FEE = 0
CAPITAL_FRACTIONAL_FEE = 0

PREMIUM_FIXED_FEE = 0
PREMIUM_FRACTIONAL_FEE = 0

class GifPoolV2(object):

    def __init__(self, 
        registry_address: Account, 
        token: Account,
        riskpoolKeeper: Account, 
        riskpoolWallet: Account,
        investor: Account,
        collateralization:int,
        name,
        pool_address=None,
        set_gas_price=False,
        publish_source=False
    ):

        print('------ setting up riskpool ------')
        self.pool = None

        if pool_address:
            print('1) obtain riskpool from address {}'.format(pool_address))
            self.pool = contract_from_address(PoolV2, pool_address)

            return

        instance = GifInstance(registry_address=registry_address)
        instanceService = instance.getInstanceService()
        instanceOperatorService = instance.getInstanceOperatorService()
        componentOwnerService = instance.getComponentOwnerService()
        riskpoolKeeperRole = instanceService.getRiskpoolKeeperRole()

        if instanceService.hasRole(riskpoolKeeperRole, riskpoolKeeper):
            print('1) riskpool keeper {} already has role {}'.format(
                riskpoolKeeper, riskpoolKeeperRole))
        else:
            print('1) grant riskpool keeper role {} to riskpool keeper {}'.format(
                riskpoolKeeperRole, riskpoolKeeper))

            instanceOperatorService.grantRole(
                riskpoolKeeperRole, 
                riskpoolKeeper, 
                from_block(instance.getOwner(), set_gas_price))

        print('2) deploy riskpool {} by riskpool keeper {}'.format(
            name, riskpoolKeeper))

        self.pool = deploy_with_args(
            ArcPool,
            [
                s2b(name),
                collateralization,
                token,
                riskpoolWallet,
                instance.getRegistry()
            ],
            riskpoolKeeper,
            set_gas_price=set_gas_price,
            publish_source=publish_source)

        print('3) riskpool {} proposing to instance by riskpool keeper {}'.format(
            self.pool, riskpoolKeeper))
        
        tx = componentOwnerService.propose(
            self.pool,
            from_block(riskpoolKeeper, set_gas_price))

        wait_for_confirmations(tx)

        print('4) approval of riskpool id {} by instance operator {}'.format(
            self.pool.getId(), instance.getOwner()))
        
        tx = instanceOperatorService.approve(
            self.pool.getId(),
            from_block(instance.getOwner(), set_gas_price))

        wait_for_confirmations(tx)

        print('7) riskpool wallet {} set for riskpool id {} by instance operator {}'.format(
            riskpoolWallet, self.pool.getId(), instance.getOwner()))
        
        instanceOperatorService.setRiskpoolWallet(
            self.pool.getId(),
            riskpoolWallet,
            from_block(instance.getOwner(), set_gas_price))

        # 7) setup capital fees
        print('8) creating capital fee spec (fixed: {}, fractional: {}) for riskpool id {} by instance operator {}'.format(
            CAPITAL_FIXED_FEE, CAPITAL_FRACTIONAL_FEE, self.pool.getId(), instance.getOwner()))
        
        feeSpec = instanceOperatorService.createFeeSpecification(
            self.pool.getId(),
            CAPITAL_FIXED_FEE,
            CAPITAL_FRACTIONAL_FEE,
            b'')

        print('9) setting capital fee spec by instance operator {}'.format(
            instance.getOwner()))
        
        instanceOperatorService.setCapitalFees(
            feeSpec,
            from_block(instance.getOwner(), set_gas_price))

    def getId(self) -> int:
        return self.pool.getId()

    def getToken(self) -> Account:
        return self.pool.getErc20Token()
    
    def getContract(self) -> ArcPool:
        return self.pool


class GifProductV2(object):

    def __init__(self,
        registry_address: Account,
        productOwner: Account,
        pool: GifPoolV2,
        name,
        product_address=None,
        set_gas_price=False,
        publish_source=False
    ):

        if product_address and pool:
            print('1) obtain product v2 from address {}'.format(product_address))
            self.product = contract_from_address(ProductV2, product_address)
            self.pool = pool

            return

        self.pool = pool

        print('------ setting up product ------')
        instance = GifInstance(registry_address=registry_address)
        instanceService = instance.getInstanceService()
        instanceOperatorService = instance.getInstanceOperatorService()
        componentOwnerService = instance.getComponentOwnerService()
        productOwnerRole = instanceService.getProductOwnerRole()

        if instanceService.hasRole(productOwnerRole, productOwner):
            print('1) product owner {} already has role {}'.format(
                productOwner, productOwnerRole))
        else:
            print('1) grant product owner role {} to product owner {}'.format(
                productOwnerRole, productOwner))

            instanceOperatorService.grantRole(
                productOwnerRole,
                productOwner, 
                from_block(instance.getOwner(), set_gas_price))

        print('2) deploy product by product owner {}'.format(
            productOwner))

        model = deploy(
            ArcModel,
            productOwner,
            set_gas_price=set_gas_price,
            publish_source=publish_source)

        self.product = deploy_with_args(
            ArcProduct,
            [
                s2b(name),
                pool.getToken(),
                pool.getId(),
                instance.getRegistry(),
                model
            ],
            productOwner,
            set_gas_price=set_gas_price,
            publish_source=publish_source)

        model.transferOwnership(
            self.product,
            from_block(productOwner, set_gas_price))

        # hack
        if web3.chain_id == 1337:
            chain.mine(1)

        print('3) product {} (id={}) proposing to instance by product owner {}'.format(
            self.product, self.product.getId(), productOwner))
        
        tx = componentOwnerService.propose(
            self.product,
            from_block(productOwner, set_gas_price))

        wait_for_confirmations(tx)

        print('4) approval of product id {} by instance operator {}'.format(
            self.product.getId(), instance.getOwner()))

        tx = instanceOperatorService.approve(
            self.product.getId(),
            from_block(instance.getOwner(), set_gas_price))

        wait_for_confirmations(tx)

        print('5) setting erc20 product token {} for product id {} by instance operator {}'.format(
            self.product.getToken(), self.product.getId(), instance.getOwner()))

        instanceOperatorService.setProductToken(
            self.product.getId(), 
            self.product.getToken(),
            from_block(instance.getOwner(), set_gas_price))

        print('6) creating premium fee spec (fixed: {}, fractional: {}) for product id {} by instance operator {}'.format(
            PREMIUM_FIXED_FEE, PREMIUM_FRACTIONAL_FEE, self.product.getId(), instance.getOwner()))
        
        feeSpec = instanceOperatorService.createFeeSpecification(
            self.product.getId(),
            PREMIUM_FIXED_FEE,
            PREMIUM_FRACTIONAL_FEE,
            b'') 

        print('7) setting premium fee spec by instance operator {}'.format(
            instance.getOwner()))

        instanceOperatorService.setPremiumFees(
            feeSpec,
            from_block(instance.getOwner(), set_gas_price))

    def getId(self) -> int:
        return self.product.getId()

    def getToken(self):
        return self.product.getToken()

    def getContract(self) -> ArcProduct:
        return self.product

    def getPool(self) -> GifPoolV2:
        return self.pool


class GifSetupV2Complete(object):

    def __init__(self,
        registry_address: Account,
        investor: Account,
        token: Account,
        productOwner: Account,
        riskpoolKeeper: Account,
        riskpoolWallet: Account,
        base_name=f"{NAME_BASE}_{int(time.time())}",
        pool_address=None,
        product_address=None,
        set_gas_price=False,
        publish_source=False
    ):
        instance = GifInstance(registry_address=registry_address)
        instace_service = instance.getInstanceService()
        full_collateralization_level = instace_service.getFullCollateralizationLevel()

        print('====== obtain/deploy pool ======')
        self.pool = GifPoolV2(
            registry_address, 
            token, 
            riskpoolKeeper, 
            riskpoolWallet,
            investor, 
            full_collateralization_level,
            '{}_Pool'.format(base_name),
            pool_address=pool_address,
            set_gas_price=set_gas_price,
            publish_source=publish_source)

        print('====== obtain/deploy product ======')
        self.product = GifProductV2(
            registry_address, 
            productOwner, 
            self.pool, 
            '{}_Product'.format(base_name),
            product_address=product_address,
            set_gas_price=set_gas_price,
            publish_source=publish_source)

    def getToken(self):
        return self.product.getToken()

    def getProductV2(self) -> GifProductV2:
        return self.product

    def getPoolV2(self) -> GifPoolV2:
        return self.pool
