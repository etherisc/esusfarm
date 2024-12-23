from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # fastapi settings
    APP_TITLE: str = "Etherisc API Server"
    APP_DEBUG: bool = False

    # list of valid crops
    VALID_CROPS: list = ["coffee", "maize"]

    # model fields settings
    MODEL_ID_ATTRIBUTE: str = "id"
    MODEL_CSV_DELIMITER: str = ";"
    MODEL_CSV_PERSON_FIELDS: str = "id,locationId,firstName,lastName,gender,mobilePhone,externalId,walletIndex,wallet"
    MODEL_CSV_LOCATION_FIELDS: str = "id,country,region,province,department,village,latitude,longitude,openstreetmap,coordinatesLevel"
    MODEL_CSV_POLICY_FIELDS: str = "id,personId,riskId,subscriptionDate,sumInsuredAmount,premiumAmount,nft,tx"
    MODEL_CSV_CLAIM_FIELDS: str = "id,onChainId,policyId,claimAmount,paidAmount,closedAt,createdAt,updatedAt"
    MODEL_CSV_PAYOUT_FIELDS: str = "id,onChainId,policyId,claimId,amount,paidAt,beneficiary,createdAt,updatedAt"
    MODEL_CSV_RISK_FIELDS: str = "id,isValid,configId,locationId,crop,createdAt,updatedAt"
    MODEL_CSV_CONFIG_FIELDS: str = "id,isValid,name,year,startOfSeason,endOfSeason,createdAt,updatedAt"

    # account mnemonics (only via .env)
    FARMER_WALLET_MNEMONIC: str | None
    OPERATOR_WALLET_MNEMONIC: str | None
    OPERATOR_ACCOUNT_INDEX: int = 0 # for local testing, for prod set value to 2

    # farmer minimum funding amount
    FARMER_FUNDING_AMOUNT: int = 100000001

    # smart contracs settings
    PRODUCT_CONTRACT_ADDRESS: str | None
    TOKEN_CONTRACT_ADDRESS: str | None

    # onchain latitude longitude decimals
    LOCATION_DECIMALS: int = 6

    # rpc node settings (default is local anvil node)
    RPC_NODE_URL: str | None = "http://127.0.0.1:8545"

    # mongodb settings
    MONGO_ID_ATTRIBUTE: str = "_id"
    MONGO_CREATE_COLLECTIONS: bool = True
    MONGO_DOCUMENTS_PER_PAGE: int = 5

    # loguru settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
        "<level>{level}</level> "
        "<cyan>{file}</cyan>:<cyan>{line}</cyan> <cyan>{function}</cyan> "
        "<level>{message}</level>"
    )
    LOG_COLORIZE: bool = True

    # uvicorn server settings
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    SERVER_RELOAD: bool = True

    model_config = SettingsConfigDict(
        env_file='app/.env', 
        env_file_encoding='utf-8',
        extra='ignore')

# Load settings
settings = Settings()