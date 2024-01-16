from loguru._logger import Logger
from loguru import logger
from server.config import settings

import sys

logger_setup_done = False

def get_logger() -> Logger:
    global logger_setup_done

    if logger_setup_done:
        return logger

    logger.remove()
    logger.add(
        sys.stdout, 
        format=settings.LOG_FORMAT,
        level=settings.LOG_LEVEL, 
        colorize=settings.LOG_COLORIZE)

    logger_setup_done = True

    return logger
