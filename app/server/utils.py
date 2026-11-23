from fastapi import FastAPI
from fastapi.routing import APIRouter
from loguru import logger
from loguru._logger import Logger
from nanoid import generate

from server.config import Settings
from server.error import raise_with_log
from util.logging import get_logger

import os
import sys

NANO_ID_SIZE=12

logger = get_logger()

def create_app(settings: Settings) -> FastAPI:
    return FastAPI(
        title=settings.APP_TITLE,
        debug=settings.APP_DEBUG)


def include_router(app: FastAPI, router: APIRouter, message: str) -> None:
    logger.info(message)
    app.include_router(router)


def setup_logging(settings: Settings) -> Logger:
    logger.remove()
    logger.add(
        sys.stdout, 
        format=settings.LOG_FORMAT,
        level=settings.LOG_LEVEL, 
        colorize=settings.LOG_COLORIZE)

    return logger


def getenv_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, default)
    
    if isinstance(value, bool):
        return value
    
    return value.lower() in ["true", "1"]


def getenv_int(name: str, default: int = 0) -> int:
    value = os.getenv(name, default)
    
    if isinstance(value, int):
        return value
    
    return int(value)

