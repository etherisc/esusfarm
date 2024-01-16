import json
import os

from web3 import Web3

from brownie.convert import to_bytes
from brownie.network import accounts
from brownie.network.account import Account

from brownie import (
    Wei,
    Contract, 
    network,
    interface
)

from scripts.const import (
    GIF_RELEASE,
    ZERO_ADDRESS,
)

from scripts.util import (
    encode_function_data,
    get_account,
    get_package,
    s2h,
    s2b,
    b2s,
    contract_from_address,
    deploy,
    deploy_with_args,
    from_block,
)

INSTANCE_CONTRACTS = [
    'InstanceOperatorService',
    'Registry',
    'RegistryController',
    'BundleToken',
    'RiskpoolToken',
    'AccessController',
    'Access',
    'ComponentController',
    'Component',
    'QueryController',
    'Query',
    'LicenseController',
    'License',
    'PolicyController',
    'Policy',
    'BundleController',
    'Bundle',
    'PoolController',
    'Pool',
    'TreasuryController',
    'Treasury',
    'PolicyDefaultFlow',
    'PolicyDefaultFlowExt',
    'InstanceServiceController',
    'InstanceService',
    'ComponentOwnerServiceController',
    'ComponentOwnerService',
    'OracleServiceController',
    'OracleService',
    'RiskpoolServiceController',
    'RiskpoolService',
    'ProductService',
    'InstanceOperatorServiceControlle',
]

class GifRegistry(object):

    def __init__(
        self, 
        instanceOperator: Account, 
        registry_address: Account,
        set_gas_price=False,
        publish_source=False
    ):
        gif = get_package('gif-contracts')
        registryAddress = registry_address

        if instanceOperator is not None and registryAddress is None:
            # controller = gif.RegistryController.deploy(
            #     {'from': instanceOperator},
            #     publish_source=publish_source)
            controller = deploy(
                gif.RegistryController,
                instanceOperator,
                set_gas_price=set_gas_price,
                publish_source=publish_source)

            encoded_initializer = encode_function_data(
                s2b(GIF_RELEASE),
                initializer=controller.initializeRegistry)

            # proxy = gif.CoreProxy.deploy(
            #     controller.address,
            #     encoded_initializer, 
            #     {'from': instanceOperator},
            #     publish_source=publish_source)
            proxy = deploy_with_args(
                gif.CoreProxy,
                [controller.address, encoded_initializer],
                instanceOperator,
                set_gas_price=set_gas_price,
                publish_source=publish_source)

            registry = contract_from_address(gif.RegistryController, proxy.address)
            registry.register(s2b('Registry'), proxy.address, from_block(instanceOperator, set_gas_price))
            registry.register(s2b('RegistryController'), controller.address, from_block(instanceOperator, set_gas_price))

            registryAddress = proxy.address

        elif registryAddress is not None:
            registry = contract_from_address(gif.RegistryController, registryAddress)

            if instanceOperator is None:
                instanceOperatorServiceAddress = registry.getContract(s2b('InstanceOperatorService'))
                instanceOperatorService = contract_from_address(gif.InstanceOperatorService, instanceOperatorServiceAddress)
                
                instanceOperator = instanceOperatorService.owner()

        else:
            print('ERROR invalid arguments for GifRegistry: registryAddress and instanceOperator must not both be None')
            return

        self.gif = gif
        self.instanceOperator = instanceOperator
        self.registry = contract_from_address(interface.IRegistry, registryAddress)

        print('owner {}'.format(instanceOperator))
        print('registry.address {}'.format(self.registry.address))
        print('registry.getContract(\'InstanceOperatorService\') {}'.format(self.registry.getContract(s2b('InstanceOperatorService'))))

    def getOwner(self) -> Account:
        return self.instanceOperator

    def getRegistry(self) -> interface.IRegistry:
        return self.registry


class GifInstance(GifRegistry):

    gifi = get_package('gif-interface')

    def __init__(
        self, 
        instanceOperator:Account=None, 
        instanceWallet:Account=None, 
        registry_address:Account=None,
        test_deploy_abort:bool=False,
        set_gas_price=False,
        publish_source=False
    ):
        registryAddress = registry_address
        super().__init__(
            instanceOperator,
            registryAddress,
            set_gas_price,
            publish_source
        )
        
        if instanceOperator:
            self.deployWithRegistry(test_deploy_abort, set_gas_price, publish_source)

            if test_deploy_abort:
                print('registry={}'.format(self.getRegistry()))
            else:
                if instanceWallet and self.instanceService.getInstanceWallet() != instanceWallet:
                    self.instanceOperatorService.setInstanceWallet(
                        instanceWallet,
                        from_block(instanceOperator, set_gas_price))

        else:
            self.createFromRegistry()


    def createFromRegistry(self):
        gif = get_package('gif-contracts')
        gifi = get_package('gif-interface')

        registry = self.getRegistry()
        instanceOperator = self.getOwner()

        # minimal set of contracts
        self.instanceService = contract_from_address(
            gif.InstanceService,
            registry.getContract(s2b('InstanceService')))
        
        self.componentOwnerService = contract_from_address(
            gif.ComponentOwnerService,
            registry.getContract(s2b('ComponentOwnerService')))

        self.instanceOperatorService = contract_from_address(
            gif.InstanceOperatorService,
            registry.getContract(s2b('InstanceOperatorService')))
        
        # other contracts needed
        self.treasury = contract_from_address(
            gif.TreasuryModule,
            registry.getContract(s2b('Treasury')))


    def deployWithRegistry(
        self, 
        test_deploy_abort=False, 
        set_gas_price=False,
        publish_source=False
    ):
        gif = self.gif
        registry = self.getRegistry()
        instanceOperator = self.getOwner()

        self.bundleToken = deployGifToken("BundleToken", gif.BundleToken, registry, instanceOperator, set_gas_price, publish_source)
        self.riskpoolToken = deployGifToken("RiskpoolToken", gif.RiskpoolToken, registry, instanceOperator, set_gas_price, publish_source)

        # modules (need to be deployed first)
        # deploy order needs to respect module dependencies
        self.access = deployGifModuleV2("Access", gif.AccessController, registry, instanceOperator, gif, set_gas_price, publish_source)
        self.component = deployGifModuleV2("Component", gif.ComponentController, registry, instanceOperator, gif, set_gas_price, publish_source)

        if test_deploy_abort:
            return

        self.query = deployGifModuleV2("Query", gif.QueryModule, registry, instanceOperator, gif, set_gas_price, publish_source)
        self.license = deployGifModuleV2("License", gif.LicenseController, registry, instanceOperator, gif, set_gas_price, publish_source)
        self.policy = deployGifModuleV2("Policy", gif.PolicyController, registry, instanceOperator, gif, set_gas_price, publish_source)
        self.bundle = deployGifModuleV2("Bundle", gif.BundleController, registry, instanceOperator, gif, set_gas_price, publish_source)
        self.pool = deployGifModuleV2("Pool", gif.PoolController, registry, instanceOperator, gif, set_gas_price, publish_source)
        self.treasury = deployGifModuleV2("Treasury", gif.TreasuryModule, registry, instanceOperator, gif, set_gas_price, publish_source)

        # TODO these contracts do not work with proxy pattern
        self.policyFlow = deployGifService("PolicyDefaultFlow", gif.PolicyDefaultFlow, registry, instanceOperator, set_gas_price, publish_source)

        # services
        self.instanceService = deployGifModuleV2("InstanceService", gif.InstanceService, registry, instanceOperator, gif, set_gas_price, publish_source)
        self.componentOwnerService = deployGifModuleV2("ComponentOwnerService", gif.ComponentOwnerService, registry, instanceOperator, gif, set_gas_price, publish_source)
        self.oracleService = deployGifModuleV2("OracleService", gif.OracleService, registry, instanceOperator, gif, set_gas_price, publish_source)
        self.riskpoolService = deployGifModuleV2("RiskpoolService", gif.RiskpoolService, registry, instanceOperator, gif, set_gas_price, publish_source)

        # TODO these contracts do not work with proxy pattern
        self.productService = deployGifService("ProductService", gif.ProductService, registry, instanceOperator, set_gas_price, publish_source)

        # needs to be the last module to register as it will 
        # perform some post deploy wirings and changes the address 
        # of the instance operator service to its true address
        self.instanceOperatorService = deployGifModuleV2("InstanceOperatorService", gif.InstanceOperatorService, registry, instanceOperator, gif, set_gas_price, publish_source)

        # ensure that the instance has 32 contracts when freshly deployed
        assert 32 == registry.contracts()

    def getRegistry(self):
        return self.registry

    def getTreasury(self) -> gifi.interface.ITreasury:
        return self.treasury

    def getInstanceOperatorService(self) -> interface.IInstanceOperatorService:
        return self.instanceOperatorService

    def getInstanceService(self) -> interface.IInstanceService:
        return self.instanceService

    def getComponentOwnerService(self) -> interface.IComponentOwnerService:
        return self.componentOwnerService


def check_registry(registryAddress) -> bool:
    print('checking registry at {}'.format(registryAddress))

    gif = get_package('gif-contracts')
    registry = contract_from_address(gif.RegistryController, registryAddress)
    registry_is_ok = True

    contracts = []
    numContracts = registry.contracts()
    numContractsOk = 'OK ({})'.format(numContracts) if numContracts == 32 else 'ERROR (found: {}, expected: 32)'.format(numContracts)
    print('registry count {}'.format(numContractsOk))

    for i, name in enumerate(INSTANCE_CONTRACTS):
        nameB32 = s2b(name)
        address = registry.getContract(nameB32)
        if address != ZERO_ADDRESS:
            print("contract[{}] '{}' at {}".format(i, name, address))
        else:
            print("contract[{}] '{}' missing".format(i, name))
            registry_is_ok = False

    if registry_is_ok:
        print('registry check OK')
    else:
        print('registry check ERROR')

    return registry_is_ok


# gif token deployment
def deployGifToken(
    tokenName,
    tokenClass,
    registry,
    owner,
    set_gas_price=False,
    publish_source=False
):
    tokenNameB32 = s2b(tokenName)
    tokenAddress = registry.getContract(tokenNameB32)

    # check if contract already available via registry
    if tokenAddress != ZERO_ADDRESS:
        print('token {} already registered at {}'.format(tokenName, tokenAddress))
        return contract_from_address(tokenClass, tokenAddress)

    # deploy contract
    print('token {} deploy'.format(tokenName))
    # token = tokenClass.deploy(
    #     {'from': owner},
    #     publish_source=publish_source)
    token = deploy(
        tokenClass,
        owner,
        set_gas_price=set_gas_price,
        publish_source=publish_source)

    print('token {} register'.format(tokenName))
    registry.register(tokenNameB32, token.address, from_block(owner, set_gas_price))

    return token


# generic open zeppelin upgradable gif module deployment
def deployGifModuleV2(
    moduleName,
    controllerClass,
    registry, 
    owner,
    gif,
    set_gas_price=False,
    publish_source=False
):
    moduleNameB32 = s2b(moduleName)
    controllerName = '{}Controller'.format(moduleName)[:32]
    controllerNameB32 = s2b(controllerName)

    controllerAddress = registry.getContract(controllerNameB32)
    proxyAddress = registry.getContract(moduleNameB32)

    # check if controller contract already available via registry
    if controllerAddress != ZERO_ADDRESS:
        controller = contract_from_address(controllerClass, controllerAddress)
        print('module {} controller already registered at {}'.format(moduleName, controllerAddress))
    else:
        print('module {} deploy controller'.format(moduleName))
        controller = deploy(
            controllerClass,
            owner,
            set_gas_price=set_gas_price,
            publish_source=publish_source)

    # check if module contract already available via registry
    # check for != owner covers special case with instance operator
    if proxyAddress != ZERO_ADDRESS and proxyAddress != owner:
        print('module {} proxy already registered at {}'.format(moduleName, proxyAddress))
        proxy = contract_from_address(gif.CoreProxy, proxyAddress)
    else:
        encoded_initializer = encode_function_data(
            registry.address,
            initializer=controller.initialize)

        print('module {} deploy proxy'.format(moduleName))
        proxy = deploy_with_args(
            gif.CoreProxy,
            [controller.address, encoded_initializer],
            owner,
            set_gas_price=set_gas_price,
            publish_source=publish_source)

    if controllerAddress != ZERO_ADDRESS:
        print('module {} ({}) controller already registered'.format(moduleName, controllerNameB32))
    else:
        print('module {} ({}) register controller'.format(moduleName, controllerNameB32))
        registry.register(controllerNameB32, controller.address, from_block(owner, set_gas_price))

    if proxyAddress != ZERO_ADDRESS and proxyAddress != owner:
        print('module {} ({}) proxy already registered'.format(moduleName, moduleNameB32))
    else:
        print('module {} ({}) register proxy'.format(moduleName, moduleNameB32))
        registry.register(moduleNameB32, proxy.address, from_block(owner, set_gas_price))

        proxyAddress = proxy.address

    return contract_from_address(controllerClass, proxyAddress)


# generic upgradable gif service deployment
def deployGifService(
    name,
    serviceClass, 
    registry, 
    owner,
    set_gas_price=False,
    publish_source=False
):
    serviceNameB32 = s2b(name)
    serviceAddress = registry.getContract(serviceNameB32)

    # check if contract already available via registry
    if serviceAddress != ZERO_ADDRESS:
        print('service {} already registered at {}'.format(name, serviceAddress))
        return contract_from_address(serviceClass, serviceAddress)

    print('service {} deploy'.format(name))
    # service = serviceClass.deploy(
    #     registry.address, 
    #     {'from': owner},
    #     publish_source=publish_source)
    service = deploy_with_args(
        serviceClass,
        [registry.address],
        owner,
        set_gas_price=set_gas_price,
        publish_source=publish_source)

    print('service {} register'.format(name))
    registry.register(serviceNameB32, service.address, from_block(owner, set_gas_price))

    return service
