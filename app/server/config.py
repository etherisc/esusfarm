from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # fastapi settings
    APP_TITLE: str = "Etherisc API Server"
    APP_DEBUG: bool = False

    # model fields settings
    MODEL_ID_ATTRIBUTE: str = "id"
    MODEL_CSV_DELIMITER: str = ";"
    MODEL_CSV_PERSON_FIELDS: str = "id,locationId,firstName,lastName,gender,mobilePhone,externalId,walletIndex,wallet"
    MODEL_CSV_LOCATION_FIELDS: str = "id,country,region,province,department,village,latitude,longitude,openstreetmap,coordinatesLevel"
    MODEL_CSV_POLICY_FIELDS: str = "id,year,seasonStart,seasonEnd,indexType,locationNanoId,region,province,department,city,beneficiarySex,subscriptionDate,premium,sumInsured,triggerSevere,payoutSevere,triggerMedium,payoutMedium,triggerLow,payoutLow,indexReferenceValue,indexEndOfSeasonValue,indexRatio,payoutEstimated"
    MODEL_CSV_CLAIM_FIELDS: str = "id,onChainId,policyId,claimAmount,paidAmount,closedAt,createdAt,updatedAt"
    MODEL_CSV_PAYOUT_FIELDS: str = "id,onChainId,policyId,claimId,amount,paidAt,beneficiary,createdAt,updatedAt"
    MODEL_CSV_RISK_FIELDS: str = "id,isValid,configId,locationId,crop,createdAt,updatedAt"
    MODEL_CSV_CONFIG_FIELDS: str = "id,isValid,name,year,startOfSeason,endOfSeason,createdAt,updatedAt"

    # farmer wallet mnemonic (only via .env)
    FARMER_WALLET_MNEMONIC: str | None

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