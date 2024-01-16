
# === env variables (.env file) ============================================= #

WEB3_INFURA_PROJECT_ID = 'WEB3_INFURA_PROJECT_ID'
POLYGONSCAN_TOKEN = 'POLYGONSCAN_TOKEN'
MORALIS_API_KEY = 'MORALIS_API_KEY'

# === GIF V2 platform ======================================================= #

# GIF release
GIF_RELEASE = '2.0.0'

# GIF modules
ACCESS_NAME = 'Access'
BUNDLE_NAME = 'Bundle'
COMPONENT_NAME = 'Component'

REGISTRY_CONTROLLER_NAME = 'RegistryController'
REGISTRY_NAME = 'Registry'

ACCESS_CONTROLLER_NAME = 'AccessController'
ACCESS_NAME = 'Access'

LICENSE_CONTROLLER_NAME = 'LicenseController'
LICENSE_NAME = 'License'

POLICY_CONTROLLER_NAME = 'PolicyController'
POLICY_NAME = 'Policy'

POLICY_DEFAULT_FLOW_NAME = 'PolicyDefaultFlow'
POOL_NAME = 'Pool'

QUERY_NAME = 'Query'

RISKPOOL_CONTROLLER_NAME = 'RiskpoolController'

PRODUCT_NAME = 'Product'
RISKPOOL_NAME = 'Riskpool'
TREASURY_NAME = 'Treasury'

# GIF services
COMPONENT_OWNER_SERVICE_NAME = 'ComponentOwnerService'
PRODUCT_SERVICE_NAME = 'ProductService'
RISKPOOL_SERVICE_NAME = 'RiskpoolService'
ORACLE_SERVICE_NAME = 'OracleService'
INSTANCE_OPERATOR_SERVICE_NAME = 'InstanceOperatorService'
INSTANCE_SERVICE_NAME = 'InstanceService'

# GIF States

# enum BundleState {Active, Locked, Closed, Burned}
BUNDLE_STATE = {
    0: "Active",
    1: "Locked",
    2: "Closed",
    3: "Burned",
}

# enum ApplicationState {Applied, Revoked, Underwritten, Declined}
APPLICATION_STATE = {
    0: "Applied",
    1: "Revoked",
    2: "Underwritten",
    3: "Declined",
}

# enum PolicyState {Active, Expired, Closed}
POLICY_STATE = {
    0: "Active",
    1: "Expired",
    2: "Closed",
}

# enum ComponentState {
#     Created,
#     Proposed,
#     Declined,
#     Active,
#     Paused,
#     Suspended,
#     Archived
# }
COMPONENT_STATE = {
    0: "Created",
    1: "Proposed",
    2: "Declined",
    3: "Active",
    4: "Paused",
    5: "Suspended",
    6: "Archived"
}

# === Stakeholder names ===================================================== #
REGISTRY_OWNER = 'registryOwner'
INSTANCE_OPERATOR = 'instanceOperator'
INSTANCE_WALLET = 'instanceWallet'
PRODUCT_OWNER = 'productOwner'
PRODUCT_WALLET = 'productWallet'
DISTRBUTION_OWNER = 'distributionOwner'
DISTRBUTION_WALLET = 'distributionWallet'
RISKPOOL_KEEPER = 'riskpoolKeeper'
RISKPOOL_WALLET = 'riskpoolWallet'
INVESTOR = 'investor'
CUSTOMER = 'customer'
OUTSIDER = 'outsider'

# === GIF testing =========================================================== #

# ZERO_ADDRESS = accounts.at('0x0000000000000000000000000000000000000000')
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'
COMPROMISED_ADDRESS = '0x0000000000000000000000000000000000000013'

# TEST account values
ACCOUNTS_MNEMONIC = 'candy maple cake sugar pudding cream honey rich smooth crumble sweet treat'
