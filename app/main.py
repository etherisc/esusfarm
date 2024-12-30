from dotenv import load_dotenv
from uvicorn import run

from server.config import settings
from util.logging import get_logger

load_dotenv()

logger = get_logger()

def main() -> None:
    logger.info(f"start uvicorn '{settings.APP_TITLE}', host={settings.SERVER_HOST}, port={settings.SERVER_PORT}, reload={settings.SERVER_RELOAD}")

    run(
        "server.app:app", 
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.SERVER_RELOAD)

if __name__ == "__main__":
    main()
