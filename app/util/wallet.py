from util.logging import get_logger

logger = get_logger()

def generate_wallet() -> str:
    wallet_address = "0x03507c8a16513F1615bD4a00BDD4570514a6ef21"
    logger.warning(f"wallet generation needs implementation")
    return wallet_address

def is_valid_wallet_address(wallet: str) -> bool:
    logger.warning(f"wallet address check needs implementation")
    return True